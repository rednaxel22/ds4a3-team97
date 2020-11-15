import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
import folium  # needed for interactive map
from folium.plugins import HeatMap
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_table as dt
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme, Sign, Symbol, Group


from app import app


############################################
######         Naturela Data          ######
############################################
def db_connect():
    # Create the connection
    postgres_str = (
        'postgresql://natu_user:password*01@pg-database-1.cwzau02gc3hn.us-east-2.rds.amazonaws.com:5432/naturela_dev')
    cnx = create_engine(postgres_str)
    return(cnx)


cnx = db_connect()


def load_sales_info():
    sales = pd.read_sql_query('''
    Select 
        invoice_number, invoice_date, customer_id, contact_name,
            product_code, product_name, customer_name, quantity,
            sales_unit, sales_unit_price::decimal, kilos, price_bef_vat::decimal,
            price_per_kilo, salesperson_code, salesperson_name, city_code,
            cost, invoice_address, city_name, salesperson_id, client_name,
            type_id, type_person, type_client, nature_economy,
            aditional_condition, country, city, main_address,
            payment_terms, credit_state, email, contact_person, seller,
            verified, zone, id, description, code, presentation,
            product_line, concat(description, presentation) as product_description
        from public.sales_01 s inner join public.product p on s.product_code = p.code
        where invoice_date < '2020-09-01';
    ''', cnx)
    return(sales)


ventas = load_sales_info()
ventas['year'] = ventas['invoice_date'].dt.year
ventas['month'] = ventas['invoice_date'].dt.month
ventas['weekofyear'] = ventas['invoice_date'].dt.weekofyear

# print(ventas.columns)

# df_sales = pd.read_csv('ventas_clientes_2015_2020.csv')
# products = df_sales['pronom'].unique()
# customers = df_sales['Nombre Cliente (Factura)'].dropna().unique()
# channels = df_sales['Tipo de Cliente'].dropna().unique()
# sales_persons = df_sales['Vendedor'].dropna().unique()
# cities = df_sales['Ciudad'].dropna().unique()

############################################
# Datos de los filtros
############################################
products = ventas['product_description'].unique()
customers = ventas['customer_name'].dropna().unique()
channels = ventas['type_client'].dropna().unique()
sales_persons = ventas['salesperson_name'].dropna().unique()
cities = ventas['city_name'].dropna().unique()
product_line = ventas['product_line'].dropna().unique()

# print(ventas['price_bef_vat'].head())
############################################
# Map
############################################

def prepare_sales_data():
    # We get the unique sales
    ventas_unicas = ventas.drop_duplicates(subset=['invoice_number'])
    ventas_agg = ventas_unicas.groupby('city').agg({'invoice_number': 'count'})
    ventas_agg_top20 = ventas_agg.sort_values(
        by="invoice_number", ascending=False).head(20)
    ventas_agg_top20.reset_index(inplace=True)

    # Let's load the file that holds the city coordinates - downloaded from https://simplemaps.com
    world_coordinates = pd.read_csv('assets/worldcities.csv')
    # We filter the data set to get only the coordinates for colombia
    colombian_coordinates = world_coordinates[world_coordinates['country'] == "Colombia"].copy(
    )
    colombian_coordinates.reset_index(inplace=True)

    # Se normalizan los nombres de las ciudades
    colombian_coordinates['city_low'] = colombian_coordinates['city_ascii'].str.lower(
    )
    # Creamos diccionario para ciudades que no coinciden
    ciudades_dict = {
        "Bogotá": "bogota",
        "Medellín": "medellin",
        "Cali": "cali",
        "Villavicencio": "villavicencio",
        "Envigado": "envigado",
        "Rionegro": "rionegro",
        "Bucaramanga": "bucaramanga",
        "Pereira": "pereira",
        "Armenia": "armenia",
        "Barranquilla": "barranquilla",
        "Cartagena de Indias": "cartagena",
        "Ibagué": "ibague",
        "Sabaneta": "sabaneta",
        "Cumaral": "cumaral",
        "Manizales": "manizales",
        "Itagüí": "itagui",
        "Cúcuta": "cucuta",
        "Neiva": "neiva",
        "Cajicá": "cajica",
        "Tunja": "tunja",
        "San José del Guaviare": "san jose del guaviare",
        "Monteria": "monteria",
        "Quibdó": "quibdo",
    }
    ventas_agg_top20['city_low'] = ventas_agg_top20['city'].apply(
        lambda x: ciudades_dict[x])
    # Revisamos cuales ciudades no se encuentran en el listado de coordenadas para adicionarlas
    ventas_agg_top20[~ventas_agg_top20['city_low'].isin(
        colombian_coordinates['city_low'])]

    # Se fusionan los data frames en uno solo juntando por la columna 'city_low'
    cities_df = ventas_agg_top20.merge(
        colombian_coordinates, left_on='city_low', right_on='city_low', how='left')

    # Se adiciona la información de latitud y longitud para los municipios que no aparecen en la base
    ciudades_faltantes_dict = {
        "envigado": {"lat": "6.17591", "lng": "-75.59174"},
        "rionegro": {"lat": "6.15515", "lng": "-75.37371"},
        "sabaneta": {"lat": "6.15153", "lng": "-75.61657"},
        "cumaral": {"lat": "4.2708", "lng": "-73.48669"},
        "itagui": {"lat": "6.18461", "lng": "-75.59913"},
        "cajica": {"lat": "4.91857", "lng": "-74.02799"},
    }
    for ciudad in ciudades_faltantes_dict.keys():
        cities_df.loc[cities_df["city_low"] == ciudad,
                      "lat"] = ciudades_faltantes_dict[ciudad]["lat"]
        cities_df.loc[cities_df["city_low"] == ciudad,
                      "lng"] = ciudades_faltantes_dict[ciudad]["lng"]

    return(cities_df)


def insert_heatmap():
    cities_df = prepare_sales_data()
    max_amount = float(cities_df['invoice_number'].max())
    folium_map = folium.Map(location=[4.624335, -74.063644], zoom_start=6)
    hm_wide = HeatMap(list(zip(cities_df['lat'], cities_df['lng'], cities_df['invoice_number'])),
                      min_opacity=0.5,
                      # max_val=max_amount,
                      radius=15, blur=6,
                      max_zoom=15
                      )

    folium_map.add_child(hm_wide)
    folium_map.save('salesmap.html')


insert_heatmap()
###############################################
# Tablas de Ventas
###############################################


def get_top_three_sales(city=None, channel=None, salesperson=None, product=None, customer=None, product_line=None):
    ventas_filtered = ventas
    if city:
        ventas_filtered = ventas[(ventas['city_name'] == city)]    
    if channel:
        ventas_filtered = ventas[(ventas['type_client'] == channel)]
    if salesperson:
        ventas_filtered = ventas[(ventas['salesperson_name'] == salesperson)]
    if product:
        ventas_filtered = ventas_filtered[ventas_filtered['product_description'].isin(product)]
    if customer:
        ventas_filtered = ventas_filtered[ventas_filtered['customer_name'].isin(customer)]
    if product_line:
        ventas_filtered = ventas[(ventas['product_line'] == product_line)]
    ventas_agg = ventas_filtered.groupby(
        'product_description').agg({'invoice_number': 'count'})
    # ventas_agg = ventas[(ventas['city_name'] == city) & (ventas['type_client'] == channel) & (ventas['salesperson_name'] == salesperson)].groupby(
    #     'product_name').agg({'invoice_number': 'count'})
    ventas_agg_top3 = ventas_agg.sort_values(
        by="invoice_number", ascending=False).head(3)
    ventas_agg_top3.reset_index(inplace=True)
    ventas_agg_top3['invoice_number'].map('{:,.2f}'.format)
    return(ventas_agg_top3)


ventas_agg_top_prod = get_top_three_sales()


def get_top_three_sales_cop(city=None, channel=None, salesperson=None, product=None, customer=None, product_line=None):
    ventas_filtered = ventas
    if city:
        ventas_filtered = ventas[(ventas['city_name'] == city)]    
    if channel:
        ventas_filtered = ventas[(ventas['type_client'] == channel)]
    if salesperson:
        ventas_filtered = ventas[(ventas['salesperson_name'] == salesperson)]
    if product:
        ventas_filtered = ventas_filtered[ventas_filtered['product_description'].isin(product)]
    if customer:
        ventas_filtered = ventas_filtered[ventas_filtered['customer_name'].isin(customer)]
    if product_line:
        ventas_filtered = ventas[(ventas['product_line'] == product_line)]
    ventas_agg = ventas_filtered.groupby(
        'product_description').agg({'price_bef_vat': 'sum'})
    # ventas_agg = ventas[(ventas['city_name'] == city) & (ventas['type_client'] == channel) & (ventas['salesperson_name'] == salesperson)].groupby(
    #     'product_name').agg({'price_bef_vat': 'sum'})
    ventas_agg_top3 = ventas_agg.sort_values(
        by="price_bef_vat", ascending=False).head(3)
    ventas_agg_top3.reset_index(inplace=True)
    ventas_agg_top3['price_bef_vat'].map('${:,.2f}'.format)
    return(ventas_agg_top3)


ventas_agg_top_prod_cop = get_top_three_sales_cop()


###############################################
# Sales by Product Bar Chart
###############################################

def top_20_sales_products(city=None, channel=None, salesperson=None, product=None, customer=None, product_line=None):
    # ventas_agg = ventas.groupby('product_name').agg({'invoice_number': 'count'})
    # ventas_agg = ventas[ventas['product_name'].isin(products)].groupby('product_name').agg({'invoice_number': 'count'})
    ventas_filtered = ventas
    if city:
        ventas_filtered = ventas[(ventas['city_name'] == city)]    
    if channel:
        ventas_filtered = ventas[(ventas['type_client'] == channel)]
    if salesperson:
        ventas_filtered = ventas[(ventas['salesperson_name'] == salesperson)]
    if product:
        ventas_filtered = ventas_filtered[ventas_filtered['product_description'].isin(product)]
    if customer:
        ventas_filtered = ventas_filtered[ventas_filtered['customer_name'].isin(customer)]
    if product_line:
        ventas_filtered = ventas[(ventas['product_line'] == product_line)]
    ventas_agg = ventas_filtered.groupby('product_description').agg({'invoice_number': 'count'})
    ventas_agg_top20 = ventas_agg.sort_values(by="invoice_number", ascending=False).head(20)
    ventas_agg_top20.reset_index(inplace=True)
    return(ventas_agg_top20)

def sales_by_product_graph(city=None, channel=None, salesperson=None, product=None, customer=None, year=2019, product_line=None):
    ventas_agg_top20 = top_20_sales_products(city, channel, salesperson, product, customer)
    top_sale_products = ventas[ventas.product_description.isin(ventas_agg_top20['product_description'].head(3))].copy()
    # top_sale_products = top_sale_products[(top_sale_products['city_name'] == city) & (top_sale_products['type_client'] == channel) & (top_sale_products['salesperson_name'] == salesperson)]
    if city:
        top_sale_products = top_sale_products[(top_sale_products['city_name'] == city)]    
    if channel:
        top_sale_products = top_sale_products[(top_sale_products['type_client'] == channel)]
    if salesperson:
        top_sale_products = top_sale_products[(top_sale_products['salesperson_name'] == salesperson)]
    if product:
        top_sale_products = top_sale_products[top_sale_products['product_description'].isin(product)]
    if customer:
        top_sale_products = top_sale_products[top_sale_products['customer_name'].isin(customer)]
    if product_line:
        top_sale_products = top_sale_products[(top_sale_products['product_line'] == product_line)]
    top_sale_products['invoice_year'] = pd.DatetimeIndex(top_sale_products['invoice_date']).year
    top_sale_products['invoice_month'] = pd.DatetimeIndex(top_sale_products['invoice_date']).month
    top_sales_prod_agg = top_sale_products.groupby(['invoice_year', 'invoice_month', 'product_description']).agg({'invoice_number': 'count'})
    top_sales_prod_agg.reset_index(inplace=True)
    top_sales_year = top_sales_prod_agg[top_sales_prod_agg['invoice_year'] == year]
    return top_sales_year
    #fig = px.bar(top_sales_year, x='invoice_month', y='invoice_number', color='product_name', barmode='group')
    # return(fig)

###############################################
# Pie Chart Channels
###############################################
def sales_by_channel(city=None, channel=None, salesperson=None, product=None, customer=None, product_line=None):
    ventas_filtered = ventas
    if city:
        ventas_filtered = ventas[(ventas['city_name'] == city)]    
    if channel:
        ventas_filtered = ventas[(ventas['type_client'] == channel)]
    if salesperson:
        ventas_filtered = ventas[(ventas['salesperson_name'] == salesperson)]
    if product:
        ventas_filtered = ventas_filtered[ventas_filtered['product_description'].isin(product)]
    if customer:
        ventas_filtered = ventas_filtered[ventas_filtered['customer_name'].isin(customer)]
    if product_line:
        ventas_filtered = ventas[(ventas['product_line'] == product_line)]
    ventas_unicas = ventas_filtered.drop_duplicates(subset=['invoice_number'])
    df_ventas_canal_agg = ventas_unicas.groupby('type_client').agg({'invoice_number': 'count'})
    df_ventas_canal_agg.reset_index(inplace=True)
    df_ventas_canal_agg.sort_values(by="invoice_number", ascending=False)
    return df_ventas_canal_agg
    # fig = go.Figure(data=[go.Pie(labels=df_ventas_canal_agg['type_client'], values=df_ventas_canal_agg['invoice_number'], textinfo='label+value', hole=.5)])
    # return(fig)

###############################################
# Sales by onth of year
###############################################

def get_total_sales_by_year(city=None, channel=None, salesperson=None, product=None, customer=None, year=2019, product_line=None):
    ventas_filtered = ventas
    if city:
        ventas_filtered = ventas[(ventas['city_name'] == city)]    
    if channel:
        ventas_filtered = ventas[(ventas['type_client'] == channel)]
    if salesperson:
        ventas_filtered = ventas[(ventas['salesperson_name'] == salesperson)]
    if product:
        ventas_filtered = ventas_filtered[ventas_filtered['product_description'].isin(product)]
    if customer:
        ventas_filtered = ventas_filtered[ventas_filtered['customer_name'].isin(customer)]
    if product_line:
        ventas_filtered = ventas[(ventas['product_line'] == product_line)]
    total_sales_df = ventas_filtered
    total_sales_df['invoice_year'] = pd.DatetimeIndex(total_sales_df['invoice_date']).year
    total_sales_df['invoice_month'] = pd.DatetimeIndex(total_sales_df['invoice_date']).month
    sales_agg = total_sales_df.groupby(['invoice_year', 'invoice_month']).agg({'invoice_number':'count'})
    sales_agg.reset_index(inplace=True)
    year_sales = sales_agg[sales_agg['invoice_year'] == year]
    return(year_sales)


###############################################

# change to app.layout if running as single page app instead
layout = html.Div([
    # Header With Radio Buttons
    dbc.Row([
        dbc.Col(html.Div([
            html.H3(children='Naturela Sales Forecast', className="mb-2")
        ], className="p-3")),
        dbc.Col(html.Div()
            # dcc.RadioItems(
            #     id='xaxis-type',
            #     options=[{'label': i, 'value': i}
            #              for i in ['1M', '3M', '6M', '1Y']],
            #     value='Linear',
            #     labelStyle={'display': 'inline-block', 'padding-left': '20px'}
            #     )
                , className="mb-4 text-center"),
        dbc.Col(html.Div([html.H3(children='')],
                         className="p-3"), className="mb-2 text-right")
    ]),
    # First row of filters and graphs
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div([html.H5(children='Product')],
                                 className="p-3"), width=1),
                dbc.Col(
                    dcc.Dropdown(
                        id='product_dd',
                        options=[{'label': i, 'value': i} for i in products],
                        value=[' Docena Rosquillas Chia y linaza 75 gChia y linaza 75g docena',' Docena Rosquillas Chia y linaza 40 gChia y linaza 40g docena','Spiruté verde unidad 30 bolsitas x 1.5g',''],
                        multi=True,
                        placeholder="Select a product (If empty all products are selected)",
                        # style={'width': '50%'}
                    ),
                )
            ]),
            # html.Br(),
            dbc.Row([
                dbc.Col(
                    html.Div([html.H5(children='Customer')], className="p-3"), width=1),
                dbc.Col(
                    dcc.Dropdown(
                        id='customer_dd',
                        options=[{'label': i, 'value': i} for i in customers],
                        value='',
                        multi=True,
                        placeholder="Select a customer (If empty all customers are selected)",
                        # style={'width': '50%'}
                    ),
                )
            ]),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            # html.Br(),
            # dbc.Row([
            #     dbc.Col(html.Div([html.H5(children='Product')],
            #                      className="p-3"), width=4),
            #     dbc.Col(
            #         dcc.Dropdown(
            #             id='product_dd',
            #             options=[{'label': i, 'value': i} for i in products],
            #             value='PAN ARROZ ROSQUILLA CHIA LINAZA 75G *12',
            #             multi=True,
            #             # style={'width': '50%'}
            #         ),
            #     )
            # ]),
            # # html.Br(),
            # dbc.Row([
            #     dbc.Col(
            #         html.Div([html.H5(children='Customer')], className="p-3"), width=4),
            #     dbc.Col(
            #         dcc.Dropdown(
            #             id='customer_dd',
            #             options=[{'label': i, 'value': i} for i in customers],
            #             value='JUAN SEBASTIAN GIRALDO SEPULVEDA',
            #             multi=True,
            #             # style={'width': '50%'}
            #         ),
            #     )
            # ]),
            # html.Br(),
            dbc.Row([
                dbc.Col(html.Div([html.H5(children='Channel')],
                                 className="p-3"), width=4),
                dbc.Col(
                    dcc.Dropdown(
                        id='channel_dd',
                        options=[{'label': i, 'value': i} for i in channels],
                        value='',
                        # multi=True,
                        # style={'width': '50%'}
                    ),
                )
            ]),
            # html.Br(),
            dbc.Row([
                dbc.Col(
                    html.Div([html.H5(children='Sales Person')], className="p-3"), width=4),
                dbc.Col(
                    dcc.Dropdown(
                        id='sales_person_dd',
                        options=[{'label': i, 'value': i}
                                 for i in sales_persons],
                        value='',
                        # multi=True,
                        # style={'width': '50%'}
                    ),
                )
            ]),
            # html.Br(),
            dbc.Row([
                dbc.Col(html.Div([html.H5(children='City')],
                                 className="p-3"), width=4),
                dbc.Col(
                    dcc.Dropdown(
                        id='city_dd',
                        options=[{'label': i, 'value': i} for i in cities],
                        value='',
                        # multi=True,
                        # style={'width': '50%'}
                    ),
                ),
            ]),
            dbc.Row([
                dbc.Col(html.Div([html.H5(children='Product Line')],
                                 className="p-3"), width=4),
                dbc.Col(
                    dcc.Dropdown(
                        id='product_line_dd',
                        options=[{'label': i, 'value': i} for i in product_line],
                        value='',
                        # multi=True,
                        # style={'width': '50%'}
                    ),
                ),
            ]),
        ], width=3),
        dbc.Col(dcc.Graph(id='line-sales'), width=6),
        # dbc.Col(html.Div([html.H5(children='una tabla')], className="p-3"),width=2),
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div([html.H3(children='Top Products by Qty')],className="p"), className="mb-2 text-left"),
            ]),
            dbc.Row([
                dbc.Col(
                    dt.DataTable(id='datatable-top-products',
                            #  columns=[{"name": i, "id": i}
                            #           for i in ventas_agg_top_prod.columns],
                            columns = [{'id': 'product_description', 'name': 'Product Name'}, 
                                        {'id': 'invoice_number', 'name': 'Items Qty','type': 'numeric',
                                        'format': Format(
                                                            scheme=Scheme.fixed, 
                                                            precision=2,
                                                            group=Group.yes,
                                                            groups=3,
                                                            group_delimiter=',',
                                                            decimal_delimiter='.',
                                                            symbol=Symbol.no)}],
                            data=ventas_agg_top_prod.to_dict('records'),
                            ), width=3, style={'padding-right': '40px'}
                ),
            ]),
            dbc.Row([html.Br()]),
            dbc.Row([
                dbc.Col(html.Div([html.H3(children='Top Products by Price')],className="p"), className="mb-2 text-left"),
            ]),
            dbc.Row([
                dbc.Col(
                    dt.DataTable(id='datatable-top-products-cop',
                            #  columns=[{"name": i, "id": i}
                            #           for i in ventas_agg_top_prod_cop.columns],
                            columns = [{'id': 'product_description', 'name': 'Product Name'}, 
                                        {'id': 'price_bef_vat', 'name': 'Sales Amount','type': 'numeric','format': FormatTemplate.money(0)}],
                             data=ventas_agg_top_prod_cop.to_dict('records')), width=3, style={'padding-right': '40px'}
                ),
            ]),
        ], width=3),



    ]),
    # Maps, Products and Channel
    dbc.Row([
        # dbc.Col(dcc.Graph(id='pie_cases_or_deaths'), width=3),
        dbc.Col(html.Iframe(id='map', srcDoc=open('salesmap.html',
                                                  'r').read(), width='100%', height='100%'), width=3),
        dbc.Col(dbc.Row([html.Div([
            dcc.Slider(
                id='month-slider',
                # min=df['year'].min(),
                min=2015,
                max=ventas['year'].max(),
                value=ventas['year'].max(),
                marks={str(year): str(year) for year in [
                    '2015', '2016', '2017', '2018', '2019', '2020']},
                step=None
            ),
            dcc.Graph(id='product-detail-by-month'),
        ], style={'width': '100%'})]), width=6),
        dbc.Col(dcc.Graph(id='pie-channels'), width=3),
    ]),


    # Final

])


@app.callback(
    [Output('datatable-top-products', 'data'),
    Output('datatable-top-products-cop', 'data'),
    Output('product-detail-by-month', 'figure'),
    Output('pie-channels', 'figure'),
    Output('line-sales', 'figure'),],
    [Input('city_dd', "value"),
    Input('channel_dd', "value"),
    Input('sales_person_dd', "value"),
    Input('product_dd', "value"),
    Input('customer_dd', "value"),
    Input('month-slider', "value"),
    Input('product_line_dd', "value"),])
def update_table(city, channel, sales_person, product_value, customer, year, product_line):
    # Tables 
    ventas_agg_top_prod = get_top_three_sales(city, channel, sales_person, product_value, customer, product_line)
    ventas_agg_top_prod_cop = get_top_three_sales_cop(city, channel, sales_person, product_value, customer, product_line)
    table1 = ventas_agg_top_prod.to_dict('records')
    table2 = ventas_agg_top_prod_cop.to_dict('records')
    
    # Product Detail
    sales_by_product_data = sales_by_product_graph(city, channel, sales_person, product_value, customer, year, product_line)
    products_top = sales_by_product_data['product_description'].unique()
    fig1 = go.Figure()
    for product in products_top:
        products_top_filtered = sales_by_product_data[sales_by_product_data['product_description']==product]
        fig1.add_trace(go.Bar(x=products_top_filtered['invoice_month'], y=products_top_filtered['invoice_number'],
                                 name=product,))
    fig1.update_layout(yaxis_title='Number of Items',
                       paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       template = "seaborn",
                       margin=dict(t=30),
                       legend=dict(
                            x=0,
                            y=1.0,
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        title='Top 3 Products history (Filters apply)',)
    
    # Sales by Channel

    df_ventas_canal_agg = sales_by_channel(city, channel, sales_person, product_value, customer, product_line)

    fig2 = go.Figure(
            data=[go.Pie(labels=df_ventas_canal_agg['type_client'], 
            values=df_ventas_canal_agg['invoice_number'], 
            textinfo='label+value', hole=.5)])

    fig2.update_layout(title='Sales by Channel')

    # Sales by year
    sales_by_year = get_total_sales_by_year(city, channel, sales_person, product_value, customer, year, product_line)
    fig3 = go.Figure(data=[go.Scatter(x=sales_by_year['invoice_month'], y=sales_by_year['invoice_number'], line_shape='spline')])
    fig3.update_layout(title='Sales by month of year')

    return table1, table2, fig1, fig2, fig3


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
            product_line
        from public.sales_01 s inner join public.product p on s.product_code = p.code
        where invoice_date < "2020-09-01";
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

products = ventas['product_name'].unique()
customers = ventas['customer_name'].dropna().unique()
channels = ventas['type_client'].dropna().unique()
sales_persons = ventas['salesperson_name'].dropna().unique()
cities = ventas['city_name'].dropna().unique()

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


def get_top_three_sales(city):
    ventas_agg = ventas[ventas['city_name'] == city].groupby(
        'product_name').agg({'invoice_number': 'count'})
    ventas_agg_top3 = ventas_agg.sort_values(
        by="invoice_number", ascending=False).head(3)
    ventas_agg_top3.reset_index(inplace=True)
    return(ventas_agg_top3)


ventas_agg_top_prod = get_top_three_sales('MEDELLIN')


def get_top_three_sales_cop(city):
    ventas_agg = ventas[ventas['city_name'] == city].groupby(
        'product_name').agg({'price_bef_vat': 'sum'})
    ventas_agg_top3 = ventas_agg.sort_values(
        by="price_bef_vat", ascending=False).head(3)
    ventas_agg_top3.reset_index(inplace=True)
    return(ventas_agg_top3)


ventas_agg_top_prod_cop = get_top_three_sales_cop('MEDELLIN')


###############################################
# Sales by Product Bar Chart
###############################################

def top_20_sales_products(city):
    # ventas_agg = ventas.groupby('product_name').agg({'invoice_number': 'count'})
    # ventas_agg = ventas[ventas['product_name'].isin(products)].groupby('product_name').agg({'invoice_number': 'count'})
    ventas_agg = ventas[ventas['city_name']==city].groupby('product_name').agg({'invoice_number': 'count'})
    ventas_agg_top20 = ventas_agg.sort_values(by="invoice_number", ascending=False).head(20)
    ventas_agg_top20.reset_index(inplace=True)
    return(ventas_agg_top20)

def sales_by_product_graph(city):
    ventas_agg_top20 = top_20_sales_products(city)
    top_sale_products = ventas[ventas.product_name.isin(ventas_agg_top20['product_name'].head(3))].copy()
    top_sale_products = top_sale_products[top_sale_products['city_name']==city]
    top_sale_products['invoice_year'] = pd.DatetimeIndex(top_sale_products['invoice_date']).year
    top_sale_products['invoice_month'] = pd.DatetimeIndex(top_sale_products['invoice_date']).month
    top_sales_prod_agg = top_sale_products.groupby(['invoice_year', 'invoice_month', 'product_name']).agg({'invoice_number': 'count'})
    top_sales_prod_agg.reset_index(inplace=True)
    top_sales_year = top_sales_prod_agg[top_sales_prod_agg['invoice_year'] == 2019]
    return top_sales_year
    #fig = px.bar(top_sales_year, x='invoice_month', y='invoice_number', color='product_name', barmode='group')
    # return(fig)

###############################################


###############################################

# change to app.layout if running as single page app instead
layout = html.Div([
    # Header With Radio Buttons
    dbc.Row([
        dbc.Col(html.Div([
            html.H3(children='Naturela Sales Forecast', className="mb-2")
        ], className="p-3")),
        dbc.Col(dcc.RadioItems(
                id='xaxis-type',
                options=[{'label': i, 'value': i}
                         for i in ['1M', '3M', '6M', '1Y']],
                value='Linear',
                labelStyle={'display': 'inline-block', 'padding-left': '20px'}
                ), className="mb-4 text-center"),
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
                        value=['PAN ARROZ ROSQUILLA CHIA LINAZA 75G *12','TÉ VERDE SPIRULINA SPIRUTÉ 30 BOLS *45G','PAN ARROZ ROSQUILLA CHIA LINAZA 40G  *12',''],
                        multi=True,
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
                        value='JUAN SEBASTIAN GIRALDO SEPULVEDA',
                        multi=True,
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
                        value='Minorista',
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
                        value='NATURELA',
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
                        value='MEDELLIN',
                        # multi=True,
                        # style={'width': '50%'}
                    ),
                ),
            ]),
        ], width=3),
        dbc.Col(dcc.Graph(id='line_cases_or_deaths'), width=6),
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
                            columns = [{'id': 'product_name', 'name': 'Product Name'}, {'id': 'invoice_number', 'name': 'Items Qty'}],
                             data=ventas_agg_top_prod.to_dict('records')), width=3, style={'padding-right': '40px'}
                ),
            ]),
            dbc.Row([
                dbc.Col(html.Div([html.H3(children='Top Products by Price')],className="p"), className="mb-2 text-left"),
            ]),
            dbc.Row([
                dbc.Col(
                    dt.DataTable(id='datatable-top-products-cop',
                            #  columns=[{"name": i, "id": i}
                            #           for i in ventas_agg_top_prod_cop.columns],
                            columns = [{'id': 'product_name', 'name': 'Product Name'}, {'id': 'price_bef_vat', 'name': 'Sales Amount'}],
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
                value=ventas['year'].min(),
                marks={str(year): str(year) for year in [
                    '2015', '2016', '2017', '2018', '2019', '2020']},
                step=None
            ),
            dcc.Graph(id='product-detail-by-month'),
        ], style={'width': '100%'})]), width=6),
        dbc.Col(dcc.Graph(id='pie_cases_or_deaths'), width=3),
    ]),


    # Final

])


@app.callback(
    [Output('datatable-top-products', 'data'),
    Output('datatable-top-products-cop', 'data'),
    Output('product-detail-by-month', 'figure'),],
    [Input('city_dd', "value")])
def update_table(city):
    # Tables 
    ventas_agg_top_prod = get_top_three_sales(city)
    ventas_agg_top_prod_cop = get_top_three_sales_cop(city)
    table1 = ventas_agg_top_prod.to_dict('records')
    table2 = ventas_agg_top_prod_cop.to_dict('records')
    
    # Product Detail
    sales_by_product_data = sales_by_product_graph(city)
    products_top = sales_by_product_data['product_name'].unique()
    fig1 = go.Figure()
    for product in products_top:
        products_top_filtered = sales_by_product_data[sales_by_product_data['product_name']==product]
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
    

    return table1, table2, fig1


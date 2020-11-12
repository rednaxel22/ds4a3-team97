import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import plotly.express      as px
import plotly.graph_objs as go
import folium #needed for interactive map
from folium.plugins import HeatMap
import psycopg2
import sqlalchemy
from sqlalchemy import create_engine

def db_connect():
    # Create the connection
    postgres_str = ('postgresql://natu_user:password*01@pg-database-1.cwzau02gc3hn.us-east-2.rds.amazonaws.com:5432/naturela_dev')
    cnx = create_engine(postgres_str)
    return(cnx)

cnx = db_connect()

def load_sales_info():
    sales = pd.read_sql_query('''Select * from public.sales_01   ''', cnx)
    return(sales)

ventas = load_sales_info()

def prepare_sales_data():
    # We get the unique sales
    ventas_unicas = ventas.drop_duplicates(subset=['invoice_number'])
    ventas_agg = ventas_unicas.groupby('city').agg({'invoice_number': 'count'})
    ventas_agg_top20 = ventas_agg.sort_values(by="invoice_number", ascending=False).head(20)
    ventas_agg_top20.reset_index(inplace=True)


    # Let's load the file that holds the city coordinates - downloaded from https://simplemaps.com
    world_coordinates = pd.read_csv('data/worldcities.csv')
    # We filter the data set to get only the coordinates for colombia
    colombian_coordinates = world_coordinates[world_coordinates['country'] == "Colombia"].copy()
    colombian_coordinates.reset_index(inplace=True)

    ## Se normalizan los nombres de las ciudades
    colombian_coordinates['city_low'] = colombian_coordinates['city_ascii'].str.lower()
    # Creamos diccionario para ciudades que no coinciden
    ciudades_dict = {
        "Bogotá":"bogota",
        "Medellín":"medellin",
        "Cali":"cali",
        "Villavicencio":"villavicencio",
        "Envigado":"envigado",
        "Rionegro":"rionegro",
        "Bucaramanga":"bucaramanga",
        "Pereira":"pereira",
        "Armenia":"armenia",
        "Barranquilla":"barranquilla",
        "Cartagena de Indias":"cartagena",
        "Ibagué":"ibague",
        "Sabaneta":"sabaneta",
        "Cumaral":"cumaral",
        "Manizales":"manizales",
        "Itagüí":"itagui",
        "Cúcuta":"cucuta",
        "Neiva":"neiva",
        "Cajicá":"cajica",
        "Tunja":"tunja",
        "San José del Guaviare":"san jose del guaviare",
        "Monteria":"monteria",
        "Quibdó":"quibdo",
    }
    ventas_agg_top20['city_low'] = ventas_agg_top20['city'].apply(lambda x: ciudades_dict[x])
    # Revisamos cuales ciudades no se encuentran en el listado de coordenadas para adicionarlas
    ventas_agg_top20[~ventas_agg_top20['city_low'].isin(colombian_coordinates['city_low'])]

    # Se fusionan los data frames en uno solo juntando por la columna 'city_low'
    cities_df = ventas_agg_top20.merge(colombian_coordinates, left_on='city_low', right_on='city_low', how='left')

    # Se adiciona la información de latitud y longitud para los municipios que no aparecen en la base
    ciudades_faltantes_dict = {
        "envigado":{"lat":"6.17591", "lng":"-75.59174"},
        "rionegro":{"lat":"6.15515", "lng":"-75.37371"},
        "sabaneta":{"lat":"6.15153", "lng":"-75.61657"},
        "cumaral":{"lat":"4.2708", "lng":"-73.48669"},
        "itagui":{"lat":"6.18461", "lng":"-75.59913"},
        "cajica":{"lat":"4.91857", "lng":"-74.02799"},
    }
    for ciudad in ciudades_faltantes_dict.keys():
        cities_df.loc[cities_df["city_low"] == ciudad,"lat"] = ciudades_faltantes_dict[ciudad]["lat"]
        cities_df.loc[cities_df["city_low"] == ciudad,"lng"] = ciudades_faltantes_dict[ciudad]["lng"]
    
    return(cities_df)

def insert_heatmap():
    cities_df = prepare_sales_data()
    max_amount = float(cities_df['invoice_number'].max())
    folium_map = folium.Map(location=[4.624335,-74.063644], zoom_start=6)
    hm_wide = HeatMap(list(zip(cities_df['lat'], cities_df['lng'], cities_df['invoice_number'])),
                      min_opacity=0.5,
                      #max_val=max_amount,
                      radius=15, blur=6, 
                      max_zoom=15
                     )

    folium_map.add_child(hm_wide)
    folium_map.save('salesmap.html')

def sales_by_channel():
    ventas_unicas = ventas.drop_duplicates(subset=['invoice_number'])
    df_ventas_canal_agg = ventas_unicas.groupby('type_client').agg({'invoice_number': 'count'})
    df_ventas_canal_agg.reset_index(inplace=True)
    df_ventas_canal_agg.sort_values(by="invoice_number", ascending=False)
    fig = go.Figure(data=[go.Pie(labels=df_ventas_canal_agg['type_client'], values=df_ventas_canal_agg['invoice_number'], textinfo='label+value', hole=.5)])
    return(fig)

def sales_by_channel_graph():
    dff = sales_by_channel()
    piechart = px.pie(
        data_frame = dff,
        hole=.3,
    )
    return(piechart)

def get_top_three_sales():
    ventas_agg = ventas.groupby('product_name').agg({'invoice_number': 'count'})
    ventas_agg_top3 = ventas_agg.sort_values(by="invoice_number", ascending=False).head(3)
    ventas_agg_top3.reset_index(inplace=True)
    return(ventas_agg_top3)

def top_three_qty_table():
    top_three_sales = get_top_three_sales()
    # Rename the columns
    top_three_sales.rename(columns={'product_name':'Product', 'invoice_number':'Sales'}, inplace=True)
    table = html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in top_three_sales.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(top_three_sales.iloc[i][col]) for col in top_three_sales.columns
            ]) for i in range(min(len(top_three_sales), 10))
        ])
    ])
    return(table)

def top_20_sales_products():
    ventas_agg = ventas.groupby('product_name').agg({'invoice_number': 'count'})
    ventas_agg_top20 = ventas_agg.sort_values(by="invoice_number", ascending=False).head(20)
    ventas_agg_top20.reset_index(inplace=True)
    return(ventas_agg_top20)

def sales_by_product_graph():
    ventas_agg_top20 = top_20_sales_products()
    top_sale_products = ventas[ventas.product_name.isin(ventas_agg_top20['product_name'].head(3))].copy()
    top_sale_products['invoice_year'] = pd.DatetimeIndex(top_sale_products['invoice_date']).year
    top_sale_products['invoice_month'] = pd.DatetimeIndex(top_sale_products['invoice_date']).month
    top_sales_prod_agg = top_sale_products.groupby(['invoice_year', 'invoice_month', 'product_name']).agg({'invoice_number': 'count'})
    top_sales_prod_agg.reset_index(inplace=True)
    top_sales_year = top_sales_prod_agg[top_sales_prod_agg['invoice_year'] == 2019]
    fig = px.bar(top_sales_year, x='invoice_month', y='invoice_number', color='product_name', barmode='group')
    return(fig)

# Frontend application development
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
insert_heatmap()
# Application initialization
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Naturela Dashboard'
# Application Layout
app.layout = html.Div([
    html.Div([
        html.H1(["Sales HeatMap by City"],
            style={'textAlign': "center", "padding-bottom": "30"}
        )
    ]),
    html.Iframe(id='map', srcDoc = open('salesmap.html', 'r').read(), width='100%', height='580'),
    html.Div([
        html.H1(["Sales by Channel"],
            style={'textAlign': "center", "padding-bottom": "30"}
        )
    ]),
    dcc.Graph(
        id='sales_channels_pie',
        figure=sales_by_channel()
    ),
    html.Div([
        html.H1(["Top 3 products by number of sales"],
            style={'textAlign': "center", "padding-bottom": "30"}
        )
    ]),
    top_three_qty_table(),
    dcc.Graph(
        id='top_sales_products',
        figure=sales_by_product_graph()
    )
], className="container")

#@app.callback(
#    Output(component_id='sales_channels_pie', component_property='figure'),
#    [Input(component_id='sales_channels_pie', component_property='figure')]
#)

#def update_graph():
#    dff = sales_by_channel()
#    piechart = px.pie(
#        data_frame = dff,
#        hole=.3,
#    )
#    return(piechart)

if __name__ == '__main__':
    app.run_server(debug=True)
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
from fbprophet import Prophet
from fbprophet.plot import plot_plotly

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
products = ventas['product_name'].unique()
customers = ventas['customer_name'].dropna().unique()
channels = ventas['type_client'].dropna().unique()
sales_persons = ventas['salesperson_name'].dropna().unique()
cities = ventas['city_name'].dropna().unique()
product_line = ventas['product_line'].dropna().unique()


###############################################
# Prophet
###############################################

## Se encarga de adecuar el DataFrame para los modelos de prophet
def prophet_sales_data():
    ventas_prophet = ventas.copy()
    ventas_prophet['month'] = ventas_prophet['invoice_date'].dt.to_period('M')
    ventas_prophet = ventas_prophet.sort_values(['month'], ascending=True)
    ventas_prophet["year"] = ventas_prophet["invoice_date"].dt.year
    ventas_prophet = ventas_prophet[ventas_prophet["year"].isin([2017,2018,2019,2020])]
    return(ventas_prophet)

## Modelo prophet para ciudad
def prophet_city_model(city='MEDELLIN'):
    ventas_prophet = prophet_sales_data()
    #prophet_df = ventas_prophet[ventas_prophet["city_name"]=='MEDELLIN']
    prophet_df = ventas_prophet[ventas_prophet["city_name"]==city]
    prophet_df = prophet_df.groupby(prophet_df["month"])["quantity"].sum()
    prophet_df = pd.DataFrame(prophet_df)
    prophet_df['ds']= prophet_df.index.to_timestamp()
    prophet_df['y'] = prophet_df["quantity"]
    prophet_df = prophet_df.drop(["quantity"], axis=1)

    prophetmodel = Prophet()
    prophetmodel.fit(prophet_df)
    forecast_times = prophetmodel.make_future_dataframe(periods=12,freq='M')
    forecast = prophetmodel.predict(forecast_times)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    prophet_figure = plot_plotly(prophetmodel, forecast,uncertainty=True, xlabel="month",ylabel=" City Sales (units)")
    return(prophet_figure)

## Modelo prophet para los canales
def prophet_channel_model(channel='On line'):
    ventas_prophet = prophet_sales_data()
    #prophet_df = ventas_prophet[ventas_prophet["type_client"]=='On line']
    prophet_df = ventas_prophet[ventas_prophet["type_client"]==channel]
    prophet_df = prophet_df.groupby(prophet_df["month"])["type_client"].value_counts()
    prophet_df = pd.DataFrame(prophet_df)
    prophet_df["ds"] = [prophet_df.index[i][0].to_timestamp() for i in range(len(prophet_df))]
    prophet_df["y"] = prophet_df["type_client"]
    prophet_df =  prophet_df.drop(["type_client"], axis=1)

    prophetmodel = Prophet()
    prophetmodel.fit(prophet_df)
    forecast_times = prophetmodel.make_future_dataframe(periods=12,freq='M')
    forecast = prophetmodel.predict(forecast_times)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    prophet_figure = plot_plotly(prophetmodel, forecast,uncertainty=True, xlabel="month",ylabel=" Online Sales (sales quantity)")
    return(prophet_figure)

## Modelo prophet para las categorías
def prophet_category_model(product_line='Solids'):
    ventas_prophet = prophet_sales_data()
    #prophet_df = ventas_prophet[ventas_prophet["product_line"]=='Solids']
    prophet_df = ventas_prophet[ventas_prophet["product_line"]==product_line]
    prophet_df = prophet_df.groupby(prophet_df["month"])["product_line"].value_counts()
    prophet_df = pd.DataFrame(prophet_df)
    prophet_df["ds"] = [prophet_df.index[i][0].to_timestamp() for i in range(len(prophet_df))]
    prophet_df["y"] = prophet_df["product_line"]
    prophet_df =  prophet_df.drop(["product_line"], axis=1)

    prophetmodel = Prophet()
    prophetmodel.fit(prophet_df)
    forecast_times = prophetmodel.make_future_dataframe(periods=12,freq='M')
    forecast = prophetmodel.predict(forecast_times)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    prophet_figure = plot_plotly(prophetmodel, forecast,uncertainty=True, xlabel="month",ylabel=" Solids (sales quantity)")
    return(prophet_figure)

###############################################


###############################################

# change to app.layout if running as single page app instead
layout = html.Div([
    # Header With Radio Buttons
    dbc.Row([
        dbc.Col(html.Div([
            html.H3(children='Naturela Sales Forecast', className="mb-2")
        ], className="p-3")),
        dbc.Col(html.Div()
                , className="mb-4 text-center"),
        dbc.Col(html.Div([html.H3(children='')],
                         className="p-3"), className="mb-2 text-right")
    ]),
    # First row of filters and graphs
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Time Series by City')], className="p-3")])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='cities_dd',
                        options=[{'label': i, 'value': i} for i in cities],
                        value='MEDELLIN',
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Un texto de descripción de la serie de tiempo')], className="p-3")])
            ])
        ],width=4),
        dbc.Col([
            dcc.Graph(id='time-city')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Time Series by Channel')], className="p-3")])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='channel_dd',
                        options=[{'label': i, 'value': i} for i in channels],
                        value='On line',
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Un texto de descripción de la serie de tiempo')], className="p-3")])
            ])
        ],width=4),
        dbc.Col([
            dcc.Graph(id='time-channel')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Time Series by Product Line')], className="p-3")])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='product_line_dd',
                        options=[{'label': i, 'value': i} for i in product_line],
                        value='Solids',
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Un texto de descripción de la serie de tiempo')], className="p-3")])
            ])
        ],width=4),
        dbc.Col([
            dcc.Graph(id='time-product-line')
        ], width=8)
    ]),

    # Final

])


@app.callback(
    [Output('time-city', 'figure'),
    Output('time-channel', 'figure'),
    Output('time-product-line', 'figure'),],
    [Input('cities_dd', "value"),
    Input('channel_dd', "value"),
    Input('product_line_dd', "value"),])
def update_table(cities_dd, channel_dd, product_line_dd):
    #city='MEDELLIN'
    #channel='On line'
    #product_line = 'Solids'
    fig1 = prophet_city_model(cities_dd)
    fig2 = prophet_channel_model(channel_dd)
    fig3 = prophet_category_model(product_line_dd)
    return fig1, fig2, fig3


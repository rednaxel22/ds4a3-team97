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


def load_nn_city_info():
    nerualnet = pd.read_sql_query('''
    SELECT * FROM public.neural_city
    ''', cnx)
    return(nerualnet)

def load_nn_chan_info():
    nerualnet = pd.read_sql_query('''
    SELECT * FROM public.neural_channel
    ''', cnx)
    return(nerualnet)

def load_nn_cate_info():
    nerualnet = pd.read_sql_query('''
    SELECT * FROM public.neural_category
    ''', cnx)
    return(nerualnet)


neuralnet_city = load_nn_city_info()
neuralnet_chan = load_nn_chan_info()
neuralnet_cate = load_nn_cate_info()


############################################
# Datos de los filtros
############################################
cities = neuralnet_city['city'].unique()
channels = neuralnet_chan['channel'].unique()
product_line = neuralnet_cate['product_line'].unique()


###############################################
# Prediction model
###############################################
def neuralnet_city_model(city='MEDELLIN'):
    # Filter neural city network by city
    neuralnet_city_model = neuralnet_city[neuralnet_city['city'] == city].copy()
    # Get real data and prediction data from data frame
    neuralnet_city_real = neuralnet_city_model[neuralnet_city_model['date_real'] != 'NaT'][['date_real', 'q_real']]
    neuralnet_city_pred = neuralnet_city_model[neuralnet_city_model['date_predict'] != 'NaT'][['date_predict', 'q_predict']]
    # Set date as index to plot
    neuralnet_city_real.set_index('date_real', inplace=True)
    neuralnet_city_pred.set_index('date_predict', inplace=True)
    # Set figure data for plotting
    city_prediction_figure = go.Figure()
    # Add real sales scatterline
    city_prediction_figure.add_trace(go.Scatter(
        x = neuralnet_city_real.index,
        y = neuralnet_city_real['q_real'],
        hovertext = neuralnet_city_real['q_real'],
        name = 'Real',
        line_shape='spline'
    ))

    # Add prediction scatterline 
    city_prediction_figure.add_trace(go.Scatter(
        x = neuralnet_city_pred.index,
        y = neuralnet_city_pred['q_predict'],
        hovertext = neuralnet_city_pred['q_predict'],
        name = 'Prediction',
        line_shape='spline'
    ))
    # We update layout
    city_prediction_figure.update_layout(
        title = 'Sales predictions for city',
        xaxis_title = 'Date',
        yaxis_title = 'City sales (units)'
    )
    # Set rangeslider - Optional
    city_prediction_figure.update_xaxes(rangeslider_visible=True)

    return(city_prediction_figure)

def neuralnet_channel_model(channel='On line'):
    # Filter neural city network by city
    neuralnet_channel_model = neuralnet_chan[neuralnet_chan['channel'] == channel].copy()
    # Get real data and prediction data from data frame
    neuralnet_channel_real = neuralnet_channel_model[neuralnet_channel_model['date_real'] != 'NaT'][['date_real', 'q_real']]
    neuralnet_channel_pred = neuralnet_channel_model[neuralnet_channel_model['date_predict'] != 'NaT'][['date_predict', 'q_predict']]
    # Set date as index to plot
    neuralnet_channel_real.set_index('date_real', inplace=True)
    neuralnet_channel_pred.set_index('date_predict', inplace=True)
    # Set figure data for plotting
    channel_prediction_figure = go.Figure()
    # Add real sales scatterline
    channel_prediction_figure.add_trace(go.Scatter(
        x = neuralnet_channel_real.index,
        y = neuralnet_channel_real['q_real'],
        hovertext = neuralnet_channel_real['q_real'],
        name = 'Real',
        line_shape='spline'
    ))

    # Add prediction scatterline 
    channel_prediction_figure.add_trace(go.Scatter(
        x = neuralnet_channel_pred.index,
        y = neuralnet_channel_pred['q_predict'],
        hovertext = neuralnet_channel_pred['q_predict'],
        name = 'Prediction',
        line_shape='spline'
    ))
    # We update layout
    channel_prediction_figure.update_layout(
        title = 'Sales predictions for channel',
        xaxis_title = 'Date',
        yaxis_title = 'Channel sales (units)'
    )
    # Set rangeslider - Optional
    channel_prediction_figure.update_xaxes(rangeslider_visible=True)

    return(channel_prediction_figure)

def neuralnet_product_line_model(product_line='Solids'):
    # Filter neural city network by city
    neuralnet_product_line_model = neuralnet_cate[neuralnet_cate['product_line'] == product_line].copy()
    # Get real data and prediction data from data frame
    neuralnet_product_line_real = neuralnet_product_line_model[neuralnet_product_line_model['date_real'] != 'NaT'][['date_real', 'q_real']]
    neuralnet_product_line_pred = neuralnet_product_line_model[neuralnet_product_line_model['date_predict'] != 'NaT'][['date_predict', 'q_predict']]
    # Set date as index to plot
    neuralnet_product_line_real.set_index('date_real', inplace=True)
    neuralnet_product_line_pred.set_index('date_predict', inplace=True)
    # Set figure data for plotting
    product_line_prediction_figure = go.Figure()
    # Add real sales scatterline
    product_line_prediction_figure.add_trace(go.Scatter(
        x = neuralnet_product_line_real.index,
        y = neuralnet_product_line_real['q_real'],
        hovertext = neuralnet_product_line_real['q_real'],
        name = 'Real',
        line_shape='spline'
    ))

    # Add prediction scatterline 
    product_line_prediction_figure.add_trace(go.Scatter(
        x = neuralnet_product_line_pred.index,
        y = neuralnet_product_line_pred['q_predict'],
        hovertext = neuralnet_product_line_pred['q_predict'],
        name = 'Prediction',
        line_shape='spline'
    ))
    # We update layout
    product_line_prediction_figure.update_layout(
        title = 'Sales predictions for product line',
        xaxis_title = 'Date',
        yaxis_title = 'Product line sales (units)'
    )
    # Set rangeslider - Optional
    product_line_prediction_figure.update_xaxes(rangeslider_visible=True)

    return(product_line_prediction_figure)

###############################################

# change to app.layout if running as single page app instead
layout = html.Div([
    # Header With Radio Buttons
    dbc.Row([
        dbc.Col(html.Div([
            html.H3(children='Naturela Sales Predictions', className="mb-2")
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
                dbc.Col([html.Div([html.H5(children='Predictions by City')], className="p-3")])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='cities_nn_dd',
                        options=[{'label': i, 'value': i} for i in cities],
                        value='MEDELLIN',
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='This is the result of a Prediction Model using neural networks. Each dashboard update executes the model to ' +
                    'predict new values to one year in the future. This model is done using City as the main dimension.')], className="p-3")])
            ])
        ],width=4),
        dbc.Col([
            dcc.Graph(id='time-nn-city')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Predictions by Channel')], className="p-3")])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='channel_nn_dd',
                        options=[{'label': i, 'value': i} for i in channels],
                        value='On line',
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='This is the result of a Prediction Model using neural networks. Each dashboard update executes the model to ' +
                    'predict new values to one year in the future. This model is done using Distribution Channel as the main dimension.')], className="p-3")])
            ])
        ],width=4),
        dbc.Col([
            dcc.Graph(id='time-nn-channel')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='Predictions by Product Line')], className="p-3")])
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='product_line_nn_dd',
                        options=[{'label': i, 'value': i} for i in product_line],
                        value='Solids',
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([html.Div([html.H5(children='This is the result of a Prediction Model using neural networks. Each dashboard update executes the model to ' +
                    'predict new values to one year in the future. This model is done using Product Line as the main dimension.')], className="p-3")])
            ])
        ],width=4),
        dbc.Col([
            dcc.Graph(id='time-nn-product-line')
        ], width=8)
    ]),

    # Final

])

@app.callback(
    Output('time-nn-city', 'figure'),
    Input('cities_nn_dd', 'value')
)
def update_city_prediction_graph(cities_nn_dd):
    city_prediction_model_figure = neuralnet_city_model(cities_nn_dd)
    return city_prediction_model_figure

@app.callback(
    Output('time-nn-channel', 'figure'),
    Input('channel_nn_dd', 'value')
)
def update_chan_prediction_graph(channel_nn_dd):
    chan_prediction_model_figure = neuralnet_channel_model(channel_nn_dd)
    return chan_prediction_model_figure

@app.callback(
    Output('time-nn-product-line', 'figure'),
    Input('product_line_nn_dd', 'value')
)
def update_prol_prediction_graph(product_line_nn_dd):
    prol_prediction_model_figure = neuralnet_product_line_model(product_line_nn_dd)
    return prol_prediction_model_figure


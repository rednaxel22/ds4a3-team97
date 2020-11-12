import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_table as dt
from sqlalchemy import create_engine
import pandas as pd

# df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')
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
cities = ventas['city_name'].dropna().unique()


# ventas_agg = ventas.groupby('product_name').agg({'invoice_number': 'count'})

def get_top_three_sales(city):
    ventas_agg = ventas[ventas['city_name']==city].groupby('product_name').agg({'invoice_number': 'count'})
    ventas_agg_top3 = ventas_agg.sort_values(by="invoice_number", ascending=False).head(3)
    ventas_agg_top3.reset_index(inplace=True)
    return(ventas_agg_top3)

ventas_agg_top_prod = get_top_three_sales('MEDELLIN')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dt.DataTable(id = 'data-table-products', 
                    columns=[{"name": i, "id": i} for i in ventas_agg_top_prod.columns],
                    data=ventas_agg_top_prod.to_dict('records')),
    dcc.Dropdown(
                        id='city_dd',
                        options=[{'label': i, 'value': i} for i in cities],
                        value='MEDELLIN',
                        #multi=True,
                        # style={'width': '50%'}
                        )
])


@app.callback(
    Output('data-table-products', 'data'),
    [Input('city_dd', 'value')])
def update_figure(city):
    ventas_agg_top_prod = get_top_three_sales(city)

    return ventas_agg_top_prod.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
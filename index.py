import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

# must add this line in order for the app to be deployed successfully on Heroku
from app import server
from app import app
# import all pages in the app
from apps import sales, singapore, home

# building the navigation bar
# https://github.com/facultyai/dash-bootstrap-components/blob/master/examples/advanced-component-usage/Navbars.py
nav_item_home = dbc.NavItem(dbc.NavLink("Home", href="/home"))
nav_item_sales = dbc.NavItem(dbc.NavLink("Sales", href="/sales"))
nav_item_inventory = dbc.NavItem(dbc.NavLink("Inventory", href="/singapore"))

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/Logo-menu.png", height="50px")),
                        dbc.Col(dbc.NavbarBrand("Naturela", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="/home",
            ),
            # dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    # right align dropdown menu with ml-auto className
                    [nav_item_home, nav_item_sales, nav_item_inventory], className="ml-auto", navbar=True
                ),
                # id="navbar-collapse2",
                navbar=True,
            ),
        ]
    ),
    # color="dark",
    # dark=True,
    className="mb-5",
)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/sales':
        return sales.layout
    elif pathname == '/singapore':
        return singapore.layout
    else:
        return home.layout

if __name__ == '__main__':
    app.run_server(debug=True)
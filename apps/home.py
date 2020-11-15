import dash_html_components as html
import dash_bootstrap_components as dbc

# needed only if running this as a single page app
#external_stylesheets = [dbc.themes.LUX]

#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# change to app.layout if running as single page app instead
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Naturela Analytics Analysis Dashboard", className="text-center")
                    , className="mb-5 mt-5")
        ]),
        dbc.Row([
            dbc.Col(html.Div("Naturela, providing nutrition and well-being since 2007, with local and natural ingredients of high nutritional value; using the spirulina in most of the products."), align="baseline"),
            ]),

        dbc.Row([
            dbc.Col(html.Div("The uncertainty of our planning team when making the forecast (number of units to produce and raw materials to buy), due to the high number of references that are handled month by month and variables to consider such as product category, price, sales channel, customer location and customer type makes it essential for the team to have a model that supports this process. Actually, the production is planned based on sales historic of the previous year."), align="around"),
        ], justify="center"),
        dbc.Row([
            dbc.Col(html.Iframe(src=f'https://www.youtube.com/embed/5cnpaf1H0pQ', height="400px", width="720px")
                    , className="mb-5 mt-5 text-center")
        ]),

        dbc.Row([
            dbc.Col(dbc.Card(children=[dbc.Button("Visit us in naturela.com",
                                                  href="https://naturela.com/",
                                                  color="primary",
                                                  className="mt-3"),
                                       ],
                             body=True, color="dark", outline=True)
                    , width=12, className="mb-4"),
        ], className="mb-5"),


    ])

])


# needed only if running this as a single page app
# if __name__ == '__main__':
#     app.run_server(host='127.0.0.1', debug=True)
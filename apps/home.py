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
            dbc.Col(html.H5(children='This is the intro of the manual and the research'
                                     )
                    , className="mb-4")
            ]),

        dbc.Row([
            dbc.Col(html.H5(children='This is a little more detail on the process here and there.')
                    , className="mb-5")
        ]),

        dbc.Row([
            dbc.Col(html.Iframe(src=f'https://www.youtube.com/embed/5cnpaf1H0pQ', height="400px", width="720px")
                    , className="mb-5 mt-5 text-center")
        ]),

        dbc.Row([
            dbc.Col(dbc.Card(children=[html.H3(children='This is a link to something with link that needs a card css',
                                               className="text-center"),
                                       dbc.Row([dbc.Col(dbc.Button("Global", href="https://data.europa.eu/euodp/en/data/dataset/covid-19-coronavirus-data/resource/55e8f966-d5c8-438e-85bc-c7a5a26f4863",
                                                                   color="primary"),
                                                        className="mt-3"),
                                                dbc.Col(dbc.Button("Singapore", href="https://data.world/hxchua/covid-19-singapore",
                                                                   color="primary"),
                                                        className="mt-3")], justify="center")
                                       ],
                             body=True, color="dark", outline=True)
                    , width=4, className="mb-4"),

            dbc.Col(dbc.Card(children=[html.H3(children='Others links',
                                               className="text-center"),
                                       dbc.Button("GitHub",
                                                  href="https://github.com/meredithwan/covid-dash-app",
                                                  color="primary",
                                                  className="mt-3"),
                                       ],
                             body=True, color="dark", outline=True)
                    , width=4, className="mb-4"),

            dbc.Col(dbc.Card(children=[html.H3(children='Others links',
                                               className="text-center"),
                                       dbc.Button("Medium",
                                                  href="https://medium.com/@meredithwan",
                                                  color="primary",
                                                  className="mt-3"),

                                       ],
                             body=True, color="dark", outline=True)
                    , width=4, className="mb-4")
        ], className="mb-5"),


    ])

])


# needed only if running this as a single page app
# if __name__ == '__main__':
#     app.run_server(host='127.0.0.1', debug=True)

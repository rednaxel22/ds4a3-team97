import dash
import dash_bootstrap_components as dbc

# bootstrap theme
# https://bootswatch.com/lux/
# external_stylesheets = [dbc.themes.MINTY]
external_stylesheets = [dbc.themes.LUX]
# external_stylesheets = [dbc.themes.SOLAR]
# external_stylesheets = [dbc.themes.YETI]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server
app.config.suppress_callback_exceptions = True
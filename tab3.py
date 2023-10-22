from dash import html
from dash import dcc
import plotly.graph_objects as go


def render_tab(df):

    layout = html.Div([html.H1('Kanały sprzedaży', style={'text-align': 'center'}),
                       html.Div([dcc.Dropdown(id='store_dropdown',
                                              options=[{'label': Store_type, 'value': Store_type}
                                                       for Store_type in df['Store_type'].unique()],
                                              value=df['Store_type'].unique()[
                                                  0],
                                              style={'margin': 'auto', 'width': '50%'}),
                                 html.Div([html.Div([dcc.Graph(id='bar-weekday-sales')], style={'width': '70%', 'height': '100%'}),
                                           html.Div([dcc.Graph(id='sunburst-customers')], style={'width': '60%'})], style={'display': 'flex'})])
                       ])

    return layout

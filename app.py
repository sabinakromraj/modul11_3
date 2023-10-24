import pandas as pd
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import dash_auth
import plotly.graph_objects as go
import plotly.express as px
import tab1
import tab2
import tab3
from class_db import db

df = db()
df.merge()

USERNAME_PASSWORD = [['user', 'pass']]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)

auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD)

app.layout = html.Div([html.Div([dcc.Tabs(id='tabs', value='tab-1', children=[
    dcc.Tab(label='Sprzedaż globalna', value='tab-1'),
    dcc.Tab(label='Produkty', value='tab-2'),
    dcc.Tab(label='Kanały Sprzedaży', value='tab-3')
]),
    html.Div(id='tabs-content')], style={'width': '80%', 'margin': 'auto'})],
    style={'height': '100%'})


@app.callback(Output('tabs-content', 'children'), [Input('tabs', 'value')])
def render_content(tab):

    if tab == 'tab-1':
        return tab1.render_tab(df.merged)
    elif tab == 'tab-2':
        return tab2.render_tab(df.merged)
    elif tab == 'tab-3':
        return tab3.render_tab(df.merged)


@app.callback(Output('bar-sales', 'figure'),
              [Input('sales-range', 'start_date'), Input('sales-range', 'end_date')])
def tab1_bar_sales(start_date, end_date):

    truncated = df.merged[(df.merged['tran_date'] >= start_date) & (
        df.merged['tran_date'] <= end_date)]
    grouped = truncated[truncated['total_amt'] > 0].groupby([pd.Grouper(
        key='tran_date', freq='M'), 'Store_type'])['total_amt'].sum().round(2).unstack()

    traces = []
    for col in grouped.columns:
        traces.append(go.Bar(x=grouped.index, y=grouped[col], name=col, hoverinfo='text',
                             hovertext=[f'{y/1e3:.2f}k' for y in grouped[col].values]))

    data = traces
    fig = go.Figure(data=data, layout=go.Layout(
        title='Przychody', barmode='stack', legend=dict(x=0, y=-0.5)))

    return fig


@app.callback(Output('choropleth-sales', 'figure'),
              [Input('sales-range', 'start_date'), Input('sales-range', 'end_date')])
def tab1_choropleth_sales(start_date, end_date):

    truncated = df.merged[(df.merged['tran_date'] >= start_date) & (
        df.merged['tran_date'] <= end_date)]
    grouped = truncated[truncated['total_amt'] > 0].groupby(
        'country')['total_amt'].sum().round(2)

    trace0 = go.Choropleth(colorscale='Viridis', reversescale=True,
                           locations=grouped.index, locationmode='country names',
                           z=grouped.values, colorbar=dict(title='Sales'))
    data = [trace0]
    fig = go.Figure(data=data, layout=go.Layout(title='Mapa', geo=dict(
        showframe=False, projection={'type': 'natural earth'})))

    return fig


@app.callback(Output('barh-prod-subcat', 'figure'),
              [Input('prod_dropdown', 'value')])
def tab2_barh_prod_subcat(chosen_cat):

    grouped = df.merged[(df.merged['total_amt'] > 0) & (df.merged['prod_cat'] == chosen_cat)].pivot_table(
        index='prod_subcat', columns='Gender', values='total_amt', aggfunc='sum').assign(_sum=lambda x: x['F']+x['M']).sort_values(by='_sum').round(2)

    traces = []
    for col in ['F', 'M']:
        traces.append(
            go.Bar(x=grouped[col], y=grouped.index, orientation='h', name=col))

    data = traces
    fig = go.Figure(data=data, layout=go.Layout(
        barmode='stack', margin={'t': 20, }))
    return fig


@app.callback(Output('bar-weekday-sales', 'figure'),
              [Input('store_dropdown', 'value')])
def tab3_bar_weekday_sales(chosen_cat):

    filtered_data = df.merged[(df.merged['Store_type'] == chosen_cat) & (
        df.merged['total_amt'] > 0)]
    grouped_sales = filtered_data.groupby(filtered_data['tran_date'].dt.dayofweek)[
        'total_amt'].sum()
    grouped_transactions = filtered_data.groupby(
        filtered_data['tran_date'].dt.dayofweek).size()
    weekdays = ['Poniedziałek', 'Wtorek', 'Środa',
                'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
    max_value_day = weekdays[grouped_sales.idxmax()]

    trace0 = go.Bar(x=grouped_sales.values, y=weekdays, orientation='h', text=[f'{amt:.2f}' for amt in grouped_sales.values],
                    textposition='inside', name='Wartość sprzedaży')
    max_value_index = weekdays.index(max_value_day)
    trace0.marker = dict(color=['rgba(44, 160, 44, 0.5)' if i !=
                         max_value_index else 'rgba(44, 255, 44, 0.8)' for i in range(len(weekdays))])

    trace1 = go.Bar(x=grouped_transactions.values, y=weekdays, orientation='h', text=[f'{amt}' for amt in grouped_transactions.values],
                    textposition='inside', name='Ilość transakcji')
    max_value_index = weekdays.index(max_value_day)
    trace1.marker = dict(color=['rgba(31, 119, 180, 0.5)' if i !=
                         max_value_index else 'rgba(31, 119, 180, 0.8)' for i in range(len(weekdays))])

    data = [trace0, trace1]
    fig = go.Figure(data=data, layout=go.Layout(barmode='relative', showlegend=True,
                    legend=dict(orientation='h', x=0.1, y=1.2, font=dict(size=20))))
    return fig


@app.callback(Output('sunburst-customers', 'figure'),
              [Input('store_dropdown', 'value')])
def tab3_sunburst_customers(chosen_cat):

    filtered_data = df.merged[(df.merged['total_amt'] > 0) & (
        df.merged['Store_type'] == chosen_cat)]
    grouped_data = filtered_data.groupby(['country', 'Gender'])[
        'cust_id'].count().reset_index()

    fig = px.sunburst(grouped_data, path=[
                      'country', 'Gender'], values='cust_id')

    fig.update_layout(autosize=True, title='Segmentacja klientów', title_x=0.5)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)

import pandas as pd
import dash
from dash import dcc, html
import sqlite3

from .constants import DB_PATH, NEWEST_DATA_QUERY, START_DATE
from .figures import (getBodyWeightChart, 
                      getNutritionChart, 
                      getStepsChart,
                      getEnergyBalance,
                      getBWGoal,)

# Create the Dash app
app = dash.Dash(__name__)

# get data 
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
initialDataFrame = (pd.read_sql_query(NEWEST_DATA_QUERY, conn)
        .assign(dateTime=lambda x: pd.to_datetime(x['dateTime']))
        .rename(columns={'dateTime': 'Date'})
        .sort_values('Date'))
conn.close()

app.layout = html.Div([
    html.Div(id = 'title',children='FitBot Dashboard'),
    html.Div(
        children=[
            html.Div(
                id='weight-info-box',
                children=[
                    html.H4("Today's Bodyweight"),
                    html.P(id='today-bw'),
                ],
                style={'border': '1px solid black', 'padding': '10px', 'margin': '5px'}
            ),
            html.Div(
                id='goal-info-box',
                children=[
                    html.H4("Today's Goal"),
                    html.P(id='today-goal'),
                ],
                style={'border': '1px solid black', 'padding': '10px', 'margin': '5px'}
            ),
            html.Div(
                id='energy-balance-7-box',
                children=[
                    html.H4("Energy Balance (7 Days)"),
                    html.P(id='energy-balance-7'),
                ],
                style={'border': '1px solid black', 'padding': '10px', 'margin': '5px'}
            ),
            html.Div(
                id='energy-balance-14-box',
                children=[
                    html.H4("Energy Balance (14 Days)"),
                    html.P(id='energy-balance-14'),
                ],
                style={'border': '1px solid black', 'padding': '10px', 'margin': '5px'}
            ),
            html.Div(
                id='energy-balance-21-box',
                children=[
                    html.H4("Energy Balance (21 Days)"),
                    html.P(id='energy-balance-21'),
                ],
                style={'border': '1px solid black', 'padding': '10px', 'margin': '5px'}
            ),
            html.Div(
                id='energy-balance-28-box',
                children=[
                    html.H4("Energy Balance (28 Days)"),
                    html.P(id='energy-balance-28'),
                ],
                style={'border': '1px solid black', 'padding': '10px', 'margin': '5px'}
            ),
        ],
        style={'display': 'flex', 'flexDirection': 'row', 'alignItems': 'center'}
    ),
    html.Div(
        dcc.Graph(id='graph1', figure=getBodyWeightChart(initialDataFrame.copy()),config={'displayModeBar': False}), 
        style={
            'border': '2px solid black',  # Black border
            'padding': '10px',           # Padding inside the box
            'margin-bottom': '20px',      # Space between the boxes
            'height': '1000px'
        }
    ),
    html.Div(
        dcc.Graph(id='graph2', figure=getNutritionChart(initialDataFrame.copy()),config={'displayModeBar': False}), 
        style={
            'border': '2px solid black',  # Black border
            'padding': '10px',           # Padding inside the box
            'margin-bottom': '20px'      # Space between the boxes
        }
    ),
    html.Div(
        dcc.Graph(id='graph3', figure=getStepsChart(initialDataFrame.copy()),config={'displayModeBar': False}), 
        style={
            'border': '2px solid black',  # Black border
            'padding': '10px',           # Padding inside the box
            'margin-bottom': '20px'      # Space between the boxes
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=10000,  # Update every second
        n_intervals=0
    )
])

# Define the callback to update the graphs
@app.callback(
    [
        dash.dependencies.Output('graph1', 'figure'),
        dash.dependencies.Output('graph2', 'figure'),
        dash.dependencies.Output('graph3', 'figure'),
        dash.dependencies.Output('title', 'children'),
        dash.dependencies.Output('today-bw', 'children'),
        dash.dependencies.Output('today-goal', 'children'),
        dash.dependencies.Output('energy-balance-7', 'children'),
        dash.dependencies.Output('energy-balance-14', 'children'),
        dash.dependencies.Output('energy-balance-21', 'children'),
        dash.dependencies.Output('energy-balance-28', 'children'),
    ],
    [
        dash.dependencies.Input('interval-component', 'n_intervals'),
    ],
)
def update_graphs(n):
    '''
    Get newest data from the database, create new graphs and send them on.
    Also get the Energy Balances, the BW Goal for today and the Actual BW.
    '''
    # Get new data
    conn = sqlite3.connect(DB_PATH)
    _df = (pd.read_sql_query(NEWEST_DATA_QUERY, conn)
            .assign(dateTime=lambda x: pd.to_datetime(x['dateTime']))
            .rename(columns={'dateTime': 'Date'})
            .sort_values('Date'))
    conn.close()

    # Create the new graphs
    fig1, fig2, fig3 = getBodyWeightChart(_df), getNutritionChart(_df), getStepsChart(_df)

    # Today's weight
    todayBW = _df.loc[_df.Date == _df.Date.max(),'weight'].values[0]   
    todayGoal = getBWGoal(_df)
    energyBalance7 = getEnergyBalance(_df,7)
    energyBalance14 = getEnergyBalance(_df,14)
    energyBalance21 = getEnergyBalance(_df,21)
    energyBalance28 = getEnergyBalance(_df,28)

    return (fig1, fig2, fig3, str(n),
            f"{todayBW:.2f} kg",
            f"{todayGoal:.2f} kg",
            f"{energyBalance7} kcal",
            f"{energyBalance14} kcal",
            f"{energyBalance21} kcal",
            f"{energyBalance28} kcal",
            )


__all__ = ['app']

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
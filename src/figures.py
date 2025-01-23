import sys
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import datetime as dt

pd.options.plotting.backend = "plotly"
sys.path.append('../src')

from .constants import GOALS_PATH, KG_TO_LBS, CALORIES_PER_LB, FIG_START_DATE
from .utils import LinearRegression

GOALS = pd.read_excel(GOALS_PATH,sheet_name='Weight Goal',usecols='D:G')


def getStepsChart(df: pd.DataFrame) -> go.Figure:
   return  (df.plot(x='Date', y = 'steps', kind = 'bar')
               .add_hline(y = 10_000, line_dash = 'dash', line_color = 'red')
               .update_layout(
                              yaxis = dict(showgrid = False, showticklabels = True, title = '', zeroline = False),
                              yaxis2 = dict(showgrid = False, showticklabels = True, title = '', zeroline = False),
                              showlegend = False,
                              title = 'Step count over time',
                              title_x = 0.5,
                              uirevision = 'None',
                              xaxis=dict(
                                            range=[FIG_START_DATE, df.Date.max()],  # Default visible range
                                            showgrid = False
                                        ),                                      
                        )
                  .update_yaxes(matches=None)
                  .update_annotations(text = ''))

def getNutritionChart(df: pd.DataFrame) -> go.Figure:
    # Create figure
    fig = go.Figure()

    # Add stacked bars for macros
    fig.add_trace(go.Bar(
        x=df['Date'], y=df['protein'], name='Protein',
        marker_color='green', hoverinfo='y'
    ))

    fig.add_trace(go.Bar(
        x=df['Date'], y=df['carbs'], name='Carbs',
        marker_color='blue', hoverinfo='y'
    ))
    fig.add_trace(go.Bar(
        x=df['Date'], y=df['fat'], name='Fat',
        marker_color='orange', hoverinfo='y'
    ))


    # Add line for calories (secondary y-axis)
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['calories'].apply(lambda x: None if x == 0 else x), name='Calories',
        mode='lines', line=dict(color='red', width=2),
        yaxis='y2'
    ))

    # Add red horizontal line for goal
    fig.add_shape(
        type='line', x0=df['Date'].min(), x1=df['Date'].max(),
        y0=2000, y1=2000, line=dict(color='red', dash='dash'),
        yref='y2'  # Reference secondary y-axis
    )

    fig.add_shape(
        type='line', x0=df['Date'].min(), x1=df['Date'].max(),
        y0=150, y1=150, line=dict(color='green', dash='dash'),
        yref='y1'  # Reference y-axis
    )

    # Update layout for dual y-axes and appearance
    fig.update_layout(
        title='Macros and Calories Over Time',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Macros (g)', side='left'),
        yaxis2=dict(
            title='Calories', overlaying='y', side='right'
        ),
        barmode='stack',
        legend=dict(title='Legend', orientation='h'),
    )
    #remove gridlines
    return fig.update_layout(
                        xaxis_showgrid=False,
                        yaxis_showgrid=False,
                        yaxis2_showgrid=False,
                        yaxis = dict(showgrid = False, showticklabels = True, title = '', zeroline = False),
                        yaxis2 = dict(showgrid = False, showticklabels = True, title = '', zeroline = False),
                        showlegend = False,
                        title = 'Macros and Calories over Time',
                        title_x = 0.5,
                        uirevision = 'None',
                        xaxis=dict(
                                    range=[FIG_START_DATE, df.Date.max()],  # Default visible range
                                    showgrid = False
                                ),
        )

def make_tangent_line(actualVgoal:pd.DataFrame,lookback: int)-> pd.DataFrame:
    '''
    makes a line of best fit for the actual weight data over the past `lookback` days to
    be displayed on the bodyweight graph long with the GOALS.
    '''
    domain = actualVgoal.copy().loc[lambda s: s.Date.between(dt.datetime.today()-dt.timedelta(lookback),
                                                    dt.datetime.today()+dt.timedelta(lookback)),
                            ['Date','weight_actual']]\
                        .assign(Time = lambda x: (x.Date - x.Date.min()).dt.days)
    training = domain.copy().dropna()

    lr = LinearRegression(training.Time.values.reshape(-1,1),training.weight_actual.values)
    lr.fit()

    domain[f'weight_trend_{lookback}'] = lr.predict(domain.Time.values.reshape(-1,1))
    return   (domain.drop(columns = ['weight_actual','Time'])
                    .melt(id_vars='Date', var_name='Type', value_name='Weight'))

def make_trend_line(df:pd.DataFrame,window: int)-> pd.DataFrame:
    '''
    makes a smoothed trendline for the weight data over all time with a window of 
    be displayed on the bodyweight graph long with the GOALS
    '''
    date = df.Date.min()
    min_date = df.Date.min()
    domain = df.copy()['Date weight'.split()].assign(Time = lambda x: (x.Date - x.Date.min()).dt.days)
    smooth_trend = []
    slope = []
    while date <= df.Date.max():
        smoothing_window = domain.copy().loc[lambda s: s.Date.between(date-dt.timedelta(window-1),date+dt.timedelta(window))]
        date += dt.timedelta(1)
        lr = LinearRegression(smoothing_window.Time.values.reshape(-1,1),smoothing_window.weight.values)
        lr.fit()
        smooth_trend.append(lr.predict(np.array([[(date-min_date).days]]))[0])
        slope.append(lr.beta[1])
    domain['smooth_trend'] = smooth_trend
    domain['slope'] = slope
    domain['slope'] = domain['slope']*CALORIES_PER_LB*KG_TO_LBS
    return (domain.drop(columns = ['Time','weight'])
                    .melt(id_vars='Date', var_name='Type', value_name='Weight'))


def getBodyWeightChart(df:pd.DataFrame)->go.Figure:
    actualVgoal = df['Date weight'.split()].merge(GOALS, on='Date', how = 'outer',suffixes=('_actual', '_goal'))
    maxDate = max(actualVgoal.Date.max(),dt.datetime.today(),df.Date.max())
    fig = (
    actualVgoal['Date weight_actual weight_goal'.split()]
        .melt(id_vars='Date', var_name='Type', value_name='Weight')
        .pipe(lambda x: pd.concat([x,make_trend_line(df,14)],axis=0))
        .pipe(lambda x: pd.concat([x,make_tangent_line(actualVgoal,7)],axis=0))
        .pipe(lambda x: pd.concat([x,make_tangent_line(actualVgoal,14)],axis=0))
        .pipe(lambda x: pd.concat([x,make_tangent_line(actualVgoal,21)],axis=0))
        .assign(defict_indication = lambda x: x.Type == 'slope')
        .plot(x='Date', y='Weight', kind='line', color='Type', facet_row='defict_indication', height = 1000)
        .update_traces(selector=dict(name = 'weight_actual'), line = dict(color = 'blue'),opacity = 0.25, mode = 'lines+markers')
        .update_traces(selector=dict(name = 'weight_actual'), marker = dict(color = 'red', size = 5, opacity = 1))
        .update_traces(selector=dict(name = 'smooth_trend'), line = dict(color = 'blue'))
        .update_traces(selector=dict(name = 'weight_goal'), line = dict(dash = 'dash', color = 'black'))
        .update_traces(selector=dict(name='weight_trend_7'), opacity=1.0, line = dict(color = 'darkred'))
        .update_traces(selector=dict(name='weight_trend_14'), opacity=0.7, line = dict(color = 'firebrick'))
        .update_traces(selector=dict(name='weight_trend_21'), opacity=0.4, line = dict(color = 'salmon'))
        .update_traces(selector=dict(name='slope'), opacity=0.25, line = dict(color = 'green'))
        .add_hline(y = -1000, line_dash = 'dash', line_color = 'red', row = 1,opacity = 0.5)
        .add_hline(y = -500, line_dash = 'dash', line_color = 'red', row = 1,opacity = 0.25)
        .add_hline(y = 0, line_dash = 'dash', line_color = 'red', row = 1,opacity = 0.125)
        .add_hline(y = 500, line_dash = 'dash', line_color = 'red', row = 1,opacity = 0.25)
        .add_hline(y = 1000, line_dash = 'dash', line_color = 'red', row = 1,opacity = 0.5)
        .update_layout(
            yaxis = dict(showgrid = False, showticklabels = True, title = '', zeroline = False),
            yaxis2 = dict(showgrid = False, showticklabels = True, title = '', zeroline = False),
            showlegend = False,
            title = 'Weight and Goals over Time',
            title_x = 0.5,
            uirevision = 'None',
            xaxis=dict(
                        range=[FIG_START_DATE, maxDate],  # Default visible range
                        showgrid = False
                    ),
        )
        .update_yaxes(matches=None)
        .update_annotations(text = ''))
    return fig

def getEnergyBalance(df:pd.DataFrame,window: int)-> int:
    max_date = df.Date.max()
    min_date = max_date - dt.timedelta(window)
    domain = df.copy().sort_values('Date',ignore_index=True).iloc[-window:]['Date weight'.split()]
    domain['Time'] = (domain.Date - min_date).dt.days

    lr = LinearRegression(domain.Time.values.reshape(-1,1),domain.weight.values)
    lr.fit()

    slope = lr.beta[1]
    energyBalance = slope*CALORIES_PER_LB*KG_TO_LBS
    return int(energyBalance)

def getBWGoal(df:pd.DataFrame)-> int:
    try:
        return GOALS.loc[GOALS.Date == dt.datetime.today().strftime('%Y-%m-%d'),'weight'].values[0]
    except:
        return 0


__all__ = ['getStepsChart','getNutritionChart','getBodyWeightChart']
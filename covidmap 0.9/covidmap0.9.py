################################################
#                _     _                       #
#               (_)   | |                      #
#  ___ _____   ___  __| |_ __ ___   __ _ _ __  #
# / __/ _ \ \ / / |/ _` | '_ ` _ \ / _` | '_ \ #
#| (_| (_) \ V /| | (_| | | | | | | (_| | |_) |#
# \___\___/ \_/ |_|\__,_|_| |_| |_|\__,_| .__/ #
#                                       | |    #
#                                       |_|    #
#                                              #
################################################

import json
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from urllib.request import urlopen
import psycopg2 as pspg

def retrieveData():
    '''
    Connects to the covidPolitics database. Queries covid data, then queries 
    political data. Merges the data on FIPS code and returns the merged df.
    '''
    conn = pspg.connect("dbname=covidPolitics user=alashley")
    cur = conn.cursor()
    
    cur.execute("select * from covid where date = 11")
    covid_pull = list(cur.fetchall())
    df_covid = pd.DataFrame(covid_pull, columns =['Date', 'County', 'State', 'FIPS', 'Cases', 'Deaths']) 
    
    cur.execute("select county, state, FIPS, gop_2016, gop_2020 from politics")
    politics_pull = list(cur.fetchall())
    df_politics = pd.DataFrame(politics_pull, columns =['County', 'State', 'FIPS', 'GOP_2016', 'GOP_2020']) 
    
    conn.close()
    
    df = pd.merge(df_covid, df_politics, how = 'left', left_on=['FIPS'], right_on=['FIPS'])
    
    return df

#temp = retrieveData()
#df = temp.copy()

df = pd.read_csv('DB_Covid.csv', dtype={'fips':float})
        
# Adds leading 0's to FIPS codes where needed

df['FIPS'] = df['FIPS'].astype('int64', copy=True)
df = df[df['FIPS'] < 80000].copy(deep=True)
df['FIPS'] = df['FIPS'].astype('str', copy=True)
df['FIPS'] = df['FIPS'].str.rjust(5, '0')

# Loads county outline vectors with which to render the map, matched by fips

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    countyData = json.load(response)

mapbox_accesstoken = 'pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A'

###############################################################################

counties = df['County_x'].str.title().tolist()

pl_deep= [[0.0, 'rgb(253, 253, 204)'],
          [0.1, 'rgb(243, 79, 78)'],
          [0.2, 'rgb(243, 79, 78)'],
          [0.3, 'rgb(237, 63, 62)'],
          [0.4, 'rgb(237, 63, 62)'],
          [0.5, 'rgb(230, 31, 32)'],
          [0.6, 'rgb(230, 31, 32)'],
          [0.7, 'rgb(218, 15, 19)'],
          [0.8, 'rgb(218, 15, 19)'],
          [0.9, 'rgb(201, 0, 11)'],
          [1.0, 'rgb(201, 0, 11)']]

pl_pol= [[0.0, 'rgb(3, 1, 140)'],
         [0.1, 'rgb(33, 42, 165)'],
         [0.2, 'rgb(66, 89, 195)'],
         [0.3, 'rgb(123, 159, 242)'],
         [0.4, 'rgb(158, 194, 255)'],
         [0.5, 'rgb(253, 253, 204)'],
         [0.6, 'rgb(243, 79, 78)'],
         [0.7, 'rgb(237, 63, 62)'],
         [0.8, 'rgb(230, 31, 32)'],
         [0.9, 'rgb(218, 15, 19)'],
         [1.0, 'rgb(201, 0, 11)']]
                                
Types = ['Cases','Deaths', 'GOP_2020']

trace1 = []    
    
for q in Types:
    if q != 'GOP_2020':   
        trace1.append(go.Choroplethmapbox(
            geojson = countyData,
            locations = df['FIPS'].tolist(),
            z = df[q].tolist(), 
            colorscale = pl_deep,
            text = counties,
            colorbar = dict(thickness=20, ticklen=3),
            marker_line_width=0, marker_opacity=0.7,
            visible=False,
            subplot='mapbox1',
            hovertemplate = "<b>%{text}</b><br><br>" +
                            "Number of "+str(q)+"=%{z}<br>" +
                            "<extra></extra>"))
    else:
        trace1.append(go.Choroplethmapbox(
            geojson = countyData,
            locations = df['FIPS'].tolist(),
            z = df[q].tolist(), 
            colorscale = pl_pol,
            text = counties,
            colorbar = dict(thickness=20, ticklen=3),
            marker_line_width=0, marker_opacity=0.7,
            visible=False,
            subplot='mapbox1',
            hovertemplate = "<b>%{text}</b><br><br>" +
                            "Proportion of GOP voters = %{z}<br>" +
                            "<extra></extra>"))
    
trace1[0]['visible'] = True

trace2 = []    
    
for q in Types:
    trace2.append(go.Bar(
        x=df.sort_values([q], ascending=False).head(10)[q],
        y=df.sort_values([q], ascending=False).head(10)['County_x'].str.title().tolist(),
        xaxis='x2',
        yaxis='y2',
        marker=dict(
            color='rgba(77, 153, 219, 0.5)',
            line=dict(
                color='rgba(77, 153, 219, 0.7)',
                width=0.5),
        ),
        visible=False,
        orientation='h',
    ))
    
trace2[0]['visible'] = True

###############################################################################

layout = go.Layout(
    title = {'text': 'National COVID-19 Cases: November, 2020',
    		 'font': {'size':28, 
    		 		  'family':'Arial'}},
    autosize = True,
    
    mapbox1 = dict(
        domain = {'x': [0.3, 1],'y': [0, 1]},
        center = {"lat": 37.0902, "lon": -95.7129},
        accesstoken = mapbox_accesstoken, 
        zoom = 2.5),

    xaxis2={
        'zeroline': False,
        "showline": False,
        "showticklabels":True,
        'showgrid':True,
        'domain': [0, 0.25],
        'side': 'left',
        'anchor': 'x2',
    },
    yaxis2={
        'domain': [0.4, 0.9],
        'anchor': 'y2',
        'autorange': 'reversed',
    },
    margin=dict(l=100, r=20, t=70, b=70),
    paper_bgcolor='rgb(227, 235, 240)',
    plot_bgcolor='rgb(227, 235, 240)',
)

layout.update(updatemenus=list([
    dict(x=0,
         y=1,
         xanchor='left',
         yanchor='middle',
         buttons=list([
             dict(
                 args=['visible', [True, False, False]],
                 label='Number of COVID-19 cases by county:',
                 method='restyle'
                 ),
             dict(
                 args=['visible', [False, True, False]],
                 label='Number of COVID-19 deaths by county:',
                 method='restyle'
                 ),
             dict(
                 args=['visible', [False, False, True]],
                 label='Proportion of GOP voters by county:',
                 method='restyle'
                 )  
            ]),
        )]))

###############################################################################

fig=go.Figure(data=trace2 + trace1, layout=layout)

stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=stylesheet)

app.layout = html.Div(children=[
    html.H1(children=''),

    dcc.Graph(
        id='graph-1',
        figure=fig
    ),

    html.Div(children='''
        Data source(s): The New York Times (https://github.com/nytimes/covid-19-data), 
        Townhall (https://github.com/tonmcg/US_County_Level_Election_Results_08-16/blob/master/2016_US_County_Level_Presidential_Results.csv)
    ''')
])

if __name__ == '__main__':
    app.run_server(debug=True)
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
    conn = pspg.connect("dbname=covidPolitics user=shaman")
    cur = conn.cursor()
    
    cur.execute("select * from covid where date = 11")
    covid_pull = list(cur.fetchall())
    df_covid = pd.DataFrame(covid_pull, columns =['County', 'State', 'FIPS', 'Cases', 'Deaths']) 
    
    cur.execute("select county, state, FIPS, gop_2016, gop_2020 from politics")
    politics_pull = list(cur.fetchall())
    df_politics = pd.DataFrame(politics_pull, columns =['County', 'State', 'FIPS', 'GOP_2016', 'GOP_2020']) 
    
    conn.close ()
    
    df = pd.merge(df_covid, df_politics, how = 'left', left_on=['FIPS'], right_on=['FIPS'])
    
    return df

#temp = retrieveData()
#df = temp.copy()

df = pd.read_csv('DB_Covid0.7.csv', dtype={'fips':float})
        
# This whole section is dedicated to adding leading 0's to fips where needed
# RIP Adam for wasting 6 hours diagnosing this problem as a json issue...

df['fips'] = df['fips'].astype('int64', copy=True)
df = df[df['fips'] < 80000].copy(deep=True)
df['fips'] = df['fips'].astype('str', copy=True)
df['fips'] = df['fips'].str.rjust(5, '0')

# Loads county outline vectors with which to render the map, matched by fips

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    countyData = json.load(response)

mapbox_accesstoken = 'pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A'

###############################################################################
#          Two element structure that refreshes on dropdown selection         #
###############################################################################

counties = df['county'].str.title().tolist()

pl_deep=[[0.0, 'rgb(253, 253, 204)'],
         [0.1, 'rgb(201, 235, 177)'],
         [0.2, 'rgb(145, 216, 163)'],
         [0.3, 'rgb(102, 194, 163)'],
         [0.4, 'rgb(81, 168, 162)'],
         [0.5, 'rgb(72, 141, 157)'],
         [0.6, 'rgb(64, 117, 152)'],
         [0.7, 'rgb(61, 90, 146)'],
         [0.8, 'rgb(65, 64, 123)'],
         [0.9, 'rgb(55, 44, 80)'],
         [1.0, 'rgb(39, 26, 44)']]

Types = ['cases','deaths', 'affiliation']

trace1 = []    
    
for q in Types:
    trace1.append(go.Choroplethmapbox(
        geojson = countyData,
        locations = df['fips'].tolist(),
        z = df[q].tolist(), 
        colorscale = pl_deep,
        text = counties,
        colorbar = dict(thickness=20, ticklen=3),
        marker_line_width=0, marker_opacity=0.7,
        visible=False,
        subplot='mapbox1',
        hovertemplate = "<b>%{text}</b><br><br>" +
                        "Number: %{z}<br>" +
                        "<extra></extra>"))
    

trace1[0]['visible'] = True

trace2 = []    
    
for q in Types:
    trace2.append(go.Bar(
        x=df.sort_values([q], ascending=False).head(10)[q],
        y=df.sort_values([q], ascending=False).head(10)['county'].str.title().tolist(),
        xaxis='x2',
        yaxis='y2',
        marker=dict(
            color='rgba(91, 207, 135, 0.3)',
            line=dict(
                color='rgba(91, 207, 135, 2.0)',
                width=0.5),
        ),
        visible=False,
        name='Place holder{}'.format(q),
        orientation='h',
    ))
    
trace2[0]['visible'] = True

latitude = 40.0
longitude = 100.0

###############################################################################
#         Making a layout that doesn't give up on life over every NA..        #
###############################################################################

layout = go.Layout(
    title = {'text': 'National Covid Cases in October 2020',
    		 'font': {'size':28, 
    		 		  'family':'Arial'}},
    autosize = True,
    
    mapbox1 = dict(
        domain = {'x': [0.3, 1],'y': [0, 1]},
        center = dict(lat=latitude, lon=longitude),
        accesstoken = mapbox_accesstoken, 
        zoom = 12),

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
    paper_bgcolor='rgb(204, 204, 204)',
    plot_bgcolor='rgb(204, 204, 204)',
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
                 label='Number of CoVID-19 deaths by county:',
                 method='restyle'
                 ),
             dict(
                 args=['visible', [False, False, True]],
                 label='Political affiliation by county:',
                 method='restyle'
                 )  
            ]),
        )]))

fig=go.Figure(data=trace2 + trace1, layout=layout)

###############################################################################
#            The actual dash part that makes an app go brrrrrr                #
###############################################################################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children=''),

    dcc.Graph(
        id='example-graph-1',
        figure=fig
    ),

    html.Div(children='''
        Data did done come from these dang-ole places. 
    ''')
])

if __name__ == '__main__':
    app.run_server(debug=True)
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from machine_learning import topic_extraction, create_dict_list_of_topics
import time

global final_reddit_topic_df
global top_post_df
global dict_topics

# Set up the app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# app = dash.Dash()
# reddit_post_df = pd.read_csv('resource/topics.csv')
reddit_post_df = pd.read_csv('resource/petition_sampled.csv')

# sorted_reddit_post_df = reddit_post_df.sort_values(by=['comms_num'],ascending=False)
sorted_reddit_post_df = reddit_post_df.sort_values(by=['votes'],ascending=False)

final_reddit_post_df = sorted_reddit_post_df.head(5)
topic_words, final_reddit_topic_df = topic_extraction(sorted_reddit_post_df)
print(topic_words)
print(final_reddit_topic_df.columns)
final_reddit_topic_df.rename(columns={"start":"timestamp", "votes":"score", "category":"url"}, inplace=True)

top_post_df = final_reddit_topic_df[['title','score','url','dominanttopic','timestamp']].sort_values(by=['score'], ascending=False)

# top_post_df = top_post_df.assign(rank=[ 1+i for i in range(len(top_post_df))])[['rank'] + top_post_df.columns.tolist()]
dict_topics = create_dict_list_of_topics(final_reddit_topic_df, topic_words)

def dict_topic_list(dict_list):
    topic_list = []
    for dict in dict_list:
        topic_list.append(dict.get('value'))
        # topic_list.append(dict.get('label'))
    print(topic_list)
    return topic_list

app.layout = html.Div([
    html.H1('Dominant Topic by monthly'),

    html.Div([html.H3('Select Topics'),
              dcc.Dropdown(
                id='my-dropdown',
                options=dict_topics,
                multi=True,
                value= dict_topic_list(dict_topics)
                )
            ]
        ),

    # html.H3('Select Topics'),
    # dcc.Dropdown(
    #     id='my-dropdown',
    #     options=dict_topics,
    #     multi=True,
    #     value= dict_topic_list(dict_topics)
    # ),

    html.H3('Trending Topics'),

    # dcc.Graph(
    #     id='top_topics'
    # ),

    html.Div([
        dcc.Graph(
            id='top_topics',
        ),
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'middle'}),

    # dcc.Graph(
    #     id='top_topics_timeline'
    # ),

    html.Div([
        dcc.Graph(
            id='top_topics_timeline',
        ),
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'middle', "marginTop": 30}),

    html.H3('FAQ This Week'),

    html.Div([
        html.Table(id='my-table')]
    ),
])

colors = ['steelblue','firebrick', 'indianred', 'lightsalmon', 'darkgreen']

# For the top topics graph
@app.callback(Output('top_topics', 'figure'), [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    top_topic_filtered_df = top_post_df.copy()
    top_topic_filtered_df = top_post_filtered(top_topic_filtered_df, selected_dropdown_value)

    figure = {
        'data': [go.Bar(
            y=top_topic_filtered_df.dominant_topic_text.value_counts().index,
            x=top_topic_filtered_df.dominant_topic_text.value_counts().values,
            orientation='h',
        )],
        'layout': go.Layout(
            title= 'Trending Topics',
            yaxis = dict(
                # autorange=True,
                automargin=True
            )
        )
    }
    return figure

# For the top topics graph
@app.callback(Output('top_topics_timeline', 'figure'), [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    top_topic_filtered_df = top_post_df.copy()
    top_topic_filtered_df = top_post_filtered(top_topic_filtered_df, selected_dropdown_value)
    data = timeline_top_post_filtered(top_topic_filtered_df,selected_dropdown_value)
    # Edit the layout
    layout = dict(title='Top Topics Timeline',
                  xaxis=dict(title='Month'),
                  yaxis=dict(title='count posts'),
                  )
    figure = dict(data=data,layout=layout)
    return figure

@app.callback(Output('my-table', 'children'), [Input('my-dropdown', 'value')])
def generate_table(selected_dropdown_value,max_rows=10):
    top_post_filtered_df= top_post_df.copy()
    top_post_filtered_df= top_post_filtered(top_post_filtered_df,selected_dropdown_value)
    return [html.Tr([html.Th(col) for col in top_post_filtered_df.columns])] + [html.Tr([
        html.Td(html.A('click', href=top_post_filtered_df.iloc[i][col])) if col == 'url' else html.Td(
            top_post_filtered_df.iloc[i][col]) for col in top_post_filtered_df.columns
    ]) for i in range(min(len(top_post_filtered_df), max_rows))]

def convertTuple(tup):
    to_str = ','.join(str(tup))
    return to_str

def top_post_filtered(top_post_filtered_df,selected_dropdown_value):
    print('selected_dropdown_value', selected_dropdown_value)

    # if selected_dropdown_value is None:
    #     selected_dropdown_value = dict_topics
    top_post_filtered_df['dominant_topic_text'] = top_post_df['dominanttopic'].apply(convertTuple)
    top_post_filtered_df = top_post_filtered_df[
        (top_post_filtered_df['dominant_topic_text'].isin(selected_dropdown_value))]
    top_post_filtered_df = top_post_filtered_df.drop(columns=['dominanttopic'])
    return top_post_filtered_df

def timeline_top_post_filtered(top_topic_filtered_df, selected_dropdown_value):
    # Make a timeline
    top_topic_filtered_df['timestamp'] = top_topic_filtered_df['timestamp'].apply(lambda x: pd.to_datetime(str(x)))
    topic_time_count = top_topic_filtered_df.set_index(top_topic_filtered_df.timestamp).loc[:, 'dominant_topic_text']
    trace_list = []
    for value in selected_dropdown_value:
        topic_time_filtered_count = topic_time_count[topic_time_count == value]
        topic_day_count = topic_time_filtered_count.groupby([topic_time_filtered_count.index.month]).value_counts()
        # topic_day_count = topic_time_filtered_count.groupby([topic_time_filtered_count.index.year]).value_counts()
        topic_day_count_df = topic_day_count.unstack(level=1)
        # print(topic_day_count_df)
        trace = go.Scatter(
            y=topic_day_count_df[value],
            x=topic_day_count_df.index,
            name = value
        )
        trace_list.append(trace)
    return trace_list

if __name__ == '__main__':
    app.run_server(debug=True)
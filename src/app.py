import json
import networkx as nx
import pandas as pd
from functools import partial
from datetime import datetime as dt


from google.oauth2 import service_account
from apiclient import discovery

import dash
import dash_auth
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_daq as daq
from plotly import graph_objects as go
import dash_table
from dash_table.Format import Format, Scheme

from dash_network import Network

pd.set_option("display.precision", 2)

SAMPLE_SPREADSHEET_ID = "1qdQN9rOd4JSOV7CAZxnn7bSVpXolaL7g2GIRq0f70X0"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SAMPLE_RANGE_NAME = 'wordlist!A1:E'

VALID_USERNAME_PASSWORD_PAIRS = {
    'sophia': 'hongyi'
}

credentials = service_account.Credentials.from_service_account_file('secret.json')

service = discovery.build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()


def _sheet_load(lang):
    if lang == 'chinese':
        range_name = 'wordlist!A1:E'
    elif lang == 'english':
        range_name = 'englishlist!A1:E'

    result = sheet.values().get(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        range=range_name,
    ).execute()
    _df = pd.DataFrame(
        result['values'],
        columns=['word', 'phrase', 'sentence', 'correct', 'wrong'],
    )
    _df['correct'] = _df['correct'].astype(int)
    _df['wrong'] = _df['wrong'].astype(int)

    _df['accuracy'] = _df['correct'] / (_df['correct'] + _df['wrong'])
    _df['total'] = _df['correct'] + _df['wrong']
    _df['cell'] = _df.index + 1
    _df['accuracy'] = _df['accuracy'].fillna(0)
    return _df

def sheet_load():
    r = {}
    for lang in ['chinese', 'english']:
        r[lang] = _sheet_load(lang)
    return r

DF = sheet_load()


# build the app
app = dash.Dash(__name__)

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

navbar = dbc.NavbarSimple(
    [
        dcc.Dropdown(
	    id='lang-dropdown',
	    options=[
		{'label': '中文', 'value': 'chinese'},
		{'label': 'English', 'value': 'english'},
	    ],
	    value='chinese',
            clearable=False,
            style={'width': '100px'}
	),
    ],
    brand="HY Spelling",
    brand_href="#",
    color="dark",
    dark=True,
)


tab1_content = html.Div(
    [
       dbc.Button(id='refresh-list', children='Refresh', color='primary'),
       html.Div(id='wordlist'),
    ]

)

tab2_content = html.Div(
    [
        dbc.Button('Refresh', id='refresh_test', color="primary", className="mr-1"),
        dbc.Button('Save Result', id='save_result', color="secondary", className="mr-1"),
        dbc.Label('123', id='msg_bar', className='mr-1'),
        html.Div(
            id='test_table',
            children=[
                html.Table(
                    [
                        html.Tbody(
                            id='practice_body'
                        )
                    ]
                )
            ]
        )
    ]
)

tab3_content = html.Div(
    dbc.Form(
        [
            dbc.FormGroup(
                [
                    dbc.Label("字/Word", className="mr-2"),
                    dbc.Input(id='input-word', type="text", placeholder=""),
                ],
            ),
            dbc.FormGroup(
                [
                    dbc.Label("词/Phrase", className="mr-2"),
                    dbc.Input(id='input-phrase', type="text", placeholder=""),
                ],
            ),
            dbc.FormGroup(
                [
                    dbc.Label("句/Sentence", className="mr-2"),
                    dbc.Input(id='input-sentence', type="text", placeholder=""),
                ],
            ),
            dbc.Button(id='submit-add', children="Submit", color="primary"),
            html.Div(id='submit-status'),
        ],
    ),
    id='edit-form',
    className="col-4"
)

tab4_content = html.Div(
    [
        html.Span(id='flashcard-id', className='d-none', children='0'),
        dbc.Button('Pre', id='card-pre'),
        dbc.Label(id='flashcard-info'),
        dbc.Card(
            dbc.CardBody(
                [
                ],
                id='card',
            ),
        ),
        dbc.Button('Next', id='card-next'),
    ]
)

main_panel = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label="Word List"),
        dbc.Tab(tab2_content, label="Practice"),
        dbc.Tab(tab3_content, label="Edit"),
        dbc.Tab(tab4_content, label="Flash Card"),
    ]
)

app.layout = html.Div(
    [
        navbar,
        dbc.Row(
            [
                dbc.Col(
                    [main_panel,],
                    width={"size": 10, "offset": 0},
                )
            ],
        ), 
    ],
)

@app.callback(
    [
        Output('card', 'children'),
        Output('flashcard-id', 'children'),
        Output('flashcard-info', 'children')
    ],
    [
        Input('card-pre', 'n_clicks_timestamp'),
        Input('card-next', 'n_clicks_timestamp'),
        Input('lang-dropdown', 'value'),
    ],
    [
        State('flashcard-id', 'children')
    ]
)
def show_card(pre, nex, lang, card_id):
    df = DF.get(lang)

    ind = 0
    if pre and (not nex or (pre>nex)):
        ind = int(card_id) - 1 if (int(card_id)-1) >= 0 else 0
    if nex and (not pre or (nex>pre)):
        ind = int(card_id) + 1 if (int(card_id)+1)<len(df) else len(df)-1

    p = df.phrase[ind]
    w = df.word[ind]
    s = df.sentence[ind]
    if not s:
        s = '--'

    phrase = []
    if w:
        _ = [phrase.extend([i, html.Span(w, style={'color': 'orange'})]) for i in p.split(w)]
        phrase = phrase[:-1]
    else:
        phrase = p


    return [
        [
            html.P(phrase, style={'font-size': '64pt'}),
            html.P(s, style={'font-size': '32pt'}),
        ],
        str(ind),
        '{}/{}'.format(ind, len(df)-1)
    ]

@app.callback(
    Output('wordlist', 'children'),
    [
        Input('msg_bar', 'children'),
        Input('submit-status', 'children'),
        Input('refresh-list', 'n_clicks'),
        Input('lang-dropdown', 'value'),
    ],
)
def show_wordlist(input0, input1, input2, lang):
    global DF
    DF = sheet_load()

    df = DF.get(lang)
    t = dash_table.DataTable(
        id='word-table',
        columns=[
            {
                "name": i.capitalize(), 
                "id": i, 
                "deletable": False, 
                "selectable": True, 
                "type": "text" if i in ["word", "phrase", "sentence"] else "numeric",
                "format": Format(precision=2, scheme=Scheme.fixed),
            } for i in df.columns
        ],
        hidden_columns = ['cell'],
        data=df.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="single",
        row_selectable=False,
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size = 15,
        style_cell={
            'font-size': '16pt',
        },
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['Date', 'Region']
        ],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        }
    )
    return [t]

@app.callback(
    [
        Output('practice_body', 'children')
    ],
    [
        Input('refresh_test', 'n_clicks'),
        Input('lang-dropdown', 'value'),
    ],
)
def generate_pratice(clicked, lang):
    global DF

    children = []
    df = DF.get(lang)
    # select top 10 inaccurate phrases + 5 most infrequent tested 
    _df = df.sort_values('accuracy')
    _df1 = pd.concat([_df[:10], _df[10:].sort_values('total')[:5]])

    for i, r in _df1.iterrows():
        phrase = []
        if r.word:
            _ = [phrase.extend([i, html.Span(r.word, style={'color': 'orange'})]) for i in r.phrase.split(r.word)]
            phrase = phrase[:-1]
        else:
            phrase = r.phrase

        children.append(
            html.Tr(
                [
                    html.Td(r.cell, className='d-none'),
                    html.Td(r.word, className='mytd'),
                    html.Td(phrase, className='mytd'),
                    html.Td(r.sentence, className='mytd'),
                    html.Td(
                        [
                            dcc.RadioItems(
                                options=[
                                    {'label': 'Right', 'value': 'right'},
                                    {'label': 'Wrong', 'value': 'wrong'},
                                ],
                                value='right',
                                labelStyle={'display': 'inline-block'}
                            )
                        ],
                        className='mytd'
                    ), 
                ],
                className='mytr'
            )
        )
    return [children]


@app.callback(
    Output('msg_bar', 'children'),
    [
        Input('save_result', 'n_clicks'),
        Input('lang-dropdown', 'value'),
    ],
    [
        State('practice_body', 'children'),
    ]
)
def save_test_result(clicked, lang, tbody):
    global DF


    if clicked:
        if lang == 'chinese':
            sheet_name = 'wordlist'
        elif lang == 'english':
            sheet_name = 'englishlist'
        else:
            return 'Fail: Unknow Language Choice'

        df = DF.get(lang)
        #print(json.dumps(tbody, indent=4))
        for tr in tbody:
            c = tr['props']['children'][0]['props']['children']
            w = tr['props']['children'][1]['props']['children']
            r = tr['props']['children'][4]['props']['children'][0]['props']['value']
            row = df[df.cell == int(c)].iloc[0]
            if r == 'right':
                pos = 'D{}'.format(c)
                v = row['correct'] + 1
            else:
                pos = 'E{}'.format(c)
                v = row['wrong'] + 1
            
            result = service.spreadsheets().values().update(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range='{}!{}:{}'.format(sheet_name, pos, pos),
                valueInputOption='RAW',
                body={'values': [[str(v)]]}
            ).execute()
        return 'Success'
    else:
        return ''

@app.callback(
    Output('submit-status', 'children'),
    [
        Input('submit-add', 'n_clicks'),
        Input('lang-dropdown', 'value'),
    ],
    [
        State('edit-form', 'children')
    ]
)
def add_new_entry(input0, lang, state):
    global DF
    if input0:
        if lang == 'chinese':
            sheet_name = 'wordlist'
        elif lang == 'english':
            sheet_name = 'englishlist'
        else:
            return 'Fail: Unknow Language Choice'

        w = state['props']['children'][0]['props']['children'][1]['props'].get('value', '')
        p = state['props']['children'][1]['props']['children'][1]['props'].get('value', '')
        s = state['props']['children'][2]['props']['children'][1]['props'].get('value', '')

        df = DF.get(lang)
        if p in df.phrase.values:
            return "'{}' is already in list".format(p)

        if w or p:
            r = service.spreadsheets().values().append(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range='{}!A1:E'.format(sheet_name),
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [[w, p, s, 0, 0]]},
            ).execute()
        return [html.P('Added successfully')]
    else:
        return []

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8443)

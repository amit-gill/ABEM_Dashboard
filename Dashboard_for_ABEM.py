import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
import dash
import dash_bootstrap_components as dbc
#import dash_core_components as dcc
#import dash_html_components as html

# ----------------------
# 1. Load Multiple Files and Combine
# ----------------------
exec_dir = os.path.dirname(__file__)
input_dir = os.path.abspath(os.path.join(exec_dir, 'C:/Users/3059534/OneDrive - Queen\'s University Belfast/Documents/Research/ABEM/Exec/Output_SimResults/Industrial_Results/'))
files = [
    'Industrial_results_for_period_0.csv',
    'Industrial_results_for_period_1.csv',
    'Industrial_results_for_period_2.csv'
]  # Add all your files here

all_data = []
for i, file in enumerate(files):
    temp = pd.read_csv(input_dir + '/' + file)
    temp.columns = [c.strip() for c in temp.columns]
    temp['Period'] = i  # Assign period index
    all_data.append(temp)

df = pd.concat(all_data, ignore_index=True)

# ----------------------
# 2. Prepare Dashboard Components
# ----------------------
period_options = [{'label': f'Period {p}', 'value': p} for p in sorted(df['Period'].unique())]
industry_options = [{'label': int(i), 'value': i} for i in sorted(df['Industry ID'].unique())]


# ----------------------
# 3. Dash App Layout
# ----------------------

app = Dash(__name__)

colors = {
    'background': "#111111",
    'text': '#7FDBFF'
}



##############################
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1("Industrial Dashboard with Multiple Periods", style={
            'textAlign': 'center',
            'color': colors['text']
        }),
    html.Div([
        html.Label('Select Period:'),
        dcc.Dropdown(id='period-filter', options=period_options, value=0, clearable=False),
        html.Br(),
        #
        html.Label('Select Industry IDs to Compare:'),
        dcc.Dropdown(id='industry-filter', options=industry_options, value=0, multi=True),
        html.Br(),
        #
        html.Label('Periodic Performance of Industry:'),
        dcc.Dropdown(id='compare-industry', options=industry_options, value=0, clearable=True)
    ], style={'textAlign': 'center', 'color' : colors['text'], 'margin-bottom': '20px'}),
    dcc.Tabs([
        dcc.Tab(label='KPIs', children=[dcc.Graph(id='kpi-cards')]),
        dcc.Tab(label='Industry Analysis', children=[
            dcc.Graph(id='production-chart'),
            dcc.Graph(id='imports-chart'),
            dcc.Graph(id='treemap-chart')
        ]),
        dcc.Tab(label='Correlation', children=[dcc.Graph(id='correlation-chart')]),
        dcc.Tab(label='Industry Over Time', children=[
            dcc.Graph(id='industry-time-production'),
            dcc.Graph(id='industry-time-imports')
        ])
    ])
])


# ----------------------
# 4. Callbacks
# ----------------------
@app.callback(
    [dash.dependencies.Output('kpi-cards', 'figure'),
     dash.dependencies.Output('production-chart', 'figure'),
     dash.dependencies.Output('imports-chart', 'figure'),
     dash.dependencies.Output('treemap-chart', 'figure'),
     dash.dependencies.Output('correlation-chart', 'figure')],
    [dash.dependencies.Input('period-filter', 'value'),
     dash.dependencies.Input('industry-filter', 'value')]
)
def update_dashboard(selected_period, selected_industries):
    period_df = df[df['Period'] == selected_period]

    if selected_industries and len(selected_industries) > 0:
        filtered_df = period_df[period_df['Industry ID'].isin(selected_industries)]
    else:
        filtered_df = period_df

    # KPI Cards
    total_production = filtered_df['Total domestic production'].sum()
    total_imports = filtered_df['Imports'].sum()
    total_employment = filtered_df['Employment'].sum()

    kpi_fig = go.Figure()
    kpi_fig.add_trace(go.Indicator(mode="number", value=total_production, title="Total Domestic Production", domain={'x':[0,0.33],'y':[0.5,1]}))
    kpi_fig.add_trace(go.Indicator(mode="number", value=total_imports, title="Total Imports", domain={'x':[0.33,0.66],'y':[0.5,1]}))
    kpi_fig.add_trace(go.Indicator(mode="number", value=total_employment, title="Total Employment", domain={'x':[0.66,1],'y':[0.5,1]}))
    kpi_fig.update_layout(title_text=f"KPIs for Period {selected_period}")

    # Charts
    fig_prod = px.bar(filtered_df, x='Industry ID', y='Total domestic production', title='Total Domestic Production by Industry')
    fig_imp = px.bar(filtered_df, x='Industry ID', y='Imports', title='Imports by Industry')
    fig_tree = px.treemap(filtered_df, path=['Industry ID'], values='Total Goods for Sale', title='Total Goods for Sale by Industry')

    # Correlation Matrix
    key_vars = ['Total domestic production','Imports','Employment']
    corr_matrix = filtered_df[key_vars].corr()
    fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", title="Correlation Matrix")

    return kpi_fig, fig_prod, fig_imp, fig_tree, fig_corr

# Callback for Industry Over Time comparison
@app.callback(
    [dash.dependencies.Output('industry-time-production', 'figure'),
     dash.dependencies.Output('industry-time-imports', 'figure')],
    [dash.dependencies.Input('compare-industry', 'value')]
)
def compare_industry_over_time(selected_industry):
    if selected_industry is None:
        return go.Figure(), go.Figure()

    industry_df = df[df['Industry ID'] == selected_industry]

    fig_prod_time = px.line(industry_df, x='Period', y='Total domestic production', title=f'Production Over Time for Industry {selected_industry}')
    fig_imp_time = px.bar(industry_df, x='Period', y='Imports', title=f'Imports Over Time for Industry {selected_industry}')

    return fig_prod_time, fig_imp_time

# ----------------------
# 5. Run Server
# ----------------------
if __name__ == '__main__':
    app.run(debug=True, port=8050)
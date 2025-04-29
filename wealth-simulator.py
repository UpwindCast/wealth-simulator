import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
import io
import base64

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Wealth Simulator"

# Layout
app.layout = dbc.Container([
    html.H2("Wealth Accumulation Simulator", className="text-center my-4"),
    dbc.Tabs([
        dbc.Tab(label="Inputs", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Initial Investment ($)"),
                    dcc.Input(id="starting-balance", type="number", value=170000, className="form-control"),

                    html.Label("Monthly Contribution ($)", className="mt-2"),
                    dcc.Input(id="monthly-contribution", type="number", value=3000, className="form-control"),

                    html.Label("Annual Contribution Increase (%)", className="mt-2"),
                    dcc.Input(id="contribution-growth", type="number", value=0.0, className="form-control"),

                    html.Label("Investment Fee (%)", className="mt-2"),
                    dcc.Input(id="fee-percent", type="number", value=0.0, className="form-control"),

                    html.Label("Inflation Rate (%)", className="mt-2"),
                    dcc.Input(id="inflation-rate", type="number", value=2.5, className="form-control"),
                ], width=6),

                dbc.Col([
                    html.Label("Annual Return (%)"),
                    dcc.Dropdown([5, 6, 7, 8, 10], 7, id="annual-return", className="mb-2"),

                    html.Label("Interest Compounding Frequency"),
                    dcc.Dropdown(["Monthly", "Annually"], "Monthly", id="compound-freq", className="mb-2"),

                    html.Label("Routine Withdrawal ($)"),
                    dcc.Input(id="routine-withdrawal", type="number", value=0, className="form-control"),

                    html.Label("Withdrawal Frequency", className="mt-2"),
                    dcc.Dropdown(["None", "Monthly", "Annually"], "None", id="routine-freq", className="mb-2"),

                    html.Label("Portfolio Goal ($)"),
                    dcc.Input(id="target-value", type="number", value=2000000, className="form-control"),
                ], width=6)
            ]),

            html.Hr(),

            dbc.Row([
                dbc.Col([
                    html.Label("Projection End Date"),
                    dcc.DatePickerSingle(id="end-date", date=date.today().replace(year=date.today().year + 20)),

                    html.Label("Contribution Start Date", className="mt-2"),
                    dcc.DatePickerSingle(id="contrib-start", date=date.today()),

                    html.Label("Contribution End Date", className="mt-2"),
                    dcc.DatePickerSingle(id="contrib-end", date=date.today().replace(year=date.today().year + 20)),
                ], width=6),

                dbc.Col([
                    html.Label("Withdrawal Start Date"),
                    dcc.DatePickerSingle(id="wd-start", date=date.today()),

                    html.Label("Withdrawal End Date", className="mt-2"),
                    dcc.DatePickerSingle(id="wd-end", date=date.today().replace(year=date.today().year + 20)),

                    html.Label("One-Time Withdrawals (YYYY-MM-DD: amount, ...)", className="mt-2"),
                    dcc.Input(id="custom-withdrawals", type="text", className="form-control", 
                              placeholder="2026-01-01: 5000, 2029-07-01: 20000")
                ], width=6)
            ]),

            html.Div([
                dbc.Button("Generate Report", id="run-button", color="primary", className="mt-4")
            ], className="text-center")
        ]),

        dbc.Tab(label="Charts", children=[
            dcc.Loading([
                dcc.Graph(id="portfolio-graph"),
                dcc.Graph(id="contrib-vs-growth")
            ])
        ]),

        dbc.Tab(label="Summary", children=[
            html.Div(id="summary-output", className="p-4")
        ]),

        dbc.Tab(label="Download", children=[
            html.Div(id="download-link", className="p-4")
        ])
    ])
], fluid=True)

# Callback
@app.callback(
    [Output("portfolio-graph", "figure"),
     Output("contrib-vs-growth", "figure"),
     Output("summary-output", "children"),
     Output("download-link", "children")],
    Input("run-button", "n_clicks"),
    [State("starting-balance", "value"),
     State("monthly-contribution", "value"),
     State("contribution-growth", "value"),
     State("fee-percent", "value"),
     State("inflation-rate", "value"),
     State("annual-return", "value"),
     State("compound-freq", "value"),
     State("routine-withdrawal", "value"),
     State("routine-freq", "value"),
     State("target-value", "value"),
     State("end-date", "date"),
     State("contrib-start", "date"),
     State("contrib-end", "date"),
     State("wd-start", "date"),
     State("wd-end", "date"),
     State("custom-withdrawals", "value")]
)
def update_dashboard(n_clicks, starting_balance, monthly_contribution, contribution_growth, fee_percent, inflation_rate,
                     annual_return, compound_freq, routine_withdrawal, routine_freq, target_value, end_date,
                     contrib_start, contrib_end, wd_start, wd_end, custom_withdrawals):
    if not n_clicks:
        return dash.no_update

    start_date = date.today()
    end_date = pd.to_datetime(end_date).date()
    contrib_start = pd.to_datetime(contrib_start).date()
    contrib_end = pd.to_datetime(contrib_end).date()
    wd_start = pd.to_datetime(wd_start).date()
    wd_end = pd.to_datetime(wd_end).date()

    try:
        withdrawals_dict = {}
        if custom_withdrawals:
            for item in custom_withdrawals.split(","):
                dt, amt = item.strip().split(":")
                withdrawals_dict[pd.to_datetime(dt.strip())] = float(amt)
    except:
        withdrawals_dict = {}

    dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    balance = starting_balance
    balances, real_balances = [], []
    contributions, withdrawals, routine_wds, cumulative_contributions = [], [], [], []
    monthly_rate = (annual_return / 100) / (12 if compound_freq == "Monthly" else 1)
    fee_rate = (fee_percent / 100) / (12 if compound_freq == "Monthly" else 1)
    monthly_inflation = (inflation_rate / 100) / 12
    compounding_months = [i for i, dt in enumerate(dates) if (compound_freq == "Monthly" or dt.month == 1)]

    total_contributed = 0
    target_reached = False
    milestone = None

    for i, dt in enumerate(dates):
        if i in compounding_months:
            balance *= (1 + monthly_rate - fee_rate)

        if contrib_start <= dt.date() <= contrib_end:
            if i > 0 and dt.month == 1:
                monthly_contribution *= (1 + contribution_growth / 100)
            balance += monthly_contribution
            total_contributed += monthly_contribution
            contributions.append(monthly_contribution)
        else:
            contributions.append(0)

        wd = 0
        if wd_start <= dt.date() <= wd_end:
            if routine_freq == "Monthly":
                wd = routine_withdrawal
            elif routine_freq == "Annually" and dt.month == 1:
                wd = routine_withdrawal
        balance -= wd
        routine_wds.append(wd)

        custom_wd = withdrawals_dict.get(dt, 0)
        balance -= custom_wd
        withdrawals.append(custom_wd)

        real_balance = balance / ((1 + monthly_inflation) ** i)
        balances.append(balance)
        real_balances.append(real_balance)
        cumulative_contributions.append(total_contributed)

        if not target_reached and balance >= target_value:
            milestone = f"Target of ${target_value:,.0f} reached on {dt.strftime('%m/%d/%Y')}"
            target_reached = True

    # Portfolio graph
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dates, y=balances, name="Nominal Portfolio Value"))
    fig1.add_trace(go.Scatter(x=dates, y=real_balances, name="Inflation-Adjusted Value"))
    fig1.update_layout(title="Portfolio Value Over Time", xaxis_title="Date", yaxis_title="Value ($)", template="plotly_white")

    # Contributions vs Portfolio
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dates, y=cumulative_contributions, name="Cumulative Contributions"))
    fig2.add_trace(go.Scatter(x=dates, y=balances, name="Portfolio Value"))
    fig2.update_layout(title="Contributions vs Portfolio Value", xaxis_title="Date", yaxis_title="Value ($)", template="plotly_white")

    # Summary
    summary = [
        html.H5("📄 Simulation Summary"),
        html.Ul([
            html.Li(f"Final Balance: ${balances[-1]:,.2f}"),
            html.Li(f"Inflation-Adjusted Balance: ${real_balances[-1]:,.2f}"),
            html.Li(f"Total Contributions: ${total_contributed:,.2f}"),
            html.Li(f"Annual Return: {annual_return}%"),
            html.Li(f"Investment Fee: {fee_percent}%"),
            html.Li(f"Inflation Rate: {inflation_rate}%")
        ])
    ]
    if milestone:
        summary.append(html.Div(f"🎯 {milestone}", className="alert alert-success mt-3"))

    # Download CSV
    df = pd.DataFrame({
        "Date": dates.strftime('%m/%d/%Y'),
        "Portfolio Value": balances,
        "Real Value": real_balances,
        "Contribution": contributions,
        "Routine Withdrawal": routine_wds,
        "Custom Withdrawal": withdrawals,
        "Cumulative Contributions": cumulative_contributions
    })
    csv_string = df.to_csv(index=False)
    b64 = base64.b64encode(csv_string.encode()).decode()
    href = f'data:text/csv;base64,{b64}'
    download_link = html.A("📥 Download Projection as CSV", href=href, download="wealth_projection.csv", className="btn btn-outline-primary")

    return fig1, fig2, summary, download_link

if __name__ == '__main__':
    app.run(debug=True)


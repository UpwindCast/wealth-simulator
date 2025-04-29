
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("📈 Wealth Accumulation Simulator")

starting_balance = st.number_input("Initial Investment ($)", value=170000)
monthly_contribution = st.number_input("Monthly Contribution ($)", value=3000)
annual_return = st.selectbox("Annual Return Rate (%)", [5, 6, 7, 8, 10], index=2)
years = st.slider("Time Horizon (Years)", 5, 40, 20)

months = years * 12
monthly_rate = annual_return / 100 / 12
balance = starting_balance
balances = []

for _ in range(months):
    balance = balance * (1 + monthly_rate) + monthly_contribution
    balances.append(balance)

dates = pd.date_range(start="2025-01-01", periods=months, freq="M")

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=balances, mode='lines', name="Portfolio Value", line=dict(width=3)))

fig.update_layout(
    title=f"Wealth Growth Over {years} Years",
    xaxis_title="Date",
    yaxis_title="Value ($)",
    yaxis_tickprefix="$",
    template="plotly_white"
)

st.plotly_chart(fig)

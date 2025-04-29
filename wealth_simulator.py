import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Streamlit App Title ---
st.title("📈 Wealth Accumulation Simulator")

# --- Input Form ---
with st.form("wealth_form"):
    st.subheader("🧮 Enter Your Simulation Inputs")

    starting_balance = st.number_input("Initial Investment ($)", value=170000)
    monthly_contribution = st.number_input("Monthly Contribution ($)", value=3000)
    annual_return = st.selectbox("Expected Annual Return (%)", [5, 6, 7, 8, 10], index=2)
    contribution_growth = st.number_input("Annual Contribution Increase (%)", value=0.0)
    fee_percent = st.number_input("Annual Investment Fee (%)", value=0.0)
    years = st.slider("Time Horizon (Years)", 5, 40, 20)

    submitted = st.form_submit_button("📤 Generate Report")

# --- Run Simulation After Submit ---
if submitted:
    months = years * 12
    monthly_rate = (annual_return / 100) / 12
    fee_rate = (fee_percent / 100) / 12
    balance = starting_balance
    balances = []
    contributions = []

    for month in range(months):
        if month > 0 and month % 12 == 0:
            monthly_contribution *= (1 + contribution_growth / 100)

        balance = balance * (1 + monthly_rate - fee_rate) + monthly_contribution
        balances.append(balance)
        contributions.append(monthly_contribution)

    dates = pd.date_range(start="2025-01-01", periods=months, freq="M")

    # --- Plotly Line Chart ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=balances, mode='lines', name="Portfolio Value", line=dict(width=3)))

    fig.update_layout(
        title=f"Wealth Growth Over {years} Years",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        yaxis_tickprefix="$",
        template="plotly_white"
    )

    st.subheader("📊 Portfolio Value Over Time")
    st.plotly_chart(fig)

    # --- Summary Table ---
    summary = {
        "Starting Balance ($)": [starting_balance],
        "Final Balance ($)": [round(balances[-1], 2)],
        "Monthly Contribution ($)": [round(contributions[0], 2)],
        "Annual Return (%)": [annual_return],
        "Contribution Growth (%)": [contribution_growth],
        "Investment Fee (%)": [fee_percent],
        "Time Horizon (Years)": [years]
    }

    st.subheader("📄 Simulation Summary")
    st.table(pd.DataFrame(summary))

    # --- Downloadable CSV ---
    df = pd.DataFrame({
        "Date": dates,
        "Portfolio Value ($)": balances,
        "Monthly Contribution ($)": contributions
    })

    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Monthly Projections as CSV",
        data=csv,
        file_name='wealth_projection.csv',
        mime='text/csv',
    )

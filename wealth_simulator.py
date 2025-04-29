import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# Title
st.title("📈 Wealth Accumulation Simulator")

# --- Input Form ---
with st.form("wealth_form"):
    st.subheader("🧮 Simulation Inputs")

    # Basic inputs
    starting_balance = st.number_input("Initial Investment ($)", value=170000)
    monthly_contribution = st.number_input("Monthly Contribution ($)", value=3000)
    annual_return = st.selectbox("Expected Annual Return (%)", [5, 6, 7, 8, 10], index=2)
    contribution_growth = st.number_input("Annual Contribution Increase (%)", value=0.0)
    fee_percent = st.number_input("Annual Investment Fee (%)", value=0.0)

    # Dates
    start_date = date.today()
    end_date = st.date_input("Projection End Date", value=date(start_date.year + 20, start_date.month, start_date.day))

    # Compounding frequency
    compound_freq = st.selectbox("Interest Compounding Frequency", ["Monthly", "Annually"])

    # Routine withdrawals
    routine_withdrawal = st.number_input("Routine Withdrawal Amount ($)", value=0.0)
    routine_freq = st.selectbox("Routine Withdrawal Frequency", ["None", "Monthly", "Annually"])

    # Custom withdrawals
    withdrawals_input = st.text_input("One-Time Withdrawals (format: YYYY-MM-DD: amount, ...)", value="")

    submitted = st.form_submit_button("📤 Generate Report")

# --- Run Simulation ---
if submitted:
    # Parse custom withdrawals
    custom_withdrawals = {}
    if withdrawals_input:
        try:
            for item in withdrawals_input.split(","):
                date_str, amt = item.strip().split(":")
                custom_withdrawals[pd.to_datetime(date_str.strip())] = float(amt)
        except:
            st.error("❗ Check your custom withdrawals format. Example: 2026-01-01: 5000, 2029-07-01: 20000")

    # Setup
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')  # Monthly start of month
    balance = starting_balance
    balances = []
    contributions = []
    withdrawals = []
    routine_wds = []

    # Determine compounding
    if compound_freq == "Monthly":
        compounding_months = [i for i in range(len(dates))]
        rate_periods = 12
    elif compound_freq == "Annually":
        compounding_months = [i for i, dt in enumerate(dates) if dt.month == 1]
        rate_periods = 1

    monthly_rate = (annual_return / 100) / rate_periods
    fee_rate = (fee_percent / 100) / rate_periods

    for i, dt in enumerate(dates):
        # Apply interest
        if i in compounding_months:
            balance *= (1 + monthly_rate - fee_rate)

        # Apply contribution (with growth every Jan)
        if i > 0 and dt.month == 1:
            monthly_contribution *= (1 + contribution_growth / 100)
        balance += monthly_contribution

        # Apply routine withdrawal
        wd = 0
        if routine_freq == "Monthly":
            wd = routine_withdrawal
        elif routine_freq == "Annually" and dt.month == 1:
            wd = routine_withdrawal
        balance -= wd
        routine_wds.append(wd)

        # Apply custom withdrawal
        custom_wd = custom_withdrawals.get(dt, 0)
        balance -= custom_wd
        withdrawals.append(custom_wd)

        balances.append(balance)
        contributions.append(monthly_contribution)

    # --- Plotly Chart ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=balances, mode='lines', name="Portfolio Value", line=dict(width=3)))
    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        yaxis_tickprefix="$",
        template="plotly_white"
    )
    st.subheader("📊 Portfolio Projection")
    st.plotly_chart(fig)

    # --- Summary Table ---
    summary = {
        "Start Date": [start_date],
        "End Date": [end_date],
        "Final Balance ($)": [round(balances[-1], 2)],
        "Starting Contribution ($)": [round(contributions[0], 2)],
        "Annual Return (%)": [annual_return],
        "Contribution Growth (%)": [contribution_growth],
        "Investment Fee (%)": [fee_percent],
        "Routine Withdrawal ($)": [routine_withdrawal],
        "Compounding": [compound_freq]
    }

    st.subheader("📄 Summary")
    st.table(pd.DataFrame(summary))

    # --- Download CSV ---
    df = pd.DataFrame({
        "Date": dates,
        "Portfolio Value ($)": balances,
        "Contribution ($)": contributions,
        "Routine Withdrawal ($)": routine_wds,
        "Custom Withdrawal ($)": withdrawals
    })

    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Projection as CSV",
        data=csv,
        file_name='wealth_projection.csv',
        mime='text/csv',
    )

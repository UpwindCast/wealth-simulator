import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# Title
st.title("📈 Wealth Accumulation Simulator")

# --- Tabs Layout ---
tabs = st.tabs(["Inputs", "Charts", "Summary", "Download"])

# --- Input Form ---
with tabs[0]:
    with st.form("wealth_form"):
        st.subheader("🧮 Simulation Inputs")

        # Layout Columns
        col1, col2 = st.columns(2)
        with col1:
            starting_balance = st.number_input("Initial Investment ($)", value=170000)
            monthly_contribution = st.number_input("Monthly Contribution ($)", value=3000)
            contribution_growth = st.number_input("Annual Contribution Increase (%)", value=0.0)
            fee_percent = st.number_input("Annual Investment Fee (%)", value=0.0)
            inflation_rate = st.number_input("Inflation Rate (%)", value=2.5)

        with col2:
            annual_return = st.selectbox("Expected Annual Return (%)", [5, 6, 7, 8, 10], index=2)
            compound_freq = st.selectbox("Interest Compounding Frequency", ["Monthly", "Annually"])
            routine_withdrawal = st.number_input("Routine Withdrawal Amount ($)", value=0.0)
            routine_freq = st.selectbox("Routine Withdrawal Frequency", ["None", "Monthly", "Annually"])
            target_value = st.number_input("Target Portfolio Goal ($)", value=2000000)

        col3, col4 = st.columns(2)
        with col3:
            start_date = date.today()
            end_date = st.date_input("Projection End Date", value=date(start_date.year + 20, start_date.month, start_date.day))
            contribution_start_date = st.date_input("Contribution Start Date", value=start_date)
            contribution_end_date = st.date_input("Contribution End Date", value=end_date)

        with col4:
            withdrawals_input = st.text_input("One-Time Withdrawals (YYYY-MM-DD: amount, ...)", value="")
            withdrawal_start_date = st.date_input("Withdrawal Start Date", value=start_date)
            withdrawal_end_date = st.date_input("Withdrawal End Date", value=end_date)

        dark_mode = st.checkbox("🌙 Dark Mode")
        submitted = st.form_submit_button("📤 Generate Report")

# --- Run Simulation ---
if submitted:
    with st.spinner('Calculating projections...'):
        custom_withdrawals = {}
        if withdrawals_input:
            try:
                for item in withdrawals_input.split(","):
                    date_str, amt = item.strip().split(":")
                    custom_withdrawals[pd.to_datetime(date_str.strip())] = float(amt)
            except:
                st.error("❗ Check your custom withdrawals format. Example: 2026-01-01: 5000, 2029-07-01: 20000")

        dates = pd.date_range(start=start_date, end=end_date, freq='MS')
        balance = starting_balance
        balances = []
        contributions = []
        withdrawals = []
        routine_wds = []
        real_balances = []
        milestones = []
        cumulative_contributions = []
        total_contributed = 0

        if compound_freq == "Monthly":
            compounding_months = [i for i in range(len(dates))]
            rate_periods = 12
        elif compound_freq == "Annually":
            compounding_months = [i for i, dt in enumerate(dates) if dt.month == 1]
            rate_periods = 1

        monthly_rate = (annual_return / 100) / rate_periods
        fee_rate = (fee_percent / 100) / rate_periods
        monthly_inflation = (inflation_rate / 100) / 12

        target_reached = False

        for i, dt in enumerate(dates):
            if i in compounding_months:
                balance *= (1 + monthly_rate - fee_rate)

            if contribution_start_date <= dt.date() <= contribution_end_date:
                if i > 0 and dt.month == 1:
                    monthly_contribution *= (1 + contribution_growth / 100)
                balance += monthly_contribution
                total_contributed += monthly_contribution
                contributions.append(monthly_contribution)
            else:
                contributions.append(0)

            wd = 0
            if withdrawal_start_date <= dt.date() <= withdrawal_end_date:
                if routine_freq == "Monthly":
                    wd = routine_withdrawal
                elif routine_freq == "Annually" and dt.month == 1:
                    wd = routine_withdrawal
            balance -= wd
            routine_wds.append(wd)

            custom_wd = custom_withdrawals.get(dt, 0)
            balance -= custom_wd
            withdrawals.append(custom_wd)

            real_balance = balance / ((1 + monthly_inflation) ** i)

            balances.append(balance)
            real_balances.append(real_balance)
            cumulative_contributions.append(total_contributed)

            if not target_reached and balance >= target_value:
                milestones.append((dt.strftime('%m/%d/%Y'), round(balance, 2)))
                target_reached = True

    theme = 'plotly_dark' if dark_mode else 'plotly_white'

    with tabs[1]:
        st.subheader("📊 Portfolio Projection")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[d.strftime('%m/%d/%Y') for d in dates], y=balances, mode='lines', name="Nominal Portfolio Value"))
        fig.add_trace(go.Scatter(x=[d.strftime('%m/%d/%Y') for d in dates], y=real_balances, mode='lines', name="Inflation-Adjusted Value"))
        fig.update_layout(title="Portfolio Value Over Time", xaxis_title="Date", yaxis_title="Value ($)", yaxis_tickprefix="$", template=theme)
        st.plotly_chart(fig)

        st.subheader("📊 Contributions vs Portfolio Value")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=[d.strftime('%m/%d/%Y') for d in dates], y=cumulative_contributions, mode='lines', name="Cumulative Contributions"))
        fig2.add_trace(go.Scatter(x=[d.strftime('%m/%d/%Y') for d in dates], y=balances, mode='lines', name="Portfolio Value"))
        fig2.update_layout(title="Contributions vs Portfolio Value", xaxis_title="Date", yaxis_title="Value ($)", yaxis_tickprefix="$", template=theme)
        st.plotly_chart(fig2)

    with tabs[2]:
        st.subheader("📄 Summary")
        summary = {
            "Start Date": [start_date.strftime('%m/%d/%Y')],
            "End Date": [end_date.strftime('%m/%d/%Y')],
            "Final Balance ($)": [round(balances[-1], 2)],
            "Final Real Balance ($)": [round(real_balances[-1], 2)],
            "Total Contributions ($)": [round(total_contributed, 2)],
            "Annual Return (%)": [annual_return],
            "Contribution Growth (%)": [contribution_growth],
            "Investment Fee (%)": [fee_percent],
            "Inflation Rate (%)": [inflation_rate],
            "Routine Withdrawal ($)": [routine_withdrawal],
            "Compounding": [compound_freq]
        }
        st.table(pd.DataFrame(summary))

        if milestones:
            st.success(f"🎯 Target of ${target_value:,.0f} reached on {milestones[0][0]} with a balance of ${milestones[0][1]:,.2f}")

        st.metric(label="Final Portfolio Value", value=f"${balances[-1]:,.0f}")
        st.metric(label="Total Contributions", value=f"${total_contributed:,.0f}")

    with tabs[3]:
        df = pd.DataFrame({
            "Date": [d.strftime('%m/%d/%Y') for d in dates],
            "Portfolio Value ($)": balances,
            "Inflation-Adjusted Value ($)": real_balances,
            "Contribution ($)": contributions,
            "Cumulative Contributions ($)": cumulative_contributions,
            "Routine Withdrawal ($)": routine_wds,
            "Custom Withdrawal ($)": withdrawals
        })
        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(label="📥 Download Projection as CSV", data=csv, file_name='wealth_projection.csv', mime='text/csv')

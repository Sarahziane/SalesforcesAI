import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    visits_df = pd.read_excel("exp01_calls_efkfr_20250505.xlsx", sheet_name="Visits")
    visits_df = visits_df[visits_df['Pharmacies'].notnull()].copy()
    visits_df['Visit Date'] = pd.to_datetime(visits_df['Visit Date'])
    visits_df['quarter'] = visits_df['Visit Date'].dt.to_period('Q')
    visits_df['month'] = visits_df['Visit Date'].dt.to_period('M')
    visits_df['has_order'] = visits_df['Activity Type'].str.contains('Commande', case=False, na=False)
    return visits_df

visits_df = load_data()

st.title("📈 Pharma Sales Intelligence Dashboard")

# Sidebar for territory selection
territories = visits_df['Territory Code'].unique()
selected_territory = st.sidebar.selectbox("Select Territory", sorted(territories))
territory_df = visits_df[visits_df['Territory Code'] == selected_territory]

st.header(f"Territory: {selected_territory}")

# --- 1. Territory Optimization ---
st.subheader("1️⃣ Territory Optimization")
territory_summary = visits_df.groupby('Territory Code').agg(
    total_visits=('Visit Date', 'count'),
    unique_reps=('Rep', pd.Series.nunique)
).reset_index()
territory_summary['visits_per_rep'] = (territory_summary['total_visits'] / territory_summary['unique_reps']).round(2)
st.dataframe(territory_summary.sort_values(by='visits_per_rep', ascending=False))

# --- 2. Account Segmentation ---
st.subheader("2️⃣ Account Segmentation")
segmentation = territory_df.groupby('Pharmacies').agg(
    total_visits=('Visit Date', 'count'),
    unique_activity_types=('Activity Type', pd.Series.nunique),
    first_visit=('Visit Date', 'min'),
    last_visit=('Visit Date', 'max')
).reset_index()
segmentation['engagement_duration'] = (segmentation['last_visit'] - segmentation['first_visit']).dt.days
segmentation['score'] = segmentation['total_visits']*0.6 + segmentation['unique_activity_types']*20 + segmentation['engagement_duration']*0.2
segmentation['tier'] = pd.qcut(segmentation['score'], q=3, labels=['Low', 'Medium', 'High'], duplicates='drop')
st.dataframe(segmentation.sort_values(by='score', ascending=False))

# --- 3. Sales Forecasting ---
st.subheader("3️⃣ Sales Forecasting")
quarter_data = territory_df.groupby(['Pharmacies', 'quarter']).agg(
    total_visits=('Visit Date', 'count'),
    order_visits=('has_order', 'sum'),
    unique_activities=('Activity Type', pd.Series.nunique),
    last_visit=('Visit Date', 'max')
).reset_index()
quarter_data['order_rate'] = (quarter_data['order_visits'] / quarter_data['total_visits']).round(2)
latest_q = quarter_data['quarter'].max()
historical = quarter_data[quarter_data['quarter'] < latest_q]
recent = quarter_data[quarter_data['quarter'] == latest_q]
historical_avg = historical.groupby('Pharmacies').agg(
    avg_order_rate=('order_rate', 'mean')
).reset_index()
prediction = recent.merge(historical_avg, on='Pharmacies', how='left')
prediction['likely_to_order'] = prediction['avg_order_rate'] > 0.3
st.dataframe(prediction[['Pharmacies', 'order_rate', 'avg_order_rate', 'likely_to_order']])

# --- 4. Rep & Pharmacy Monthly Insights ---
st.subheader("4️⃣ Rep & Pharmacy Monthly Insights")
monthly_summary = territory_df.groupby(['month', 'Activity Type']).agg(visits=('Visit Date', 'count')).reset_index()
st.markdown("**Monthly Visits by Activity Type:**")
st.dataframe(monthly_summary)

rep_productivity = territory_df.groupby(['month', 'Rep']).agg(
    total_visits=('Visit Date', 'count'),
    order_visits=('has_order', 'sum')
).reset_index()
st.markdown("**Rep Productivity:**")
st.dataframe(rep_productivity)

pharmacy_trend = territory_df.groupby(['month', 'Pharmacies']).agg(
    pharmacy_visits=('Visit Date', 'count'),
    activity_types=('Activity Type', pd.Series.nunique)
).reset_index()
st.markdown("**Pharmacy Engagement Trend:**")
st.dataframe(pharmacy_trend)

st.success("Dashboard generated for Territory: " + selected_territory)

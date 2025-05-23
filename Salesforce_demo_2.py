import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    visits = pd.read_excel("exp01_calls_efkfr_20250505.xlsx", sheet_name='Visits')
    visits['Visit Date'] = pd.to_datetime(visits['Visit Date'])
    visits['month'] = visits['Visit Date'].dt.to_period('M')
    visits['quarter'] = visits['Visit Date'].dt.to_period('Q')
    visits['has_order'] = visits['Activity Type'].str.contains('Commande', case=False, na=False)
    return visits

df = load_data()

# Sidebar navigation
section = st.sidebar.radio("Dashboard Section", [
    "Territory Optimization",
    "Account Segmentation",
    "Sales Forecasting",
    "Rep & Pharmacy Insights"
])

st.title("📊 Pharma Field Activity Dashboard")

# SECTION 1: TERRITORY OPTIMIZATION
if section == "Territory Optimization":
    st.header("📍 Territory Optimization")
    territory_stats = df.groupby('Territory Code').agg(
        total_visits=('Visit Date', 'count'),
        unique_reps=('Rep', pd.Series.nunique)
    ).reset_index()
    territory_stats['visits_per_rep'] = territory_stats['total_visits'] / territory_stats['unique_reps']
    fig = px.bar(territory_stats.sort_values("visits_per_rep", ascending=False), 
                 x='Territory Code', y='visits_per_rep',
                 color='visits_per_rep', title="Visits per Rep by Territory")
    st.plotly_chart(fig)
    st.dataframe(territory_stats)

# SECTION 2: ACCOUNT SEGMENTATION
elif section == "Account Segmentation":
    st.header("🏪 Pharmacy Engagement Segmentation")
    pharm_df = df[df['Pharmacies'].notnull()].copy()
    grouped = pharm_df.groupby('Pharmacies').agg(
        total_visits=('Visit Date', 'count'),
        unique_activities=('Activity Type', pd.Series.nunique),
        first_visit=('Visit Date', 'min'),
        last_visit=('Visit Date', 'max')
    ).reset_index()
    grouped['duration'] = (grouped['last_visit'] - grouped['first_visit']).dt.days
    grouped['score'] = grouped['total_visits'] * 0.6 + grouped['unique_activities'] * 20 + grouped['duration'] * 0.2
    labels = ['Low', 'Medium', 'High']
    grouped['engagement_tier'] = pd.qcut(grouped['score'], q=3, labels=labels, duplicates='drop')
    fig = px.histogram(grouped, x='score', color='engagement_tier', nbins=30,
                       title="Pharmacy Engagement Score Distribution")
    st.plotly_chart(fig)
    st.dataframe(grouped)

# SECTION 3: SALES FORECASTING
elif section == "Sales Forecasting":
    st.header("📦 Sales Forecasting - Likely Orders")
    pharm_df = df[df['Pharmacies'].notnull()].copy()
    agg = pharm_df.groupby(['Pharmacies', 'quarter']).agg(
        visits=('Visit Date', 'count'),
        order_visits=('has_order', 'sum')
    ).reset_index()
    agg['order_rate'] = agg['order_visits'] / agg['visits']
    latest_q = agg['quarter'].max()
    hist = agg[agg['quarter'] < latest_q].groupby('Pharmacies').agg(
        avg_order_rate=('order_rate', 'mean'),
        total_orders=('order_visits', 'sum')
    ).reset_index()
    latest = agg[agg['quarter'] == latest_q]
    forecast = latest.merge(hist, on='Pharmacies', how='left')
    forecast['predicted_order'] = forecast['avg_order_rate'] > 0.3
    st.metric("✅ Pharmacies Likely to Order", int(forecast['predicted_order'].sum()))
    st.dataframe(forecast[['Pharmacies', 'quarter', 'order_rate', 'avg_order_rate', 'predicted_order']])

# SECTION 4: REP & PHARMACY INSIGHTS
elif section == "Rep & Pharmacy Insights":
    st.header("👥 Rep and Pharmacy Insights")
    territory_filter = st.selectbox("Select a Territory", df['Territory Code'].unique())
    filtered = df[df['Territory Code'] == territory_filter]

    st.subheader("Rep Productivity")
    rep_prod = filtered.groupby(['month', 'Rep']).agg(
        visits=('Visit Date', 'count'),
        order_visits=('has_order', 'sum')
    ).reset_index()
    fig1 = px.bar(rep_prod, x='month', y='visits', color='Rep', barmode='group',
                  title="Monthly Visits per Rep")
    st.plotly_chart(fig1)
    st.dataframe(rep_prod)

    st.subheader("Pharmacy Engagement")
    pharm_engage = filtered[filtered['Pharmacies'].notnull()].groupby(['month', 'Pharmacies']).agg(
        visits=('Visit Date', 'count'),
        unique_activities=('Activity Type', pd.Series.nunique)
    ).reset_index()
    fig2 = px.bar(pharm_engage, x='month', y='visits', color='Pharmacies',
                  title="Monthly Visits per Pharmacy", height=500)
    st.plotly_chart(fig2)
    st.dataframe(pharm_engage)


import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load data
@st.cache_data
def load_data():
    visits_df = pd.read_excel("exp01_calls_efkfr_20250505.xlsx", sheet_name="Visits")
    visits_df = visits_df[visits_df['Pharmacies'].notna()]
    return visits_df

visits_df = load_data()

st.title("Pharmacy Sales Force Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
territories = sorted(visits_df["Territory Code"].dropna().unique())
selected_territories = st.sidebar.multiselect("Select Territories", territories, default=territories)

filtered_df = visits_df[visits_df["Territory Code"].isin(selected_territories)]

# Territory Heatmap (Bar)
st.header("📍 Pharmacy Visit Density by Territory")
territory_visits = filtered_df.groupby("Territory Code").size().reset_index(name="Visit Count")
avg_visits = territory_visits["Visit Count"].mean()
territory_visits["Coverage Status"] = territory_visits["Visit Count"].apply(lambda x: "Under-covered" if x < avg_visits else "Well-covered")
territory_visits = territory_visits.sort_values("Visit Count", ascending=False)

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=territory_visits, x="Visit Count", y="Territory Code", hue="Coverage Status", dodge=False, palette={"Under-covered": "salmon", "Well-covered": "seagreen"})
plt.axvline(avg_visits, color='gray', linestyle='--', label='Average')
plt.title("Pharmacy Visit Density by Territory")
plt.tight_layout()
st.pyplot(fig)

# Top & Low Engagement Pharmacies
st.header("🏪 High- and Low-Engagement Pharmacies")
pharmacy_counts = filtered_df.groupby('Pharmacies').agg({'Visit Date': 'count', 'Territory Code': 'first'}).reset_index()
pharmacy_counts.columns = ['Pharmacy', 'Visit Count', 'Territory Code']
top_pharmacies = pharmacy_counts.sort_values(by='Visit Count', ascending=False).head(10)

territory_density = filtered_df.groupby('Territory Code')['Pharmacies'].nunique().reset_index(name='Pharmacy Count')
high_density_territories = territory_density[territory_density['Pharmacy Count'] > territory_density['Pharmacy Count'].mean()]['Territory Code']
low_visit_threshold = pharmacy_counts['Visit Count'].quantile(0.25)
low_engaged = pharmacy_counts[(pharmacy_counts['Territory Code'].isin(high_density_territories)) & (pharmacy_counts['Visit Count'] <= low_visit_threshold)]

st.subheader("⭐ Top 10 Engaged Pharmacies")
st.dataframe(top_pharmacies)

st.subheader("✅ Priority Pharmacies in High-Density Areas")
st.dataframe(low_engaged)

# Rep Efficiency
st.header("👤 Rep Performance & Efficiency")
rep_data = filtered_df.groupby('Rep').agg(Total_Visits=('Visit Date', 'count'), Unique_Pharmacies=('Pharmacies', pd.Series.nunique), Territories=('Territory Code', pd.Series.nunique)).reset_index()
rep_data['Visits_per_Pharmacy'] = rep_data['Total_Visits'] / rep_data['Unique_Pharmacies']
overload_thresh = rep_data['Total_Visits'].quantile(0.90)
underperf_thresh = rep_data['Visits_per_Pharmacy'].quantile(0.25)
rep_data['Status'] = 'Normal'
rep_data.loc[rep_data['Total_Visits'] >= overload_thresh, 'Status'] = '⚠️ Overloaded'
rep_data.loc[rep_data['Visits_per_Pharmacy'] <= underperf_thresh, 'Status'] = '⬇️ Underperforming'
rep_data.loc[(rep_data['Total_Visits'] >= overload_thresh) & (rep_data['Visits_per_Pharmacy'] <= underperf_thresh), 'Status'] = '🔴 Critical'
st.dataframe(rep_data)

# Deployment Recommendation
st.header("🚀 Rep Deployment Suggestion")
suggested_zones = ['K105', 'K406']
st.markdown("Based on readiness scoring, we recommend allocating new reps to:")
st.write(suggested_zones)
priority_zones = pharmacy_counts[pharmacy_counts['Territory Code'].isin(suggested_zones)]
priority_summary = priority_zones.groupby('Territory Code').size().reset_index(name='Low Engagement Pharmacies')
st.dataframe(priority_summary)

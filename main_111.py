
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# === GOOGLE SHEETS SETUP ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/content/dashboard1-463207-1a30e1730fbc.json", scope)
client = gspread.authorize(creds)
sheet = client.open("meta_data_fetching").worksheet("Final_Meta_Dashboard_Data")
data = pd.DataFrame(sheet.get_all_records())

# === STREAMLIT SETUP ===
st.set_page_config(page_title="Meta Ads Dashboard", layout="wide")
st.title("Meta Ads Real-Time & Historical Dashboard")

# Sidebar
view_type = st.sidebar.radio("Select View Type:", ["Real Time Dashboard", "Historical Data Dashboard"])

# Convert date column to datetime format
data['Date'] = pd.to_datetime(data['Date'])
data['Month'] = data['Date'].dt.to_period('M')

# === Real Time Dashboard Logic ===
if view_type == "Real Time Dashboard":
    selected_date = st.sidebar.date_input("Select a specific date to view analytics")
    selected_datetime = pd.to_datetime(selected_date)

    if selected_datetime not in data['Date'].unique():
        st.warning("⚠️ No data available for the selected date. Please choose an appropriate date.")
        st.stop()
    
    filtered_data = data[data['Date'] == selected_datetime]
    month_data = data[data['Date'].dt.month == selected_datetime.month]
else:
    filtered_data = data.copy()

# === 1. Spend Metrics ===
st.subheader("1. Spend Overview")
total_cost = pd.to_numeric(filtered_data['Cost'], errors='coerce').sum()
monthly_cost = pd.to_numeric(data[data['Date'].dt.month == filtered_data['Date'].dt.month.iloc[0]]['Cost'], errors='coerce').sum()

if view_type == "Real Time Dashboard":
    st.metric("Total Spend (Selected)", f"₹{total_cost:,.2f}")
st.metric("Total Spend (Month)", f"₹{monthly_cost:,.2f}")

# === 2. Reach & Impression ===
st.subheader("2. Reach & Impressions")
st.write("**Totals**")
st.write(f"Reach: {pd.to_numeric(filtered_data['Reach'], errors='coerce').sum():,.0f}")
st.write(f"Impressions: {pd.to_numeric(filtered_data['Impressions'], errors='coerce').sum():,.0f}")
st.write(f"Frequency: {pd.to_numeric(filtered_data['Frequency'], errors='coerce').mean():.2f}")

fig = px.bar(filtered_data, x="Campaign name", y=["Reach", "Impressions"], barmode="group")
st.plotly_chart(fig, use_container_width=True)

# === 3. Engagement Metrics ===
st.subheader("3. Engagement Metrics")
st.write("**Link Clicks & Engagements**")
eng_cols = ["Link clicks", "Unique link clicks", "CTR (link click-through rate)",
            "Cost per unique link click", "Post engagements", "Post reactions",
            "Post comments", "Post shares", "Page engagements"]
eng_df = filtered_data[eng_cols].apply(pd.to_numeric, errors='coerce')
st.dataframe(eng_df.sum().to_frame(name="Total"))

fig_eng = px.bar(filtered_data, x="Campaign name", y=["Link clicks", "Post engagements"], barmode="group")
st.plotly_chart(fig_eng, use_container_width=True)

# === 4. Conversion Metrics ===
st.subheader("4. Conversion Metrics")
conv_cols = ["On-Facebook purchases", "Website adds to cart", "On-Facebook view content",
             "On-Facebook leads", "Landing page views", "Cost per website purchase",
             "Cost per website add to cart"]
conv_df = filtered_data[conv_cols].apply(pd.to_numeric, errors='coerce')
st.dataframe(conv_df.sum().to_frame(name="Total"))

# === 5. Revenue & ROAS ===
st.subheader("5. Revenue & ROAS")
rev_cols = ["Purchase conversion value", "Website purchases conversion value"]
rev_df = filtered_data[rev_cols].apply(pd.to_numeric, errors='coerce')
revenue = rev_df["Purchase conversion value"].sum()
roas = revenue / total_cost if total_cost > 0 else 0
st.metric("Purchase Conversion Value", f"₹{revenue:,.2f}")
st.metric("ROAS", f"{roas:.2f}")

# === 6. Video Metrics ===
st.subheader("6. Video Metrics")
video_cols = ["Video watches at 25%", "Video watches at 50%", "Video watches at 75%",
              "Video watches at 100%", "ThruPlay actions", "Cost per ThruPlay"]
video_df = filtered_data[video_cols].apply(pd.to_numeric, errors='coerce')
st.dataframe(video_df.sum().to_frame(name="Total"))

# === 7. Audience Demographics ===
st.subheader("7. Audience Demographics")
demo_df = filtered_data.groupby(['Age', 'Gender']).agg({
    'Cost': lambda x: pd.to_numeric(x, errors='coerce').sum(),
    'Reach': lambda x: pd.to_numeric(x, errors='coerce').sum(),
    'Impressions': lambda x: pd.to_numeric(x, errors='coerce').sum(),
    'On-Facebook purchases': lambda x: pd.to_numeric(x, errors='coerce').sum()
}).reset_index()
fig_demo = px.bar(demo_df, x='Age', y='On-Facebook purchases', color='Gender', barmode='group')
st.plotly_chart(fig_demo, use_container_width=True)

# === 8. Top Campaigns by ROAS ===
st.subheader("8. Top Campaigns by ROAS")
camp_perf = filtered_data.groupby('Campaign name').agg({
    'Cost': lambda x: pd.to_numeric(x, errors='coerce').sum(),
    'Purchase conversion value': lambda x: pd.to_numeric(x, errors='coerce').sum()
}).reset_index()
camp_perf['ROAS'] = camp_perf['Purchase conversion value'] / camp_perf['Cost']
camp_perf = camp_perf.sort_values(by='ROAS', ascending=False)
st.dataframe(camp_perf.head(10))

# === 9. Cost per Purchase ===
st.subheader("9. Cost per Purchase")
cpp_df = filtered_data.copy()
cpp_df['Cost'] = pd.to_numeric(cpp_df['Cost'], errors='coerce')
cpp_df['On-Facebook purchases'] = pd.to_numeric(cpp_df['On-Facebook purchases'], errors='coerce')
cpp_df['Cost per Purchase'] = cpp_df['Cost'] / cpp_df['On-Facebook purchases'].replace(0, pd.NA)
st.dataframe(cpp_df[['Campaign name', 'Cost', 'On-Facebook purchases', 'Cost per Purchase']].dropna())

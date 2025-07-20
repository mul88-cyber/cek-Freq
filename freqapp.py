import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIG
SHEET_ID = "1ZcsGqqMzMLt35INSJMxwpAVKyTLzUwNiScVONELWSnQ"
GID = "0"
sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

st.set_page_config(page_title="Dashboard Saham Potensial", layout="wide")
st.title("📊 Dashboard Saham Potensial")

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(sheet_url)
    df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
    df['Change %'] = (df['Change'] / df['Close']) * 100
    return df

df = load_data()

# Dropdown filter
st.sidebar.header("📌 Filter")
stock_list = sorted(df['Stock Code'].dropna().unique())
selected_stock = st.sidebar.selectbox("Pilih Saham", stock_list)

df_filtered = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date')

# Show data table
st.subheader(f"📈 Data Saham: {selected_stock}")
st.dataframe(
    df_filtered[['Last Trading Date', 'Close', 'Change', 'Change %', 'Volume', 'Frequency']].sort_values('Last Trading Date', ascending=False),
    use_container_width=True,
    hide_index=True
)

# Tabs grafik
tab1, tab2, tab3 = st.tabs(["📊 Harga Close", "📉 Volume", "📈 Change %"])

with tab1:
    fig1 = px.line(df_filtered, x='Last Trading Date', y='Close',
                   title=f"Harga Close {selected_stock}", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    fig2 = px.bar(df_filtered, x='Last Trading Date', y='Volume',
                  title=f"Volume {selected_stock}")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    fig3 = px.line(df_filtered, x='Last Trading Date', y='Change %',
                   title=f"Persentase Perubahan Harga {selected_stock}", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

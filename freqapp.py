import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIG
SHEET_ID = "ISI_SHEET_ID_KAMU"
GID = "ISI_GID_KAMU"
sheet_url = f"https://docs.google.com/spreadsheets/d/{1ZcsGqqMzMLt35INSJMxwpAVKyTLzUwNiScVONELWSnQ}/export?format=csv&gid={0}"

# TITLE
st.set_page_config(page_title="Dashboard Saham", layout="wide")
st.title("📈 Dashboard Saham Potensial")

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(sheet_url)
    df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'])
    return df

df = load_data()

# FILTER SAHAM
stock_list = df['Stock Code'].unique()
selected_stock = st.selectbox("Pilih Saham", sorted(stock_list))

df_filtered = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date')

# TAMPILKAN DATA
st.subheader(f"Data Saham: {selected_stock}")
st.dataframe(df_filtered[['Last Trading Date', 'Close', 'Change', 'Volume', 'Frequency']].sort_values('Last Trading Date', ascending=False), use_container_width=True)

# HITUNG % CHANGE
df_filtered['Change %'] = (df_filtered['Change'] / df_filtered['Close']) * 100

# GRAFIK
tab1, tab2, tab3 = st.tabs(["📊 Price", "📉 Volume", "📈 Change %"])

with tab1:
    fig_price = px.line(df_filtered, x='Last Trading Date', y='Close', title=f'Harga Close {selected_stock}', markers=True)
    st.plotly_chart(fig_price, use_container_width=True)

with tab2:
    fig_volume = px.bar(df_filtered, x='Last Trading Date', y='Volume', title=f'Volume {selected_stock}')
    st.plotly_chart(fig_volume, use_container_width=True)

with tab3:
    fig_change = px.line(df_filtered, x='Last Trading Date', y='Change %', title=f'Persentase Kenaikan {selected_stock}', markers=True)
    st.plotly_chart(fig_change, use_container_width=True)

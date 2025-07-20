import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- KONFIGURASI & LOAD DATA (Sama seperti sebelumnya) ---
GCS_URL = "https://storage.googleapis.com/stock-csvku/hasil_gabungan.csv"
st.set_page_config(page_title="Dashboard Saham Potensial", layout="wide")
st.title("📊 Dashboard Analisis Saham")

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(GCS_URL)
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
        previous_close = df['Close'] - df['Change']
        previous_close.replace(0, pd.NA, inplace=True) 
        df['Change %'] = ((df['Change'] / previous_close) * 100).fillna(0)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Data tidak tersedia.")
    st.stop()

# --- SIDEBAR FILTER (Sama seperti sebelumnya) ---
st.sidebar.header("📌 Filter Saham")
stock_list = sorted(df['Stock Code'].dropna().unique())
selected_stock = st.sidebar.selectbox("Pilih Kode Saham", stock_list)
df_filtered = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date')


# --- TAMPILAN UTAMA ---
st.header(f"Analisis Saham: {selected_stock}")
st.dataframe(
    df_filtered[['Last Trading Date', 'Close', 'Change %', 'Volume', 'Frequency']].sort_values('Last Trading Date', ascending=False),
    use_container_width=True, hide_index=True,
    column_config={
        "Close": st.column_config.NumberColumn(format="Rp %d"),
        "Change %": st.column_config.NumberColumn(format="%.2f%%"),
    }
)

# --- ALTERNATIF 2: GRAFIK TUNGGAL YANG DIPERBAIKI ---
st.subheader("Grafik Analisis (Model Tunggal)")

# Inisialisasi gambar dengan sumbu-Y sekunder
fig = make_subplots(specs=[[{"secondary_y": True}]])

# 1. Volume sebagai Area Chart Transparan (Sumbu Y Primer / Kiri)
fig.add_trace(go.Scatter(
    x=df_filtered['Last Trading Date'], y=df_filtered['Volume'],
    name='Volume',
    fill='tozeroy',
    mode='none', # Tidak menampilkan garis atau penanda, hanya area
    fillcolor='rgba(119, 136, 153, 0.4)' # Light Slate Gray dengan transparansi
), secondary_y=False)

# 2. Harga Close (Sumbu Y Sekunder / Kanan)
fig.add_trace(go.Scatter(
    x=df_filtered['Last Trading Date'], y=df_filtered['Close'],
    name='Harga (Rp)',
    mode='lines',
    line=dict(color='#FF8C00', width=2.5) # Dark Orange, lebih tebal
), secondary_y=True)

# 3. Frekuensi (Sumbu Y Sekunder / Kanan)
fig.add_trace(go.Scatter(
    x=df_filtered['Last Trading Date'], y=df_filtered['Frequency'],
    name='Frekuensi',
    mode='lines',
    line=dict(color='#00FA9A', width=1.5) # Medium Spring Green
), secondary_y=True)


# Konfigurasi Layout
fig.update_layout(
    height=500,
    title_text=f'Analisis Gabungan Saham {selected_stock}',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Atur judul sumbu-Y
fig.update_yaxes(title_text="<b>Volume Perdagangan</b>", secondary_y=False)
fig.update_yaxes(title_text="<b>Harga (Rp) & Frekuensi</b>", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)

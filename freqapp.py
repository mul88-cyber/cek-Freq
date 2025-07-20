import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- KONFIGURASI ---
GCS_URL = "https://storage.googleapis.com/stock-csvku/hasil_gabungan.csv"

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Dashboard Saham Potensial", layout="wide")
st.title("📊 Dashboard Analisis Saham Gabungan")


# --- FUNGSI LOAD DATA (dengan caching) ---
@st.cache_data(ttl=300)
def load_data():
    """
    Memuat data dari GCS, membersihkan, dan menghitung metrik.
    """
    try:
        df = pd.read_csv(GCS_URL)
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
        
        previous_close = df['Close'] - df['Change']
        previous_close.replace(0, pd.NA, inplace=True) 
        df['Change %'] = ((df['Change'] / previous_close) * 100).fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari URL: {GCS_URL}")
        st.error(f"Error: {e}")
        return pd.DataFrame()

# --- LOAD DATA ---
df = load_data()

if df.empty:
    st.warning("Data tidak tersedia. Mohon periksa kembali URL atau isi file CSV.")
    st.stop()


# --- SIDEBAR FILTER ---
st.sidebar.header("📌 Filter Saham")
stock_list = sorted(df['Stock Code'].dropna().unique())
selected_stock = st.sidebar.selectbox("Pilih Kode Saham", stock_list)

# Filter dataframe berdasarkan saham yang dipilih
df_filtered = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date')


# --- TAMPILAN UTAMA ---
st.header(f"Analisis Gabungan: {selected_stock}")

# --- TAMPILKAN TABEL DATA ---
st.subheader("📈 Data Historis")
st.dataframe(
    df_filtered[['Last Trading Date', 'Close', 'Change %', 'Volume', 'Frequency']].sort_values(
        'Last Trading Date', ascending=False
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Close": st.column_config.NumberColumn(format="Rp %d"),
        "Change %": st.column_config.NumberColumn(format="%.2f%%"),
        "Volume": st.column_config.NumberColumn(format="%d"),
    }
)

# --- BUAT GRAFIK GABUNGAN DENGAN DUAL-AXIS ---
st.subheader("📊 Grafik Gabungan (Volume, Harga, Frekuensi)")

# 1. Inisialisasi gambar dengan sumbu-Y sekunder
fig = make_subplots(specs=[[{"secondary_y": True}]])

# 2. Tambahkan Bar Chart untuk Volume (Sumbu-Y Primer / Kiri)
fig.add_trace(
    go.Bar(x=df_filtered['Last Trading Date'], y=df_filtered['Volume'], name='Volume', marker_color='lightblue'),
    secondary_y=False,
)

# 3. Tambahkan Line Chart untuk Harga Close (Sumbu-Y Sekunder / Kanan)
fig.add_trace(
    go.Scatter(x=df_filtered['Last Trading Date'], y=df_filtered['Close'], name='Close', mode='lines+markers', line=dict(color='orange')),
    secondary_y=True,
)

# 4. Tambahkan Line Chart untuk Frekuensi (Sumbu-Y Sekunder / Kanan)
fig.add_trace(
    go.Scatter(x=df_filtered['Last Trading Date'], y=df_filtered['Frequency'], name='Frequency', mode='lines+markers', line=dict(color='green')),
    secondary_y=True,
)

# 5. Atur Layout dan Judul Sumbu
fig.update_layout(
    title_text=f'Analisis Gabungan Saham {selected_stock}',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Atur judul sumbu-Y
fig.update_yaxes(title_text="Volume Perdagangan", secondary_y=False)
fig.update_yaxes(title_text="Harga (Rp) & Frekuensi", secondary_y=True)


# Tampilkan grafik di Streamlit
st.plotly_chart(fig, use_container_width=True)

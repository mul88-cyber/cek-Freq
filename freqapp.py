import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Visualisasi Harga Saham", layout="wide")
st.title("📊 Visualisasi Pergerakan Harga Saham")
st.info("Upload file historis `hasil_gabungan.csv` untuk memulai.")

# --- FUNGSI UNTUK MEMBACA DATA ---
@st.cache_data(ttl=300)
def load_data(uploaded_file):
    """Membaca data dari file CSV yang di-upload."""
    if uploaded_file is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(uploaded_file)
        # Konversi kolom tanggal ke format datetime
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'])
        return df
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return pd.DataFrame()

# --- SIDEBAR & UPLOADER ---
st.sidebar.header("📌 Upload & Filter")
uploaded_file = st.sidebar.file_uploader(
    "Upload file hasil_gabungan.csv",
    type=["csv"]
)

df = load_data(uploaded_file)

# --- TAMPILAN UTAMA JIKA DATA TERSEDIA ---
if not df.empty:
    st.sidebar.success(f"{len(df)} baris data berhasil dimuat.")

    # Membuat daftar saham unik untuk filter dropdown
    stock_list = sorted(df['Stock Code'].unique())
    selected_stock = st.sidebar.selectbox("Pilih Kode Saham", stock_list)

    st.header(f"Analisis untuk Saham: {selected_stock}")

    # Filter dataframe berdasarkan saham yang dipilih
    df_filtered = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date')

    # --- MEMBUAT GRAFIK GARIS (LINE CHART) ---
    st.subheader("Grafik Pergerakan Harga Penutupan (Close)")

    fig = px.line(
        df_filtered,
        x='Last Trading Date',
        y='Close',
        title=f"Pergerakan Harga Saham {selected_stock}",
        markers=True  # Menambahkan penanda titik untuk setiap hari
    )
    
    # Memperbarui layout agar lebih informatif
    fig.update_layout(
        xaxis_title="Tanggal",
        yaxis_title="Harga Penutupan (Rp)",
        showlegend=True
    )

    # Tampilkan grafik di Streamlit
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Menunggu file CSV di-upload...")

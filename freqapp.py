import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI ---
# URL sudah diganti sesuai file yang benar
GCS_URL = "https://storage.googleapis.com/stock-csvku/hasil_gabungan.csv"

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Dashboard Saham Potensial", layout="wide")
st.title("📊 Dashboard Saham Potensial")


# --- FUNGSI LOAD DATA (dengan caching) ---
@st.cache_data(ttl=300)  # Cache data selama 5 menit
def load_data():
    """
    Memuat data dari Google Cloud Storage, membersihkan, 
    dan menghitung metrik tambahan.
    """
    try:
        df = pd.read_csv(GCS_URL)
        
        # Konversi tanggal, error akan menjadi NaT (Not a Time)
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
        
        # --- PERBAIKAN LOGIKA PERHITUNGAN CHANGE % ---
        # Hitung harga penutupan sebelumnya (Previous Close)
        previous_close = df['Close'] - df['Change']
        
        # Hindari pembagian dengan nol jika harga sebelumnya 0
        # Ganti 0 dengan None (NaN) agar hasil pembagiannya juga NaN
        previous_close.replace(0, pd.NA, inplace=True) 
        
        # Hitung persentase perubahan terhadap harga sebelumnya
        df['Change %'] = (df['Change'] / previous_close) * 100
        
        # Ganti nilai NaN di 'Change %' (jika ada) dengan 0
        df['Change %'] = df['Change %'].fillna(0)

        return df

    except Exception as e:
        st.error(f"Gagal memuat data dari URL: {GCS_URL}")
        st.error(f"Error: {e}")
        return pd.DataFrame() # Kembalikan dataframe kosong jika gagal

# --- LOAD DATA ---
df = load_data()

# Jika dataframe kosong setelah gagal load, hentikan eksekusi
if df.empty:
    st.warning("Data tidak tersedia. Mohon periksa kembali URL atau isi file CSV.")
    st.stop()


# --- SIDEBAR FILTER ---
st.sidebar.header("📌 Filter Saham")
# Ambil daftar saham unik dan urutkan, hapus nilai kosong (NaN)
stock_list = sorted(df['Stock Code'].dropna().unique())
selected_stock = st.sidebar.selectbox("Pilih Kode Saham", stock_list)

# Filter dataframe berdasarkan saham yang dipilih dan urutkan berdasarkan tanggal
df_filtered = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date')


# --- TAMPILAN UTAMA ---
st.header(f"Analisis Saham: {selected_stock}")

# Tampilkan tabel data terakhir di paling atas
st.subheader("📈 Data Historis")
st.dataframe(
    df_filtered[['Last Trading Date', 'Close', 'Change', 'Change %', 'Volume', 'Frequency']].sort_values(
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

# Buat Tab untuk visualisasi
tab1, tab2, tab3 = st.tabs(["📊 Harga Penutupan (Close)", "📉 Volume Perdagangan", "📈 Persentase Perubahan (%)"])

with tab1:
    fig1 = px.line(df_filtered, x='Last Trading Date', y='Close',
                   title=f"Grafik Harga Penutupan {selected_stock}", markers=True)
    fig1.update_layout(xaxis_title="Tanggal", yaxis_title="Harga Penutupan (Rp)")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    fig2 = px.bar(df_filtered, x='Last Trading Date', y='Volume',
                  title=f"Grafik Volume Perdagangan {selected_stock}")
    fig2.update_layout(xaxis_title="Tanggal", yaxis_title="Volume")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    fig3 = px.line(df_filtered, x='Last Trading Date', y='Change %',
                   title=f"Grafik Persentase Perubahan Harian {selected_stock}", markers=True)
    fig3.update_layout(xaxis_title="Tanggal", yaxis_title="Perubahan (%)")
    st.plotly_chart(fig3, use_container_width=True)

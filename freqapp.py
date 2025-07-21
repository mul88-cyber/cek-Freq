import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.api as sm # Library untuk analisis statistik

# --- KONFIGURASI & LOAD DATA ---
GCS_URL = "https://storage.googleapis.com/stock-csvku/hasil_gabungan.csv"
st.set_page_config(page_title="Dashboard Riset Saham", layout="wide")
st.title("📊 Dashboard Riset Pengaruh Transaksi Vol Freq")

@st.cache_data(ttl=300)
def load_data():
    """Memuat data, membersihkan, dan membuat variabel baru."""
    try:
        df = pd.read_csv(GCS_URL)
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
        df['Bulan'] = df['Last Trading Date'].dt.strftime('%Y-%m')
        
        # PERHITUNGAN VARIABEL UNTUK TESIS
        # Y (Dependent Variable): Kenaikan/Penurunan Harga dalam Rupiah
        # Kita akan menggunakan kolom 'Change' sebagai variabel Y
        
        # X3 (Independent Variable): Net Foreign
        # Sesuai permintaan: Foreign Sell - Foreign Buy
        if 'Foreign Sell' in df.columns and 'Foreign Buy' in df.columns:
            df['Net Foreign'] = df['Foreign Sell'] - df['Foreign Buy']
        else:
            # Jika kolom tidak ada, buat kolom kosong agar tidak error
            df['Net Foreign'] = 0 
        
        df.dropna(subset=['Last Trading Date', 'Change', 'Volume', 'Frequency'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Data tidak tersedia atau gagal dimuat.")
    st.stop()

# --- SIDEBAR FILTER ---
st.sidebar.header("📌 Filter Data")
stock_list = sorted(df['Stock Code'].dropna().unique())
selected_stock = st.sidebar.selectbox("Pilih Kode Saham untuk Analisis", stock_list)
df_stock_filtered = df[df['Stock Code'] == selected_stock]
month_list = sorted(df_stock_filtered['Bulan'].unique())
selected_months = st.sidebar.multiselect("Pilih Periode Bulan", options=month_list, default=month_list)

# --- FILTER DATA AKHIR ---
if not selected_months:
    st.warning("Pilih minimal satu bulan untuk menampilkan data.")
    df_filtered = pd.DataFrame()
else:
    df_filtered = df_stock_filtered[df_stock_filtered['Bulan'].isin(selected_months)].sort_values('Last Trading Date')

# --- TAMPILAN UTAMA ---
st.header(f"Analisis Saham: {selected_stock}")
st.info(f"Periode data yang dianalisis: **{selected_months[0]}** sampai **{selected_months[-1]}**.")

# --- Bagian Grafik (Sama seperti sebelumnya) ---
st.subheader("Grafik Visual")
# ... (kode grafik dari skrip sebelumnya bisa ditaruh di sini jika mau)

# --- BAGIAN BARU: ANALISIS REGRESI UNTUK MINI TESIS ---
st.header("🔬 Analisis Regresi untuk Mini Tesis")
st.markdown(f"**Hipotesis:** Apakah **Volume (X1)**, **Frekuensi (X2)**, dan **Net Foreign (X3)** berpengaruh terhadap **Perubahan Harga (Y)** pada saham **{selected_stock}**?")

# Cek apakah data cukup untuk dianalisis
if not df_filtered.empty and len(df_filtered) > 4:
    # 1. Definisikan Variabel
    Y = df_filtered['Change']
    X = df_filtered[['Volume', 'Frequency', 'Net Foreign']]
    X = sm.add_constant(X) # Menambahkan konstanta (intercept) ke model

    # 2. Jalankan Model Regresi (Ordinary Least Squares)
    model = sm.OLS(Y, X).fit()
    
    # 3. Tampilkan Hasil Tabel Statistik
    st.subheader("Hasil Output Statistik")
    st.code(model.summary())
    
    # 4. Tampilkan Interpretasi Hasil
    st.subheader("Interpretasi Hasil Analisis")
    
    # Interpretasi R-squared
    r_squared = model.rsquared_adj * 100
    st.markdown(f"""
    - **R-squared (adjusted): {r_squared:.2f}%**
    - **Artinya:** Sekitar **{r_squared:.2f}%** variasi (naik/turunnya) harga saham **{selected_stock}** dapat dijelaskan secara bersama-sama oleh variabel Volume, Frekuensi, dan Net Foreign dalam model ini. Sisanya dijelaskan oleh faktor lain di luar model.
    """)
    
    # Interpretasi Koefisien & Signifikansi (P>|t|)
    st.markdown("**Pengaruh Masing-Masing Variabel:**")
    
    results_df = pd.DataFrame({
        "Koefisien": model.params,
        "P-value": model.pvalues
    })
    
    # Volume
    coef_vol = results_df.loc['Volume']['Koefisien']
    pval_vol = results_df.loc['Volume']['P-value']
    pengaruh_vol = "naik" if coef_vol > 0 else "turun"
    signifikan_vol = "**signifikan secara statistik**" if pval_vol < 0.05 else "tidak signifikan."
    st.markdown(f"""
    - **Volume (X1):** Koefisiennya **{coef_vol:.4f}**. Artinya, setiap kenaikan 1 unit volume transaksi, diprediksi akan membuat harga saham **{pengaruh_vol} sebesar {abs(coef_vol):.4f} Rupiah**, dengan asumsi variabel lain konstan. Pengaruh ini dinyatakan **{signifikan_vol}** (P-value = {pval_vol:.3f}).
    """)
    
    # Frekuensi
    coef_freq = results_df.loc['Frequency']['Koefisien']
    pval_freq = results_df.loc['Frequency']['P-value']
    pengaruh_freq = "naik" if coef_freq > 0 else "turun"
    signifikan_freq = "**signifikan secara statistik**" if pval_freq < 0.05 else "tidak signifikan."
    st.markdown(f"""
    - **Frekuensi (X2):** Koefisiennya **{coef_freq:.4f}**. Artinya, setiap kenaikan 1 kali frekuensi transaksi, diprediksi akan membuat harga saham **{pengaruh_freq} sebesar {abs(coef_freq):.4f} Rupiah**, dengan asumsi variabel lain konstan. Pengaruh ini dinyatakan **{signifikan_freq}** (P-value = {pval_freq:.3f}).
    """)
    
    # Net Foreign
    # Cek dulu apakah kolomnya ada dan tidak nol semua
    if 'Net Foreign' in results_df.index:
        coef_netf = results_df.loc['Net Foreign']['Koefisien']
        pval_netf = results_df.loc['Net Foreign']['P-value']
        pengaruh_netf = "naik" if coef_netf > 0 else "turun"
        signifikan_netf = "**signifikan secara statistik**" if pval_netf < 0.05 else "tidak signifikan."
        st.markdown(f"""
        - **Net Foreign (X3):** Koefisiennya **{coef_netf:.4f}**. Artinya, setiap kenaikan 1 Rupiah pada Net Foreign (semakin banyak jual daripada beli), diprediksi akan membuat harga saham **{pengaruh_netf} sebesar {abs(coef_netf):.4f} Rupiah**, dengan asumsi variabel lain konstan. Pengaruh ini dinyatakan **{signifikan_netf}** (P-value = {pval_netf:.3f}).
        """)

    st.success("Analisis selesai. Kamu bisa menggunakan tabel output dan interpretasi di atas untuk bahan mini tesismu.")

else:
    st.warning("Data tidak cukup untuk melakukan analisis regresi. Pilih periode yang lebih panjang atau saham lain.")

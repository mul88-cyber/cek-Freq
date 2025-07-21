import streamlit as st
import pandas as pd
import statsmodels.api as sm
import numpy as np

# --- KONFIGURASI & LOAD DATA ---
st.set_page_config(page_title="Dashboard Analisis Prediktif", layout="wide")
st.title("📈 Dashboard Analisis Prediktif Saham")

@st.cache_data(ttl=300)
def load_data(file_uploader):
    """Memuat data dari file yang di-upload."""
    if file_uploader is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_uploader)
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
        if 'Net Foreign' not in df.columns:
            df['Net Foreign'] = df['Foreign Sell'] - df['Foreign Buy']
        df.dropna(subset=['Last Trading Date', 'Change', 'Volume', 'Frequency', 'Stock Code'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

# --- UPLOADER DI SIDEBAR ---
st.sidebar.header("📌 Upload & Filter Data")
uploaded_file = st.sidebar.file_uploader("Upload file hasil_gabungan.csv", type=["csv"])

df = load_data(uploaded_file)

if not df.empty:
    stock_list = sorted(df['Stock Code'].dropna().unique())
    selected_stock = st.sidebar.selectbox("Pilih Kode Saham untuk Analisis", stock_list)
    
    # Filter data hanya untuk saham yang dipilih
    df_stock = df[df['Stock Code'] == selected_stock].sort_values('Last Trading Date').copy()

    st.header(f"Analisis Prediktif untuk Saham: {selected_stock}")
    st.markdown(f"**Hipotesis:** Apakah `Volume`, `Frekuensi`, dan `Net Foreign` hari ini bisa memprediksi kenaikan harga **besok**?")

    # --- PERSIAPAN DATA UNTUK PREDIKSI ---
    # Variabel prediktor (X) adalah data hari ini
    X = df_stock[['Volume', 'Frequency', 'Net Foreign']]
    
    # Variabel target (Y) adalah apa yang terjadi besok
    # Kita "geser" kolom 'Change' ke atas (-1) untuk mendapatkan perubahan harga besok
    df_stock['Perubahan Harga Besok'] = df_stock['Change'].shift(-1)
    
    # Buat target biner: 1 jika harga besok naik (> 0), 0 jika turun/tetap (<= 0)
    df_stock['Besok Naik?'] = (df_stock['Perubahan Harga Besok'] > 0).astype(int)
    
    # Hapus baris terakhir karena tidak punya data 'besok'
    df_stock.dropna(subset=['Perubahan Harga Besok'], inplace=True)
    
    Y = df_stock['Besok Naik?']
    X = X.loc[Y.index] # Pastikan X dan Y punya baris yang sama

    # Cek apakah data cukup
    if len(df_stock) > 10:
        # --- MENJALANKAN MODEL REGRESI LOGISTIK ---
        X = sm.add_constant(X)
        model = sm.Logit(Y, X).fit(disp=0) # disp=0 untuk menyembunyikan output iterasi

        st.subheader("Hasil Model Prediktif (Regresi Logistik)")
        st.code(model.summary())
        
        # --- INTERPRETASI HASIL ---
        st.subheader("Cara Membaca Hasilnya")
        
        # Akurasi Model
        predictions = (model.predict(X) > 0.5).astype(int)
        accuracy = np.mean(predictions == Y) * 100
        st.markdown(f"🎯 **Akurasi Model**: Model ini berhasil menebak **{accuracy:.2f}%** dari total hari perdagangan apakah harga akan naik atau turun besok. (Catatan: Akurasi 50% sama dengan lempar koin).")

        # Koefisien
        st.markdown("**Pengaruh Setiap Variabel:**")
        odds_ratios = np.exp(model.params)
        st.markdown(f"- **Volume**: Setiap kenaikan 1 unit `Volume`, peluang (odds) harga untuk naik besok berubah **{odds_ratios['Volume']:.4f} kali**.")
        st.markdown(f"- **Frekuensi**: Setiap kenaikan 1 unit `Frekuensi`, peluang (odds) harga untuk naik besok berubah **{odds_ratios['Frequency']:.4f} kali**.")
        st.markdown(f"- **Net Foreign**: Setiap kenaikan 1 unit `Net Foreign`, peluang (odds) harga untuk naik besok berubah **{odds_ratios['Net Foreign']:.4f} kali**.")
        st.caption("*(Nilai > 1 berarti meningkatkan peluang, Nilai < 1 berarti menurunkan peluang)*")

        # P-values
        st.markdown("**Tingkat Keyakinan (Signifikansi Statistik):**")
        st.markdown("Lihat kolom `P>|z|` pada tabel di atas. Jika nilainya di bawah 0.05, artinya pengaruh variabel tersebut **signifikan secara statistik** dan bukan cuma kebetulan.")
        
        st.warning("**Disclaimer:** Analisis ini berdasarkan data historis dan bukan merupakan saran finansial. Kinerja masa lalu tidak menjamin hasil di masa depan.")

    else:
        st.warning("Data tidak cukup untuk saham ini untuk dilakukan analisis prediktif.")
else:
    st.info("Silakan upload file CSV datamu untuk memulai analisis.")

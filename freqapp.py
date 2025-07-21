import streamlit as st
import pandas as pd
import statsmodels.api as sm

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Analisis Harian", layout="wide")
st.title("📊 Dashboard Analisis Data Saham Harian")
st.info("Anda bisa meng-upload beberapa file harian (.xlsx) sekaligus. Data akan otomatis digabungkan.")

# --- FUNGSI UNTUK MEMBACA DAN MENGGABUNGKAN DATA ---
@st.cache_data(ttl=300)
def load_and_combine_data(uploaded_files):
    """Membaca semua file yg di-upload, menggabungkannya, dan membersihkan data."""
    if not uploaded_files:
        return pd.DataFrame()
    
    dataframes = []
    for file in uploaded_files:
        try:
            # Baca file excel. 'engine='openpyxl'' dibutuhkan untuk file .xlsx modern
            df = pd.read_excel(file, engine='openpyxl')
            dataframes.append(df)
        except Exception as e:
            st.warning(f"Gagal membaca file {file.name}: {e}")
            
    if not dataframes:
        return pd.DataFrame()
        
    # Gabungkan semua dataframe menjadi satu
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Lakukan pembersihan data pada dataframe gabungan
    # Ubah nama kolom agar konsisten (sesuaikan jika nama di file xlsx berbeda)
    # Contoh: jika nama kolomnya 'Kode Saham', ubah jadi 'Stock Code'
    # combined_df.rename(columns={'Nama Kolom Asli': 'Nama Kolom Baru'}, inplace=True)
    
    # Hapus baris yang tidak memiliki 'Stock Code'
    combined_df.dropna(subset=['Stock Code'], inplace=True)
    # Hapus baris ringkasan (jika ada) yang biasanya tidak punya kode saham
    combined_df = combined_df[combined_df['Stock Code'] != 'Total']
    
    # Hitung 'Change' dan 'Net Foreign' jika belum ada
    if 'Change' not in combined_df.columns:
        # Asumsikan 'Close' dan 'Prev' ada
        combined_df['Close'] = pd.to_numeric(combined_df['Close'], errors='coerce')
        combined_df['Prev'] = pd.to_numeric(combined_df['Prev'], errors='coerce')
        combined_df['Change'] = combined_df['Close'] - combined_df['Prev']

    if 'Net Foreign' not in combined_df.columns:
        combined_df['Foreign Buy'] = pd.to_numeric(combined_df['Foreign Buy'], errors='coerce')
        combined_df['Foreign Sell'] = pd.to_numeric(combined_df['Foreign Sell'], errors='coerce')
        combined_df['Net Foreign'] = combined_df['Foreign Sell'] - combined_df['Foreign Buy']

    # Pastikan tipe data numerik benar
    numeric_cols = ['Volume', 'Frequency', 'Net Foreign', 'Change']
    for col in numeric_cols:
        combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')

    combined_df.dropna(subset=numeric_cols, inplace=True)
        
    return combined_df

# --- SIDEBAR & UPLOADER ---
st.sidebar.header("📌 Upload & Filter")
uploaded_files = st.sidebar.file_uploader(
    "Upload file harian (.xlsx)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

df_combined = load_and_combine_data(uploaded_files)

# --- ANALISIS JIKA DATA TERSEDIA ---
if not df_combined.empty:
    st.sidebar.success(f"{len(df_combined)} baris data berhasil dimuat dari {len(uploaded_files)} file.")
    
    stock_list = ['Semua Saham'] + sorted(df_combined['Stock Code'].unique())
    selected_stock = st.sidebar.selectbox("Pilih Kode Saham untuk Analisis", stock_list)

    if selected_stock == 'Semua Saham':
        df_filtered = df_combined
    else:
        df_filtered = df_combined[df_combined['Stock Code'] == selected_stock]
        
    st.header(f"Analisis untuk: {selected_stock}")
    st.dataframe(df_filtered)

    # --- ANALISIS REGRESI ---
    st.header("🔬 Analisis Regresi Pengaruh Transaksi")
    st.markdown("**Hipotesis:** Apakah `Volume`, `Frekuensi`, dan `Net Foreign` berpengaruh terhadap `Perubahan Harga` pada hari yang sama?")

    if len(df_filtered) > 4:
        Y = df_filtered['Change']
        X = df_filtered[['Volume', 'Frequency', 'Net Foreign']]
        X = sm.add_constant(X)

        model = sm.OLS(Y, X).fit()
        
        st.subheader("Hasil Output Statistik")
        st.code(model.summary())
        
        st.subheader("Interpretasi Hasil")
        r_squared = model.rsquared_adj * 100
        st.markdown(f"- **R-squared (adjusted):** Sekitar **{r_squared:.2f}%** variasi harga dapat dijelaskan oleh model ini.")
        # ... (Interpretasi detail lainnya bisa ditambahkan seperti skrip sebelumnya) ...
    else:
        st.warning("Data tidak cukup untuk melakukan analisis regresi. Upload lebih banyak file atau pilih 'Semua Saham'.")

else:
    st.info("Silakan upload satu atau lebih file Excel data harian untuk memulai analisis.")

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

# --- ALTERNATIF 1: GRAFIK BERTUMPUK (STACKED CHARTS) ---
st.subheader("Grafik Analisis (Model Bertumpuk)")

# Buat 2 baris subplot, yang berbagi sumbu-X
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    row_heights=[0.7, 0.3], # Alokasi ruang: 70% untuk chart atas, 30% bawah
                    specs=[[{"secondary_y": True}], # Chart atas punya sumbu Y ganda
                           [{"secondary_y": False}]]) # Chart bawah tidak

# Grafik Atas (Harga & Frekuensi)
# 1. Harga Close (Sumbu Y Primer / Kiri)
fig.add_trace(go.Scatter(
    x=df_filtered['Last Trading Date'], y=df_filtered['Close'],
    name='Harga (Rp)', mode='lines', line=dict(color='#00BFFF', width=2) # Deep Sky Blue
), row=1, col=1, secondary_y=False)

# 2. Frekuensi (Sumbu Y Sekunder / Kanan)
fig.add_trace(go.Scatter(
    x=df_filtered['Last Trading Date'], y=df_filtered['Frequency'],
    name='Frekuensi', mode='lines', line=dict(color='#32CD32', width=1.5, dash='dash') # Lime Green
), row=1, col=1, secondary_y=True)

# Grafik Bawah (Volume)
# 3. Volume sebagai Area Chart
fig.add_trace(go.Scatter(
    x=df_filtered['Last Trading Date'], y=df_filtered['Volume'],
    name='Volume', fill='tozeroy', mode='none', fillcolor='rgba(119, 136, 153, 0.5)' # Light Slate Gray
), row=2, col=1)

# Konfigurasi Layout
fig.update_layout(
    height=600,
    showlegend=True,
    xaxis_showticklabels=True,
    xaxis2_showticklabels=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
# Sembunyikan label tanggal di grafik atas untuk menghindari duplikasi
fig.update_xaxes(showticklabels=False, row=1, col=1)

# Atur judul sumbu-Y
fig.update_yaxes(title_text="<b>Harga Close (Rp)</b>", color='#00BFFF', row=1, col=1, secondary_y=False)
fig.update_yaxes(title_text="<b>Frekuensi</b>", color='#32CD32', row=1, col=1, secondary_y=True)
fig.update_yaxes(title_text="<b>Volume</b>", row=2, col=1)


st.plotly_chart(fig, use_container_width=True)

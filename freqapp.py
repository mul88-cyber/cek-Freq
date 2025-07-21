import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- KONFIGURASI & LOAD DATA ---
GCS_URL = "https://storage.googleapis.com/stock-csvku/hasil_gabungan.csv"
st.set_page_config(page_title="Dashboard Saham Potensial", layout="wide")
st.title("📊 Dashboard Analisis FREQ")

@st.cache_data(ttl=300)
def load_data():
    """Memuat data dari GCS, membersihkan, dan menghitung metrik."""
    try:
        df = pd.read_csv(GCS_URL)
        df['Last Trading Date'] = pd.to_datetime(df['Last Trading Date'], errors='coerce')
        df['Bulan'] = df['Last Trading Date'].dt.strftime('%Y-%m')
        
        previous_close = df['Close'] - df['Change']
        previous_close.replace(0, pd.NA, inplace=True)
        df['Change %'] = ((df['Change'] / previous_close) * 100).fillna(0)
        
        df.dropna(subset=['Last Trading Date'], inplace=True)
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
selected_stock = st.sidebar.selectbox("Pilih Kode Saham", stock_list)

df_stock_filtered = df[df['Stock Code'] == selected_stock]

month_list = sorted(df_stock_filtered['Bulan'].unique())

selected_months = st.sidebar.multiselect(
    "Pilih Bulan (bisa lebih dari satu)",
    options=month_list,
    default=month_list
)

# --- FILTER DATA AKHIR ---
if not selected_months:
    st.warning("Pilih minimal satu bulan untuk menampilkan data.")
    df_filtered = pd.DataFrame()
else:
    df_filtered = df_stock_filtered[df_stock_filtered['Bulan'].isin(selected_months)].sort_values('Last Trading Date')


# --- TAMPILAN UTAMA ---
st.header(f"Analisis Saham: {selected_stock}")

if not df_filtered.empty:
    st.subheader("📈 Data Historis")
    st.dataframe(
        df_filtered[['Last Trading Date', 'Close', 'Change %', 'Volume', 'Frequency']].sort_values('Last Trading Date', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={"Close": st.column_config.NumberColumn(format="Rp %d"), "Change %": st.column_config.NumberColumn(format="%.2f%%")}
    )

    # --- GRAFIK BERTUMPUK (STACKED CHARTS) ---
    st.subheader("Grafik Analisis")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        row_heights=[0.7, 0.3], specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

    fig.add_trace(go.Scatter(
        x=df_filtered['Last Trading Date'], y=df_filtered['Close'],
        name='Harga (Rp)', mode='lines', line=dict(color='#00BFFF', width=2)
    ), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_filtered['Last Trading Date'], y=df_filtered['Frequency'],
        name='Frekuensi', mode='lines', line=dict(color='#32CD32', width=1.5, dash='dash')
    ), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(
        x=df_filtered['Last Trading Date'], y=df_filtered['Volume'],
        name='Volume', fill='tozeroy', mode='none', fillcolor='rgba(119, 136, 153, 0.5)'
    ), row=2, col=1)

    # Konfigurasi Layout
    fig.update_layout(height=600, showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_yaxes(title_text="<b>Harga Close (Rp)</b>", color='#00BFFF', row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="<b>Frekuensi</b>", color='#32CD32', row=1, col=1, secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text="<b>Volume</b>", row=2, col=1)
    
    # --- BARIS BARU UNTUK MENAMPILKAN SEMUA TANGGAL ---
    # Paksa sumbu-X untuk menampilkan setiap label tanggal dari data yang difilter
    fig.update_xaxes(
        tickvals=df_filtered['Last Trading Date'],
        tickformat='%d %b', # Format tanggal menjadi '14 Jul', '15 Jul', dst.
        tickangle=45, # Miringkan label agar tidak tumpang tindih
        row=2, col=1
    )
    # --- AKHIR BARIS BARU ---

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tidak ada data untuk ditampilkan sesuai filter yang dipilih.")

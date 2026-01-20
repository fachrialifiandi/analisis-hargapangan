import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Harga Pangan",
    page_icon="🌾",
    layout="wide"
)

# --- FUNGSI LOAD DATA ---


@st.cache_data
def load_data():

    try:
        df = pd.read_excel("data_pangan.xlsx")
    except FileNotFoundError:
        st.error("File tidak ditemukan.")
        return pd.DataFrame()

    # --- MEMBERSIHKAN DATA ---

    # 1. Bersihkan Kolom Harga (Contoh: "Rp 12.373" -> 12373)
    def clean_currency(x):
        if isinstance(x, str):
            # Hapus 'Rp', hapus titik ribuan, hapus spasi
            clean_str = x.replace("Rp", "").replace(".", "").strip()
            # Jika ada koma sebagai desimal (misal 12.000,00), ganti jadi titik
            clean_str = clean_str.replace(",", ".")
            try:
                return float(clean_str)
            except ValueError:
                return 0
        return x

    if 'Harga' in df.columns:
        df['Harga_Num'] = df['Harga'].apply(clean_currency)

    # 2. Pastikan Tanggal formatnya benar
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])

    return df


# --- MEMUAT DATA ---
df = load_data()

if df.empty:
    st.stop()

# --- SIDEBAR (FILTER) ---
st.sidebar.header("🔍 Filter Data")

# 1. Filter Komoditas
list_komoditas = df['Komoditas'].unique()
pilihan_komoditas = st.sidebar.selectbox("Pilih Komoditas:", list_komoditas)

# 2. Filter Rentang Waktu
min_date = df['Tanggal'].min()
max_date = df['Tanggal'].max()

start_date, end_date = st.sidebar.date_input(
    "Rentang Tanggal:",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Terapkan Filter
df_filtered = df[
    (df['Komoditas'] == pilihan_komoditas) &
    (df['Tanggal'] >= pd.to_datetime(start_date)) &
    (df['Tanggal'] <= pd.to_datetime(end_date))
]

# --- HALAMAN UTAMA ---
st.title(f"📊 Monitoring Harga: {pilihan_komoditas}")
st.markdown(
    "Dashboard ini menampilkan data harga pangan eceran daerah berdasarkan data Bapanas.")

# 1. METRIK RINGKASAN
col1, col2, col3, col4 = st.columns(4)

rata_rata = df_filtered['Harga_Num'].mean()
harga_min = df_filtered['Harga_Num'].min()
harga_max = df_filtered['Harga_Num'].max()
jumlah_provinsi = df_filtered['Provinsi'].nunique()

col1.metric("Rata-rata Nasional", f"Rp {rata_rata:,.0f}")
col2.metric("Harga Terendah", f"Rp {harga_min:,.0f}")
col3.metric("Harga Tertinggi", f"Rp {harga_max:,.0f}")
col4.metric("Jumlah Wilayah Data", f"{jumlah_provinsi} Lokasi")

st.divider()

# 2. VISUALISASI UTAMA
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Tren Pergerakan Harga")
    # Agregasi harga rata-rata per hari
    trend_data = df_filtered.groupby(
        'Tanggal')['Harga_Num'].mean().reset_index()

    fig_line = px.line(
        trend_data,
        x='Tanggal',
        y='Harga_Num',
        markers=True,
        title=f"Tren Rata-rata Harga {pilihan_komoditas}",
        labels={'Harga_Num': 'Harga (Rp)', 'Tanggal': 'Tanggal'}
    )
    fig_line.update_layout(hovermode="x unified")
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("🗺️ Peta Persebaran")
    # Ambil data terbaru saja untuk peta
    latest_date = df_filtered['Tanggal'].max()
    map_data = df_filtered[
        (df_filtered['Tanggal'] == latest_date) &
        (df_filtered['Latitude'] != 0)  # Hapus data tanpa koordinat
    ]

    if not map_data.empty:
        # Scatter Mapbox: Warna titik berbeda sesuai harga
        fig_map = px.scatter_mapbox(
            map_data,
            lat="Latitude",
            lon="Longtitude",
            color="Harga_Num",
            size_max=15,
            zoom=3.5,
            hover_name="Provinsi",
            hover_data={"Harga": True, "Latitude": False,
                        "Longtitude": False, "Harga_Num": False},
            color_continuous_scale="RdYlGn_r",  # Merah = Mahal, Hijau = Murah
            mapbox_style="open-street-map",
            title=f"Harga per Provinsi ({latest_date.strftime('%d %b %Y')})"
        )
        fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Data koordinat tidak tersedia untuk ditampilkan di peta.")

# 3. TABEL DATA DETAIL
with st.expander("📋 Lihat Data Mentah"):
    st.dataframe(
        df_filtered[['Tanggal', 'Provinsi',
                     'Harga', 'Perubahan (%)', 'Harga_Num']]
        .sort_values(by=['Tanggal', 'Harga_Num'], ascending=[False, False]),
        use_container_width=True
    )

import pandas as pd
import streamlit as st

# Load data
df = pd.read_csv("laptop_prices.csv")

# Pilih kolom yang diperlukan
df = df[["Company", "Product", "Price_euros", "Ram", "PrimaryStorage", "CPU_freq"]]
df.rename(columns={
    "Company": "Brand",
    "Product": "Laptop",
    "Price_euros": "Harga",
    "Ram": "RAM",
    "PrimaryStorage": "Storage",
    "CPU_freq": "Prosesor"
}, inplace=True)

brand_options = sorted(df["Brand"].unique())

# Sidebar input
st.sidebar.title("Filter & Bobot Kriteria")


min_ram = st.sidebar.slider("Minimum RAM (GB)", 2, 64, 8, step=2)
min_storage = st.sidebar.slider("Minimum Storage (GB)", 64, 2048, 128, step=128)
min_prosesor = st.sidebar.slider("Minimum Prosesor (GHz)", 0.5, 5.0, 1.5, step=0.1)
max_harga = st.sidebar.slider("Maximum Harga (â‚¬)", 100, 5000, 1000, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("Bobot Kriteria (Total harus = 1.0)")
w_harga = st.sidebar.slider("Bobot Harga", 0.0, 1.0, 0.4, step=0.05)
w_ram = st.sidebar.slider("Bobot RAM", 0.0, 1.0, 0.2, step=0.05)
w_storage = st.sidebar.slider("Bobot Storage", 0.0, 1.0, 0.2, step=0.05)
w_prosesor = st.sidebar.slider("Bobot Prosesor", 0.0, 1.0, 0.2, step=0.05)

selected_brands = st.sidebar.multiselect("Pilih Brand (opsional)", brand_options)

# Validasi bobot
total_bobot = w_harga + w_ram + w_storage + w_prosesor

if round(total_bobot, 2) != 1.0:
    st.error(f"âŒ Total bobot harus 1.0! Sekarang: {round(total_bobot, 2)}")
else:
    bobot = {
        "Harga": w_harga,
        "RAM": w_ram,
        "Storage": w_storage,
        "Prosesor": w_prosesor
    }

    # Filter brand
    df_selected = df.copy() if not selected_brands else df[df["Brand"].isin(selected_brands)].copy()

    # Filter spesifikasi
    df_filtered = df_selected[
        (df_selected["RAM"] >= min_ram) &
        (df_selected["Storage"] >= min_storage) &
        (df_selected["Prosesor"] >= min_prosesor) &
        (df_selected["Harga"] <= max_harga)
    ].copy()

    if df_filtered.empty:
        st.warning("âš ï¸ Tidak ada laptop yang sesuai dengan kriteria.")
    else:
        # Normalisasi dan pembobotan
        for col in ["Harga", "RAM", "Storage", "Prosesor"]:
            df_filtered[f"Norm_{col}"] = df_filtered[col] / df_filtered[col].sum()
            df_filtered[f"Bobot_{col}"] = df_filtered[f"Norm_{col}"] * bobot[col]

        # COPRAS
        df_filtered["S_plus"] = df_filtered[["Bobot_RAM", "Bobot_Storage", "Bobot_Prosesor"]].sum(axis=1)
        df_filtered["S_minus"] = df_filtered["Bobot_Harga"]
        min_s_minus = df_filtered["S_minus"].min()
        df_filtered["Q"] = df_filtered["S_plus"] + (min_s_minus / df_filtered["S_minus"]) * bobot["Harga"]
        df_filtered["Ranking"] = df_filtered["Q"].rank(ascending=False).astype(int)

        # Output
        st.subheader("Rekomendasi Laptop Berdasarkan COPRAS")
        df_result = df_filtered[["Brand", "Laptop", "Q", "Ranking"]].sort_values(by="Q", ascending=False)
        st.dataframe(df_result.reset_index(drop=True))

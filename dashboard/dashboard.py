from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ---------------------------------------------------------------- konfigurasi
st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")
sns.set_theme(style="whitegrid")

C_ACCENT = "#D1495B"
C_BLUE = "#00798C"
C_GREY = "#B8B8B8"
DAY_TYPE_COLORS = {"Hari Kerja": C_ACCENT, "Akhir Pekan/Libur": C_BLUE}
BASE = Path(__file__).parent


# ---------------------------------------------------------------- data
@st.cache_data
def load_data():
    hour = pd.read_csv(BASE / "main_data.csv", parse_dates=["dteday"])
    day = pd.read_csv(BASE / "day_data.csv", parse_dates=["dteday"])
    seg_order = ["Dini Hari (00-05)", "Pagi (06-09)", "Siang (10-15)", "Sore (16-19)", "Malam (20-23)"]
    hour["time_segment"] = pd.Categorical(hour["time_segment"], categories=seg_order, ordered=True)
    temp_order = ["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-30°C)", "Panas (>30°C)"]
    day["temp_bin"] = pd.Categorical(day["temp_bin"], categories=temp_order, ordered=True)
    return hour, day


hour_df, day_df = load_data()

# ---------------------------------------------------------------- sidebar (filter)
with st.sidebar:
    st.title("🚲 Filter")
    min_date, max_date = day_df["dteday"].min().date(), day_df["dteday"].max().date()
    date_range = st.date_input("Rentang tanggal", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)
    seasons = st.multiselect("Musim", ["Semi", "Panas", "Gugur", "Dingin"],
                             default=["Semi", "Panas", "Gugur", "Dingin"])
    st.caption("Sumber: Bike Sharing Dataset (Washington D.C., 2011-2012)")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start, end = pd.Timestamp(min_date), pd.Timestamp(max_date)

mask_h = hour_df["dteday"].between(start, end) & hour_df["season"].isin(seasons)
mask_d = day_df["dteday"].between(start, end) & day_df["season"].isin(seasons)
hour_f, day_f = hour_df[mask_h], day_df[mask_d]

# ---------------------------------------------------------------- header & ringkasan
st.title("🚲 Dashboard Analisis Bike Sharing")
st.caption("Pola penyewaan sepeda berdasarkan jam, cuaca, dan tipe pengguna")

if day_f.empty:
    st.warning("Tidak ada data pada filter yang dipilih. Ubah rentang tanggal atau musim.")
    st.stop()

peak_hour = hour_f.groupby("hr")["cnt"].mean().idxmax()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total penyewaan", f"{day_f['cnt'].sum():,.0f}")
c2.metric("Rata-rata per hari", f"{day_f['cnt'].mean():,.0f}")
c3.metric("Porsi pengguna casual", f"{day_f['casual'].sum() / day_f['cnt'].sum():.1%}")
c4.metric("Jam puncak (rata-rata)", f"{peak_hour:02d}:00")

if len(day_f) < 30:
    st.info("Rentang data kurang dari 30 hari, sehingga pola yang tampil kurang stabil.")

tab1, tab2, tab3 = st.tabs(["⏰ Pola per Jam", "🌦️ Cuaca, Musim & Suhu", "👥 Tipe Pengguna"])


def fmt_axis(ax):
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    sns.despine(ax=ax)


# ---------------------------------------------------------------- tab 1
with tab1:
    st.subheader("Pada jam berapa permintaan mencapai puncak?")
    hourly = hour_f.pivot_table(index="hr", columns="day_type", values="cnt", aggfunc="mean")

    left, right = st.columns([1.8, 1])
    with left:
        fig, ax = plt.subplots(figsize=(9, 4.8))
        for tipe in hourly.columns:
            ax.plot(hourly.index, hourly[tipe], lw=2.6, marker="o", ms=4, color=DAY_TYPE_COLORS[tipe], label=tipe)
            jam = hourly[tipe].idxmax()
            ax.annotate(f"Puncak {jam:02d}:00\n{hourly.loc[jam, tipe]:,.0f}", xy=(jam, hourly.loc[jam, tipe]),
                        xytext=(jam, hourly.loc[jam, tipe] * 1.12), ha="center", fontsize=9,
                        color=DAY_TYPE_COLORS[tipe], fontweight="bold")
        ax.set_xticks(range(0, 24, 2))
        ax.set_xlabel("Jam dalam sehari")
        ax.set_ylabel("Rata-rata penyewaan per jam")
        ax.set_ylim(0, hourly.max().max() * 1.35)
        ax.legend(frameon=False, loc="upper left")
        fmt_axis(ax)
        st.pyplot(fig)
    with right:
        seg = (hour_f.groupby(["day_type", "time_segment"], observed=True)["cnt"].mean().reset_index())
        fig, ax = plt.subplots(figsize=(5.2, 4.8))
        sns.barplot(data=seg, x="time_segment", y="cnt", hue="day_type", palette=DAY_TYPE_COLORS, ax=ax)
        for c in ax.containers:
            ax.bar_label(c, fmt="%.0f", fontsize=8, padding=2)
        ax.set_xlabel("")
        ax.set_ylabel("Rata-rata penyewaan per jam")
        ax.tick_params(axis="x", rotation=30)
        ax.legend(frameon=False, title="", fontsize=8)
        fmt_axis(ax)
        st.pyplot(fig)

    st.markdown("**Insight:** hari kerja memiliki dua puncak komuter (pagi dan sore), sedangkan akhir pekan/libur "
                "hanya satu puncak landai di siang hari. Gunakan filter di sisi kiri untuk melihat apakah pola ini "
                "berubah antar-musim.")

# ---------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Seberapa besar cuaca, musim, dan suhu memengaruhi penyewaan?")
    weather_order = ["Cerah/Berawan", "Berkabut/Mendung", "Hujan/Salju Ringan"]
    w = day_f.groupby("weathersit")["cnt"].agg(["mean", "count"]).reindex(weather_order).dropna()
    s = day_f.groupby("season")["cnt"].mean().reindex(["Semi", "Panas", "Gugur", "Dingin"]).dropna()
    t = day_f.groupby("temp_bin", observed=True)["cnt"].agg(["mean", "count"])
    t = t[t["count"] > 0]

    def bar_panel(ax, labels, values, title, extra=None, rot=0):
        low = np.argmin(values)
        colors = [C_ACCENT if i == low else C_GREY for i in range(len(values))]
        bars = ax.bar(labels, values, color=colors)
        for i, b in enumerate(bars):
            txt = f"{b.get_height():,.0f}" + (f"\n(n={extra[i]} hari)" if extra is not None else "")
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + max(values) * 0.01, txt, ha="center", fontsize=9)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.set_ylim(0, max(values) * 1.25)
        ax.tick_params(axis="x", rotation=rot)
        ax.grid(axis="x", visible=False)
        fmt_axis(ax)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    bar_panel(axes[0], list(w.index), w["mean"].values, "Kondisi cuaca", w["count"].values, 15)
    axes[0].set_ylabel("Rata-rata penyewaan harian")
    bar_panel(axes[1], list(s.index), s.values, "Musim")
    bar_panel(axes[2], [str(i) for i in t.index], t["mean"].values, "Kategori suhu", t["count"].values, 15)
    plt.tight_layout()
    st.pyplot(fig)

    if "Cerah/Berawan" in w.index and "Hujan/Salju Ringan" in w.index:
        drop = 1 - w.loc["Hujan/Salju Ringan", "mean"] / w.loc["Cerah/Berawan", "mean"]
        st.markdown(f"**Insight:** pada filter saat ini, hari hujan/salju ringan memiliki penyewaan "
                    f"**{drop:.0%} lebih rendah** dibanding hari cerah/berawan "
                    f"(n={int(w.loc['Hujan/Salju Ringan', 'count'])} hari, sampel kecil). "
                    "Suhu yang terlalu rendah dan musim dingin juga menekan permintaan.")
    else:
        st.info("Kategori cuaca pembanding tidak tersedia pada filter yang dipilih.")

# ---------------------------------------------------------------- tab 3
with tab3:
    st.subheader("Kapan pengguna casual paling aktif?")
    order = [o for o in ["Hari Kerja", "Akhir Pekan/Libur"] if o in day_f["day_type"].unique()]
    u = day_f.groupby("day_type")[["casual", "registered", "cnt"]].mean().loc[order]
    u["share"] = u["casual"] / u["cnt"] * 100

    left, right = st.columns(2)
    with left:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        x = np.arange(len(order)); wd = 0.36
        b1 = ax.bar(x - wd / 2, u["registered"], wd, color=C_BLUE, label="Registered")
        b2 = ax.bar(x + wd / 2, u["casual"], wd, color=C_ACCENT, label="Casual")
        for b in list(b1) + list(b2):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 50, f"{b.get_height():,.0f}", ha="center", fontsize=9)
        ax.set_xticks(x); ax.set_xticklabels(order)
        ax.set_ylabel("Rata-rata penyewaan harian")
        ax.set_ylim(0, u[["registered", "casual"]].max().max() * 1.2)
        ax.legend(frameon=False)
        ax.grid(axis="x", visible=False)
        fmt_axis(ax)
        st.pyplot(fig)
    with right:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        bars = ax.bar(order, u["share"], color=[C_GREY if o == "Hari Kerja" else C_ACCENT for o in order])
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8, f"{b.get_height():.1f}%",
                    ha="center", fontsize=11, fontweight="bold")
        ax.set_ylabel("Porsi pengguna casual (%)")
        ax.set_ylim(0, max(u["share"].max() * 1.3, 10))
        ax.grid(axis="x", visible=False)
        sns.despine(ax=ax)
        st.pyplot(fig)

    st.markdown("**Insight:** pengguna casual jauh lebih aktif pada akhir pekan/libur, sedangkan pengguna registered "
                "didominasi komuter di hari kerja. Akhir pekan adalah momen terbaik untuk promo konversi membership.")

st.caption("Proyek Analisis Data · Bike Sharing Dataset")

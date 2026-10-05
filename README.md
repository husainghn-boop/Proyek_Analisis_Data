# Proyek Analisis Data: Bike Sharing Dataset 🚲

Analisis data penyewaan sepeda (2011-2012) beserta dashboard interaktif Streamlit.

## Pertanyaan Bisnis
1. Pada jam berapa permintaan puncak terjadi pada hari kerja vs akhir pekan/libur?
2. Seberapa besar pengaruh cuaca, musim, dan suhu terhadap penyewaan harian?
3. Kapan pengguna casual paling aktif dan berapa porsinya?

## Struktur Direktori
```
submission
├── dashboard
│   ├── main_data.csv      # data per jam (sudah dibersihkan)
│   ├── day_data.csv       # data per hari (sudah dibersihkan)
│   └── dashboard.py
├── data
│   ├── day.csv
│   └── hour.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment

**Shell / Terminal**
```
mkdir proyek_analisis_data
cd proyek_analisis_data
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Menjalankan Dashboard
```
streamlit run dashboard/dashboard.py
```

## Catatan
- Notebook `notebook.ipynb` dijalankan dari folder `submission` (membaca `data/day.csv` dan `data/hour.csv`, lalu menyimpan data bersih ke folder `dashboard`).
- Sumber data: Bike Sharing Dataset (Fanaee-T & Gama, 2013), Capital Bikeshare Washington D.C.

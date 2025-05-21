# MrScraper - AMGR Directory Scraper

Script Python sederhana untuk melakukan web scraping pada situs [AMGR Directory](https://www.amgr.org/frm_directorySearch.cfm).

## Deskripsi

Script ini memungkinkan kamu untuk mencari informasi peternak di AMGR Directory dengan menggunakan filter seperti negara bagian (state), anggota (member), dan jenis breed. Hasilnya akan ditampilkan dalam format JSON.

## Kebutuhan

-   Python 3.6+
-   Modul Python:
    -   requests
    -   beautifulsoup4
    -   requests (untuk menggunakan fitur Natural Language)

## Instalasi

1. Pastikan Python sudah terinstal pada sistem kamu
2. Instal modul yang dibutuhkan:

```bash
pip install -r requirements.txt

# Untuk fitur Natural Language (opsional)
pip install openai
```

## Mengatur OpenAI API Key

Jika ingin menggunakan fitur Natural Language, kamu perlu mengatur OpenAI API key dengan salah satu cara berikut:

### 1. Menggunakan file .env (Direkomendasikan)

Buat file bernama `.env` di direktori yang sama dengan script, lalu tambahkan:

```
OPENAI_API_KEY=your-api-key-here
```

Pastikan kamu telah menginstal python-dotenv:

```
pip install python-dotenv
```

### 2. Menggunakan Environment Variable

#### Di Windows:

```
set OPENAI_API_KEY=your-api-key-here
```

#### Di Linux/Mac:

```
export OPENAI_API_KEY=your-api-key-here
```

Fitur Natural Language tidak akan berfungsi jika API key tidak tersedia melalui salah satu cara di atas.

## Penggunaan

### Mode Interaktif

Untuk menggunakan mode interaktif (lebih mudah untuk pemula), jalankan script tanpa argumen:

```bash
python mrscraper.py
```

Dalam mode ini, script akan:

1. Menanyakan apakah ingin mengaktifkan mode debug
2. Menanyakan apakah ingin menggunakan Natural Language
    - Jika ya, kamu dapat memasukkan perintah dalam bahasa alami
    - Script akan menganalisis perintahmu dan menerjemahkannya ke parameter pencarian
3. Jika tidak menggunakan Natural Language, script akan:
    - Meminta kamu memilih state dari daftar
    - Meminta kamu memilih member dari daftar
    - Meminta kamu memilih breed dari daftar
4. Melakukan pencarian dan menampilkan hasilnya

### Mode Command Line

Untuk pengguna yang lebih berpengalaman, script dapat dijalankan dengan parameter:

```bash
python mrscraper.py [OPSI]
```

#### Opsi yang tersedia:

-   `--state`: Filter berdasarkan negara bagian (misal: "Kansas")
-   `--member`: Filter berdasarkan anggota (misal: "Dwight Elmore")
-   `--breed`: Filter berdasarkan breed (misal: "(AR) - American Red")
-   `--debug`: Aktifkan mode debug (menyimpan file HTML di folder debug)

#### Contoh:

```bash
python mrscraper.py --state "Kansas" --member "Dwight Elmore"
```

### Mode Natural Language (NEW!)

Kamu juga dapat menggunakan perintah dalam bahasa alami untuk melakukan pencarian:

```bash
python mrscraper.py --nl "Cari peternak bernama Elmore di Kansas"
```

Untuk menggunakan fitur ini, kamu perlu:

1. Menyediakan OpenAI API key:
    - Melalui parameter: `--api-key "your-api-key-here"`
    - Atau melalui environment variable: `OPENAI_API_KEY`
    - Atau masukkan secara interaktif saat diminta

#### Contoh perintah bahasa alami:

-   "Cari peternak di Kansas"
-   "Tampilkan semua peternak dengan breed American Red"
-   "Siapa peternak bernama Dwight Elmore?"
-   "Cari peternak di Alabama yang memiliki American Black"

## Output

Output ditampilkan dalam format JSON dengan struktur:

```json
{
    "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
    "data": [
        [
            "navigate_pagination",
            "KS",
            "Dwight Elmore",
            "3TAC Ranch Genetics - 3TR",
            "(620) 899-0770",
            ""
        ],
        [
            "navigate_pagination",
            "KS",
            "Mary Powell",
            "Barnyard Weed Warriors - BWW",
            "(785) 420-0472",
            ""
        ]
    ]
}
```

## Mode Debug

Jika kamu mengalami masalah, aktifkan mode debug:

```bash
python mrscraper.py --debug
```

File debug akan disimpan di folder `debug/`:

-   `main_page.html`: HTML halaman utama
-   `response.html`: HTML hasil pencarian

## Catatan Teknis

-   Script menggunakan nama field yang benar untuk form submission: `stateID`, `memberID`, dan `breedID`
-   Script memiliki mekanisme deteksi elemen form yang fleksibel untuk menangani perubahan struktur halaman
-   Fitur Natural Language menggunakan model `gpt-4o-mini` dari OpenAI

## Automated Output Validation

Script `test_scraper.py` menyediakan pengujian otomatis untuk memverifikasi akurasi scraper. Fitur ini memungkinkan kamu memastikan bahwa scraper bekerja dengan benar dan menghasilkan output yang diharapkan.

### Cara Menjalankan Pengujian

```bash
python test_scraper.py
```

### Test Case yang Tersedia

Script pengujian mencakup 8 test case berbeda:

1. **Pencarian berdasarkan state** - Menguji kemampuan pencarian berdasarkan state (Kansas)
2. **Pencarian berdasarkan member** - Menguji kemampuan pencarian berdasarkan nama peternak (Dwight Elmore)
3. **Pencarian berdasarkan breed** - Menguji kemampuan pencarian berdasarkan jenis ternak
4. **Pencarian kombinasi parameter** - Menguji kemampuan pencarian dengan kombinasi state dan breed (Iowa dan Savanna)
5. **Pencarian dengan Natural Language** - Menguji kemampuan mengkonversi query bahasa alami ke parameter pencarian
6. **Pencarian kompleks dengan NL** - Menguji kemampuan mengkonversi query kompleks seperti "Cari peternak di IOWA dengan jenis American Savanna"
7. **Pencarian dengan parameter tidak valid** - Menguji ketahanan terhadap parameter yang tidak valid
8. **Penanganan kesalahan** - Menguji penanganan kesalahan saat terjadi masalah koneksi

### Hasil Pengujian

Hasil pengujian disimpan dalam folder `test_results/`:

-   File individual untuk setiap test case (misalnya `test_01_search_by_state.json`)
-   File ringkasan dengan statistik keseluruhan (`summary_TIMESTAMP.json`)

Setiap file hasil pengujian berisi:

-   Parameter pencarian yang digunakan
-   Waktu eksekusi
-   Contoh data hasil pencarian
-   Ekspektasi vs hasil aktual

Contoh output pengujian:

```json
{
    "test_name": "test_04_combined_search",
    "timestamp": "2025-05-17 05:07:32",
    "query_params": {
        "state": "Iowa",
        "breed": "(SA) - Savanna"
    },
    "execution_time": 0.87,
    "result_count": 6,
    "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
    "sample_data": [
        [
            "navigate_pagination",
            "IA",
            "Steve & Syrie Vicary",
            "Vicary Savanna Goats - VSG",
            "(402) 203-2165",
            ""
        ]
    ],
    "test_success": true,
    "expected_output": {
        "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
        "data": [
            [
                "navigate_pagination",
                "IA",
                "Dennis & Stacy Ratashak",
                "Ratashak Harvest Hills - RHH",
                "(703) 850-4113",
                ""
            ]
        ]
    }
}
```

## Catatan

-   Script ini dirancang hanya untuk tujuan pendidikan
-   Gunakan dengan bijak dan hormati kebijakan situs web yang diakses
-   Penggunaan fitur Natural Language memerlukan OpenAI API key yang valid

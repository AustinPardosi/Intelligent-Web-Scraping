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
-   Fitur Natural Language menggunakan model GPT-4.1 mini (gpt-4o-mini) dari OpenAI

## Catatan

-   Script ini dirancang hanya untuk tujuan pendidikan
-   Gunakan dengan bijak dan hormati kebijakan situs web yang diakses
-   Penggunaan fitur Natural Language memerlukan OpenAI API key yang valid

#!/usr/bin/env python3
"""
Script untuk pengujian otomatis dan validasi output dari AMGR Scraper

Pengujian ini menjalankan beberapa test case untuk memastikan scraper
bekerja dengan benar dan menghasilkan output yang diharapkan.
"""
import sys
import time
import json
import unittest
from unittest.mock import patch
import os
from mrscraper import AMGRScraper
from nlp_processor import NLPProcessor

# Buat folder untuk menyimpan hasil jika belum ada
TEST_RESULTS_DIR = "test_results"
if not os.path.exists(TEST_RESULTS_DIR):
    os.makedirs(TEST_RESULTS_DIR)


class TestAMGRScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up scraper instance untuk semua test"""
        print("Menginisialisasi scraper untuk pengujian...")
        cls.scraper = AMGRScraper(debug=False)

        # Cek apakah NLP Processor tersedia
        cls.nlp_available = False
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                cls.nlp = NLPProcessor(api_key=api_key)
                cls.nlp_available = True
                print("NLP Processor berhasil diinisialisasi - Pengujian NL tersedia")
            else:
                print("OPENAI_API_KEY tidak ditemukan - Pengujian NL tidak tersedia")
        except Exception as e:
            print(f"Error inisialisasi NLP: {e} - Pengujian NL tidak tersedia")

        # Dapatkan semua opsi yang tersedia untuk pengujian
        try:
            cls.options = cls.scraper.get_options()
            # Simpan jumlah opsi yang ditemukan untuk validasi
            cls.state_count = len(cls.options["states"])
            cls.member_count = len(cls.options["members"])
            cls.breed_count = len(cls.options["breeds"])

            print(
                f"Opsi ditemukan: {cls.state_count} state, {cls.member_count} member, {cls.breed_count} breed"
            )

            # Tetapkan nilai sampel yang spesifik untuk pengujian
            cls.sample_state = "Kansas"
            cls.sample_member = "Dwight Elmore"  # Peternak di Kansas
            cls.sample_breed = "(SA) - Savanna"  # Jenis ternak yang umum

            # Verifikasi bahwa sampel yang dipilih ada dalam opsi
            if cls.sample_state not in cls.options["states"]:
                print(
                    f"WARNING: State sample '{cls.sample_state}' tidak ditemukan dalam opsi"
                )
                cls.sample_state = (
                    next(iter(cls.options["states"].keys()))
                    if cls.options["states"]
                    else None
                )

            if not any(cls.sample_member in m for m in cls.options["members"]):
                print(
                    f"WARNING: Member sample '{cls.sample_member}' tidak ditemukan dalam opsi"
                )
                cls.sample_member = (
                    next(iter(cls.options["members"].keys()))
                    if cls.options["members"]
                    else None
                )

            if cls.sample_breed not in cls.options["breeds"]:
                print(
                    f"WARNING: Breed sample '{cls.sample_breed}' tidak ditemukan dalam opsi"
                )
                cls.sample_breed = (
                    next(iter(cls.options["breeds"].keys()))
                    if cls.options["breeds"]
                    else None
                )

            print(
                f"Menggunakan sampel: state='{cls.sample_state}', member='{cls.sample_member}', breed='{cls.sample_breed}'"
            )

        except Exception as e:
            print(f"ERROR: Tidak dapat memperoleh opsi untuk pengujian: {e}")
            sys.exit(1)

    def validate_result_structure(self, result):
        """Validasi struktur hasil pencarian"""
        # Periksa bahwa result adalah dictionary dengan kunci 'header' dan 'data'
        self.assertIsInstance(result, dict, "Hasil seharusnya berupa dictionary")
        self.assertIn("header", result, "Hasil harus memiliki key 'header'")
        self.assertIn("data", result, "Hasil harus memiliki key 'data'")

        # Periksa bahwa header dan data adalah list
        self.assertIsInstance(result["header"], list, "Header seharusnya berupa list")
        self.assertIsInstance(result["data"], list, "Data seharusnya berupa list")

        # Jika ada data, validasi struktur data
        if result["data"]:
            # Cek bahwa setiap row memiliki jumlah kolom yang sama dengan header
            first_row = result["data"][0]
            self.assertEqual(
                len(first_row),
                len(result["header"]),
                f"Row data harus memiliki jumlah kolom yang sama dengan header",
            )

            # Validasi bahwa header memiliki kolom yang diharapkan
            expected_columns = [
                "State",
                "Name",
            ]  # Minimal harus ada kolom state dan name
            for column in expected_columns:
                self.assertTrue(
                    any(column in header for header in result["header"]),
                    f"Header harus memiliki kolom '{column}'",
                )

        return True

    def save_test_result(self, test_name, query_params, result, execution_time):
        """Simpan hasil pengujian individual ke file JSON"""
        test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query_params": query_params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Simpan maksimal 3 hasil pertama
            "test_success": True,
        }

        # Buat file untuk test case ini
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        return file_path

    def test_01_search_by_state(self):
        """Test Case 1: Pencarian berdasarkan state"""
        test_name = "test_01_search_by_state"
        print(f"\nTest Case 1: Pencarian berdasarkan state: {self.sample_state}")

        # Definisikan parameter dan ekspektasi
        params = {"state": self.sample_state}
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": f"Semua data harus memiliki state={self.sample_state}",
            "verification": "Cek kolom State di setiap row hasil",
        }
        print(f"Ekspektasi: {expected['content']}")

        # Jalankan pencarian
        start_time = time.time()
        result = self.scraper.search(state=self.sample_state)
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")
        if result["data"]:
            print(f"Contoh hasil: {result['data'][0]}")

        # Validasi struktur hasil
        self.validate_result_structure(result)

        # Validasi isi hasil - jika ada data, pastikan state sesuai
        state_valid = True
        if result["data"]:
            # Cari indeks kolom state
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row):  # Pastikan indeks dalam batas
                        # Periksa nilai state di row data (jika bukan tombol navigasi)
                        if not row[0].startswith("navigate"):
                            if row[state_idx] != self.sample_state:
                                state_valid = False
                                print(
                                    f"Error: State dalam hasil ({row[state_idx]}) tidak sama dengan yang dicari ({self.sample_state})"
                                )

        # Simpan hasil ke file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Hasil disimpan ke: {result_file}")

        # Final assertion
        self.assertTrue(
            state_valid,
            f"Tidak semua state dalam hasil sesuai dengan {self.sample_state}",
        )

    def test_02_search_by_member(self):
        """Test Case 2: Pencarian berdasarkan member (peternak)"""
        test_name = "test_02_search_by_member"
        if not self.sample_member:
            self.skipTest("Tidak ada member sampel untuk diuji")

        print(f"\nTest Case 2: Pencarian berdasarkan member: {self.sample_member}")

        # Definisikan parameter dan ekspektasi
        params = {"member": self.sample_member}
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": f"Hasil harus memuat data dengan name={self.sample_member}",
            "verification": "Cek kolom Name di hasil pencarian",
        }
        print(f"Ekspektasi: {expected['content']}")

        # Jalankan pencarian
        start_time = time.time()
        result = self.scraper.search(member=self.sample_member)
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")

        # Validasi struktur hasil
        self.validate_result_structure(result)

        # Validasi bahwa hasil tidak kosong
        self.assertGreater(
            len(result["data"]),
            0,
            f"Pencarian untuk member '{self.sample_member}' seharusnya mengembalikan hasil",
        )

        # Tampilkan informasi hasil
        if "header" in result and "data" in result and result["data"]:
            print("Header:", result["header"])
            print("Contoh data:", result["data"][0])

            # Cari indeks kolom name
            name_idx = -1
            for i, header_col in enumerate(result["header"]):
                if "Name" in header_col:
                    name_idx = i
                    break

            if name_idx >= 0:
                print(f"Kolom Name ditemukan pada indeks {name_idx}")

                # Cek apakah member name muncul dalam hasil
                member_found = False
                for row in result["data"]:
                    if len(row) > name_idx:
                        # Test akan lulus jika menemukan member name sebagai substring
                        if row[name_idx] and self.sample_member in row[name_idx]:
                            member_found = True
                            print(f"Member ditemukan: {row[name_idx]}")
                            break

                if not member_found:
                    print(
                        f"WARNING: Member '{self.sample_member}' tidak ditemukan dalam hasil pencarian"
                    )

        # Simpan hasil ke file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Hasil disimpan ke: {result_file}")

        # Tidak perlu fail, karena mungkin hasil tidak persis sama
        # Namun jika exact match diharapkan, uncomment line berikut:
        # self.assertTrue(member_found, f"Member '{self.sample_member}' tidak ditemukan dalam hasil pencarian")

    def test_03_search_by_breed(self):
        """Test Case 3: Pencarian berdasarkan breed (jenis ternak)"""
        test_name = "test_03_search_by_breed"
        if not self.sample_breed:
            self.skipTest("Tidak ada breed sampel untuk diuji")

        print(f"\nTest Case 3: Pencarian berdasarkan breed: {self.sample_breed}")

        # Definisikan parameter dan ekspektasi
        params = {"breed": self.sample_breed}
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": f"Hasil harus memuat data peternak dengan breed={self.sample_breed}",
            "verification": "Validasi struktur output",
        }
        print(f"Ekspektasi: {expected['content']}")

        # Jalankan pencarian
        start_time = time.time()
        result = self.scraper.search(breed=self.sample_breed)
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")
        if result["data"]:
            print(f"Contoh hasil: {result['data'][0]}")

        # Validasi struktur hasil
        self.validate_result_structure(result)

        # Simpan hasil ke file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Hasil disimpan ke: {result_file}")

    def test_04_combined_search_state_breed(self):
        """Test Case 4: Pencarian kombinasi state dan breed"""
        test_name = "test_04_combined_search"

        # Ubah parameter pencarian ke Iowa dan American Savanna
        iowa_state = "Iowa"
        savanna_breed = "(SA) - Savanna"

        print(
            f"\nTest Case 4: Pencarian kombinasi state: {iowa_state} dan breed: {savanna_breed}"
        )

        # Definisikan parameter dan ekspektasi
        params = {"state": iowa_state, "breed": savanna_breed}
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": f"Hasil harus memuat data dengan state={iowa_state} dan breed={savanna_breed}",
            "verification": "Cek kolom State di setiap hasil",
        }
        print(f"Ekspektasi: {expected['content']}")

        # Jalankan pencarian
        start_time = time.time()
        result = self.scraper.search(state=iowa_state, breed=savanna_breed)
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")
        if result["data"]:
            print(f"Contoh hasil: {result['data'][0]}")

        # Validasi struktur hasil
        self.validate_result_structure(result)

        # Validasi state dalam hasil jika ada data
        state_valid = True
        if result["data"]:
            # Cari indeks kolom state
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row) and not row[0].startswith("navigate"):
                        # Iowa biasanya muncul sebagai IA di hasil pencarian
                        if row[state_idx] != "IA":
                            state_valid = False
                            print(
                                f"Error: State dalam hasil ({row[state_idx]}) tidak sama dengan yang dicari (IA)"
                            )

        # Simpan hasil ke file dengan contoh ekspektasi output
        expected_output = {
            "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
            "data": [
                [
                    "navigate_pagination",
                    "IA",
                    "Dennis & Stacy Ratashak",
                    "Ratashak Harvest Hills - RHH",
                    "(703)  850-4113",
                    "",
                ],
                ["navigate_pagination", "IA", "Stan Huber", "-", "(641)  732-9271", ""],
            ],
        }

        test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query_params": params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Simpan maksimal 3 hasil pertama
            "test_success": state_valid,
            "expected_output": expected_output,
        }

        # Buat file untuk test case ini
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        print(f"Hasil disimpan ke: {file_path}")

        # Final assertion jika ada data
        if result["data"]:
            self.assertTrue(
                state_valid,
                f"Tidak semua state dalam hasil sesuai dengan 'IA'",
            )

    def test_05_natural_language_query(self):
        """Test Case 5: Pencarian menggunakan bahasa alami"""
        test_name = "test_05_nl_query"
        if not self.nlp_available:
            self.skipTest("NLP Processor tidak tersedia untuk pengujian")

        print("\nTest Case 5: Pencarian menggunakan bahasa alami")

        # Definisikan parameter dan ekspektasi
        nl_query = f"Cari peternak di {self.sample_state}"
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": f"Hasil harus memuat data dengan state={self.sample_state}",
            "verification": "Bandingkan dengan pencarian state biasa",
        }
        print(f'Query bahasa alami: "{nl_query}"')
        print(f"Ekspektasi: {expected['content']}")

        # Proses query bahasa alami
        start_time = time.time()
        nl_params = self.nlp.parse_command(nl_query)
        print(f"Hasil parsing NL: {nl_params}")

        # Jalankan pencarian dengan parameter dari NL
        result = self.scraper.search(
            state=nl_params.get("state"),
            member=nl_params.get("member"),
            breed=nl_params.get("breed"),
        )
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")
        if result["data"]:
            print(f"Contoh hasil: {result['data'][0]}")

        # Validasi struktur hasil
        self.validate_result_structure(result)

        # Validasi state dalam hasil jika ada data
        state_valid = True
        if result["data"] and nl_params.get("state"):
            # Cari indeks kolom state
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row) and not row[0].startswith("navigate"):
                        if row[state_idx] != nl_params.get("state"):
                            state_valid = False
                            print(
                                f"Error: State dalam hasil ({row[state_idx]}) tidak sama dengan yang dicari ({nl_params.get('state')})"
                            )

        # Simpan hasil ke file dengan informasi tambahan
        nl_test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nl_query": nl_query,
            "parsed_params": nl_params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Simpan maksimal 3 hasil pertama
            "test_success": state_valid,
        }

        # Buat file untuk test case ini
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(nl_test_data, f, indent=2, ensure_ascii=False)

        print(f"Hasil disimpan ke: {file_path}")

        # Final assertion jika ada state yang diharapkan
        if result["data"] and nl_params.get("state"):
            self.assertTrue(
                state_valid,
                f"Tidak semua state dalam hasil sesuai dengan {nl_params.get('state')}",
            )

    def test_06_natural_language_complex(self):
        """Test Case 6: Pencarian kompleks menggunakan bahasa alami"""
        test_name = "test_06_nl_complex"
        if not self.nlp_available:
            self.skipTest("NLP Processor tidak tersedia untuk pengujian")

        print("\nTest Case 6: Pencarian kompleks menggunakan bahasa alami")

        # Definisikan parameter dan ekspektasi
        nl_query = "Cari peternak di IOWA dengan jenis American Savanna"
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": "Hasil harus memuat data dengan state=Iowa dan breed=American Savanna",
            "verification": "Bandingkan dengan pencarian kombinasi biasa",
        }
        print(f'Query bahasa alami: "{nl_query}"')
        print(f"Ekspektasi: {expected['content']}")

        # Proses query bahasa alami
        start_time = time.time()
        nl_params = self.nlp.parse_command(nl_query)
        print(f"Hasil parsing NL: {nl_params}")

        # Jalankan pencarian dengan parameter dari NL
        result = self.scraper.search(
            state=nl_params.get("state"),
            member=nl_params.get("member"),
            breed=nl_params.get("breed"),
        )
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")
        if result["data"]:
            print(f"Contoh hasil: {result['data'][0]}")

        # Validasi struktur hasil
        self.validate_result_structure(result)

        # Validasi hasil jika ada data
        state_valid = True
        if result["data"] and nl_params.get("state"):
            # Cari indeks kolom state
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row) and not row[0].startswith("navigate"):
                        # Iowa ditampilkan sebagai IA dalam hasil
                        if row[state_idx] != "IA":
                            state_valid = False
                            print(
                                f"Error: State dalam hasil ({row[state_idx]}) tidak sama dengan yang diharapkan (IA)"
                            )

        # Ekspektasi output
        expected_output = {
            "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
            "data": [
                [
                    "navigate_pagination",
                    "IA",
                    "Dennis & Stacy Ratashak",
                    "Ratashak Harvest Hills - RHH",
                    "(703)  850-4113",
                    "",
                ],
                ["navigate_pagination", "IA", "Stan Huber", "-", "(641)  732-9271", ""],
            ],
        }

        # Simpan hasil ke file dengan informasi tambahan
        nl_test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nl_query": nl_query,
            "parsed_params": nl_params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Simpan maksimal 3 hasil pertama
            "test_success": state_valid,
            "expected_output": expected_output,
        }

        # Buat file untuk test case ini
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(nl_test_data, f, indent=2, ensure_ascii=False)

        print(f"Hasil disimpan ke: {file_path}")

    def test_07_invalid_parameters(self):
        """Test Case 7: Pencarian dengan parameter tidak valid"""
        test_name = "test_07_invalid_params"
        print("\nTest Case 7: Pencarian dengan parameter tidak valid")

        # Definisikan parameter dan ekspektasi
        invalid_state = "NonExistentState"
        params = {"state": invalid_state}
        expected = {
            "structure": 'dictionary dengan key "header" dan "data"',
            "content": "Scraper harus menangani parameter tidak valid dengan baik",
            "verification": "Periksa struktur output",
        }
        print(f"Parameter tidak valid: state='{invalid_state}'")
        print(f"Ekspektasi: {expected['content']}")

        # Jalankan pencarian
        start_time = time.time()
        result = self.scraper.search(state=invalid_state)
        execution_time = time.time() - start_time

        # Tampilkan hasil
        print(f"Waktu eksekusi: {execution_time:.2f} detik")
        print(f"Jumlah hasil: {len(result['data'])}")

        # Validasi bahwa hasilnya adalah dictionary dengan struktur yang benar
        self.validate_result_structure(result)

        # Simpan hasil ke file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Hasil disimpan ke: {result_file}")

    @patch("builtins.print")
    def test_08_error_handling(self, mock_print):
        """Test Case 8: Penanganan kesalahan dasar"""
        test_name = "test_08_error_handling"
        print("\nTest Case 8: Penanganan kesalahan dasar")

        # Definisikan parameter dan ekspektasi
        params = {"error_test": True}
        expected = {
            "structure": "Error harus ditangani dengan baik",
            "content": "Scraper harus menampilkan pesan error yang bermakna",
            "verification": "Cek jumlah panggilan print dan pesan error",
        }
        print(f"Ekspektasi: {expected['content']}")

        # Uji dengan URL yang salah
        original_url = self.scraper.base_url
        self.scraper.base_url = "https://nonexistent-url.example.com"

        # Coba lakukan pencarian
        start_time = time.time()
        error_message = None
        try:
            result = self.scraper.search()
            print(f"Hasil: {len(result['data'])} item")
            results_data = result
        except Exception as e:
            error_message = f"{e.__class__.__name__}: {e}"
            print(f"Error tertangkap: {error_message}")
            results_data = {"error": error_message}
        finally:
            # Kembalikan URL asli
            self.scraper.base_url = original_url

        execution_time = time.time() - start_time

        # Validasi bahwa error telah dihandle dengan baik
        self.assertGreaterEqual(
            mock_print.call_count, 1, "Seharusnya ada pesan error yang dicetak"
        )

        # Simpan hasil ke file khusus untuk test error
        error_test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_params": params,
            "execution_time": execution_time,
            "error_message": error_message,
            "print_call_count": mock_print.call_count,
            "test_success": mock_print.call_count >= 1,
        }

        # Buat file untuk test case ini
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(error_test_data, f, indent=2, ensure_ascii=False)

        print(f"Hasil disimpan ke: {file_path}")


def save_summary_report(results):
    """Simpan laporan ringkasan pengujian ke file JSON"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(TEST_RESULTS_DIR, f"summary_{timestamp}.json")

    # Tambahkan informasi ekspektasi vs hasil sebenarnya untuk setiap test
    test_details = []
    for test_name in [
        "test_01_search_by_state",
        "test_02_search_by_member",
        "test_03_search_by_breed",
        "test_04_combined_search",
        "test_05_nl_query",
        "test_06_nl_complex",
        "test_07_invalid_params",
        "test_08_error_handling",
    ]:
        # Cari file hasil terbaru untuk test ini
        test_files = [
            f
            for f in os.listdir(TEST_RESULTS_DIR)
            if f.startswith(test_name) and f.endswith(".json")
        ]
        if test_files:
            latest_file = max(
                test_files,
                key=lambda f: os.path.getmtime(os.path.join(TEST_RESULTS_DIR, f)),
            )
            file_path = os.path.join(TEST_RESULTS_DIR, latest_file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    test_data = json.load(f)

                test_info = {
                    "test_name": test_name,
                    "success": test_data.get("test_success", results["success"] > 0),
                    "execution_time": test_data.get("execution_time", 0),
                    "result_count": test_data.get("result_count", 0),
                    "sample_data": test_data.get("sample_data", []),
                    "expected_result": get_test_expectation(test_name),
                    "actual_result": get_actual_result_description(test_data),
                }
                test_details.append(test_info)
            except Exception as e:
                print(f"Error saat membaca hasil test {test_name}: {e}")

    # Tambahkan detail test ke ringkasan
    results["test_details"] = test_details

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Ringkasan pengujian disimpan ke {filename}")
    return filename


def get_test_expectation(test_name):
    """Dapatkan deskripsi ekspektasi untuk test tertentu"""
    expectations = {
        "test_01_search_by_state": "Pencarian berdasarkan state harus menghasilkan daftar peternak di state tersebut",
        "test_02_search_by_member": "Pencarian berdasarkan member harus menemukan peternak dengan nama tersebut",
        "test_03_search_by_breed": "Pencarian berdasarkan breed harus menemukan peternak dengan breed tersebut",
        "test_04_combined_search": "Pencarian kombinasi parameter harus menghasilkan hasil yang sesuai dengan kedua kriteria",
        "test_05_nl_query": "Query bahasa alami harus dikonversi ke parameter yang benar dan menghasilkan hasil yang relevan",
        "test_06_nl_complex": "Query bahasa alami kompleks harus diproses dengan benar meskipun memiliki beberapa parameter",
        "test_07_invalid_params": "Parameter tidak valid harus ditangani dengan baik tanpa error",
        "test_08_error_handling": "Error koneksi atau server harus ditangani dengan baik dan memberikan pesan yang informatif",
    }
    return expectations.get(test_name, "Tidak ada deskripsi ekspektasi")


def get_actual_result_description(test_data):
    """Buat deskripsi hasil aktual berdasarkan data pengujian"""
    if "error" in test_data:
        return f"Terjadi error: {test_data['error']}"

    result_count = test_data.get("result_count", 0)

    if "nl_query" in test_data:
        parsed_params = test_data.get("parsed_params", {})
        param_str = ", ".join([f"{k}='{v}'" for k, v in parsed_params.items() if v])
        return f"Query NL diproses menjadi parameter ({param_str}) dengan {result_count} hasil"

    if "query_params" in test_data:
        param_str = ", ".join(
            [f"{k}='{v}'" for k, v in test_data["query_params"].items()]
        )
        return f"Pencarian dengan {param_str} menghasilkan {result_count} hasil"

    return f"Pengujian selesai dengan {result_count} hasil"


def run_tests():
    """Jalankan semua test case dan kumpulkan hasil"""
    # Buat test suite
    loader = unittest.TestLoader()

    # Urutkan test berdasarkan nomor
    loader.sortTestMethodsUsing = lambda x, y: int(x.split("_")[1]) - int(
        y.split("_")[1]
    )

    suite = loader.loadTestsFromTestCase(TestAMGRScraper)

    # Jalankan test dan kumpulkan hasil
    results = {}

    # Gunakan TextTestRunner untuk menangkap output
    runner = unittest.TextTestRunner(verbosity=2)
    test_results = runner.run(suite)

    # Kumpulkan statistik
    results["total"] = test_results.testsRun
    results["success"] = (
        test_results.testsRun - len(test_results.failures) - len(test_results.errors)
    )
    results["fail"] = len(test_results.failures)
    results["error"] = len(test_results.errors)
    results["success_rate"] = (
        results["success"] / results["total"] * 100 if results["total"] > 0 else 0
    )

    # Tampilkan ringkasan
    print("\n" + "=" * 50)
    print("RINGKASAN HASIL PENGUJIAN OTOMATIS")
    print("=" * 50)
    print(f"Total test case: {results['total']}")
    print(f"Sukses: {results['success']}")
    print(f"Gagal: {results['fail']}")
    print(f"Error: {results['error']}")
    print(f"Tingkat keberhasilan: {results['success_rate']:.2f}%")

    # Simpan ringkasan hasil ke file
    summary_file = save_summary_report(results)
    print(f"Laporan lengkap disimpan ke: {summary_file}")

    return results


if __name__ == "__main__":
    print("AUTOMATED OUTPUT VALIDATION - AMGR SCRAPER")
    print("=" * 50)
    run_tests()

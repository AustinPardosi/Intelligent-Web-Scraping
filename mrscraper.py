#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import argparse
import sys
import re
import os

# Import python-dotenv untuk membaca file .env
try:
    from dotenv import load_dotenv
    # Muat variabel dari file .env
    load_dotenv()
    DOTENV_LOADED = True
except ImportError:
    DOTENV_LOADED = False

# Import NLP Processor
try:
    from nlp_processor import NLPProcessor
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

class AMGRScraper:
    def __init__(self, debug=False):
        self.base_url = "https://www.amgr.org/frm_directorySearch.cfm"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.debug = debug
        
        # Buat folder debug jika belum ada
        if self.debug and not os.path.exists("debug"):
            os.makedirs("debug")
    
    def get_page_source(self):
        """Ambil source HTML dari halaman utama"""
        response = self.session.get(self.base_url, headers=self.headers)
        if self.debug:
            with open("debug/main_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Debug - HTML main page disimpan ke debug/main_page.html")
        return response.content
    
    def analyze_form_structure(self, html_content=None):
        """Analisis struktur form pada halaman"""
        if not html_content:
            html_content = self.get_page_source()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if self.debug:
            print("Debug - Analyzing form structure...")
            
            # Cek semua form di halaman
            forms = soup.find_all('form')
            print(f"Debug - Forms found: {len(forms)}")
            
            # Cek semua select di halaman
            selects = soup.find_all('select')
            print(f"Debug - Select elements found: {len(selects)}")
            for i, select in enumerate(selects):
                name = select.get('name')
                id_attr = select.get('id')
                print(f"Debug - Select #{i}: name='{name}', id='{id_attr}'")
            
            # Cek semua button di halaman
            buttons = soup.find_all('button')
            print(f"Debug - Button elements found: {len(buttons)}")
            for i, button in enumerate(buttons):
                text = button.text
                type_attr = button.get('type')
                print(f"Debug - Button #{i}: text='{text}', type='{type_attr}'")
            
            # Cek semua input di halaman
            inputs = soup.find_all('input')
            print(f"Debug - Input elements found: {len(inputs)}")
            for i, input_el in enumerate(inputs):
                name = input_el.get('name')
                type_attr = input_el.get('type')
                print(f"Debug - Input #{i}: name='{name}', type='{type_attr}'")
        
        # Cari elemen form berdasarkan atribut dan konten
        form_elements = {
            'state_select': None,
            'member_select': None,
            'breed_select': None,
            'submit_input': None
        }
        
        # Cari semua select
        for select in soup.find_all('select'):
            select_name = select.get('name', '')
            select_id = select.get('id', '')
            
            if select_name == 'stateID' or 'state' in select_id.lower():
                form_elements['state_select'] = select
                if self.debug:
                    print(f"Debug - Found state select: {select_name}")
            elif select_name == 'memberID' or any(keyword in select_id.lower() for keyword in ['member', 'breeder']):
                form_elements['member_select'] = select
                if self.debug:
                    print(f"Debug - Found member select: {select_name}")
            elif select_name == 'breedID' or 'breed' in select_id.lower():
                form_elements['breed_select'] = select
                if self.debug:
                    print(f"Debug - Found breed select: {select_name}")
        
        # Cari tombol submit
        for input_el in soup.find_all('input'):
            if input_el.get('type') == 'submit':
                form_elements['submit_input'] = input_el
                if self.debug:
                    print(f"Debug - Found submit button: input[type='submit']")
                break
        
        # Jika tidak ditemukan, cari input dengan nama submitButton
        if not form_elements['submit_input']:
            for input_el in soup.find_all('input'):
                if input_el.get('name') == 'submitButton':
                    form_elements['submit_input'] = input_el
                    if self.debug:
                        print(f"Debug - Found submit button: input[name='submitButton']")
                    break
        
        # Jika tidak ditemukan, cari button dengan teks submit/search
        if not form_elements['submit_input']:
            for button in soup.find_all('button'):
                button_text = button.text.lower()
                if any(keyword in button_text for keyword in ['submit', 'search', 'find']):
                    form_elements['submit_input'] = button
                    if self.debug:
                        print(f"Debug - Found submit button with text: {button_text}")
                    break
        
        if self.debug:
            print(f"Debug - Form elements found: state={form_elements['state_select'] is not None}, member={form_elements['member_select'] is not None}, breed={form_elements['breed_select'] is not None}, submit={form_elements['submit_input'] is not None}")
        
        return form_elements
    
    def get_options(self):
        """Ambil daftar pilihan untuk state, member, dan breed"""
        html_content = self.get_page_source()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Analisis struktur form
        form_elements = self.analyze_form_structure(html_content)
        
        states = {}
        members = {}
        breeds = {}
        
        # Dapatkan daftar state
        state_select = form_elements['state_select']
        if state_select:
            for option in state_select.find_all('option')[1:]:  # Skip pertama (-- Select State --)
                option_text = option.text.strip()
                if option_text and not option_text.startswith("-- Select"):
                    states[option_text] = option.get('value')
        
        # Dapatkan daftar member
        member_select = form_elements['member_select']
        if member_select:
            for option in member_select.find_all('option')[1:]:  # Skip pertama (-- Select Member --)
                option_text = option.text.strip()
                if option_text and not option_text.startswith("-- Select"):
                    members[option_text] = option.get('value')
        
        # Dapatkan daftar breed
        breed_select = form_elements['breed_select']
        if breed_select:
            for option in breed_select.find_all('option')[1:]:  # Skip pertama (-- Select Breed --)
                option_text = option.text.strip()
                if option_text and not option_text.startswith("-- Select"):
                    breeds[option_text] = option.get('value')
        
        if self.debug:
            print(f"Debug - States found: {len(states)}")
            print(f"Debug - Members found: {len(members)}")
            print(f"Debug - Breeds found: {len(breeds)}")
            
            # Print a few examples
            if states:
                print(f"Debug - Example states: {list(states.items())[:3]}")
            if members:
                print(f"Debug - Example members: {list(members.items())[:3]}")
            if breeds:
                print(f"Debug - Example breeds: {list(breeds.items())[:3]}")
        
        return {
            'states': states,
            'members': members,
            'breeds': breeds
        }
    
    def search(self, state=None, member=None, breed=None):
        """Lakukan pencarian dengan filter yang disediakan"""
        # Cek parameter yang diberikan
        if not state and not member and not breed:
            if self.debug:
                print("Debug - No search parameters provided")
            return {"header": [], "data": []}
        
        # Dapatkan opsi tersedia beserta form elements
        options = self.get_options()
        form_elements = self.analyze_form_structure()
        
        # Buat form data
        data = {}
        
        # Cari nilai state
        if state and options['states']:
            # Cek state langsung
            if state in options['states']:
                data['stateID'] = options['states'][state]
                if self.debug:
                    print(f"Debug - Using state value: {state} -> {options['states'][state]}")
            else:
                # Cari state berdasarkan substring
                matched = False
                for state_name, state_value in options['states'].items():
                    if state.lower() in state_name.lower():
                        data['stateID'] = state_value
                        if self.debug:
                            print(f"Debug - Found state by partial match: {state} -> {state_name} ({state_value})")
                        matched = True
                        break
                
                if not matched and self.debug:
                    print(f"Debug - State '{state}' not found in available options")
        
        # Cari nilai member
        if member and options['members']:
            # Cek member langsung
            if member in options['members']:
                data['memberID'] = options['members'][member]
                if self.debug:
                    print(f"Debug - Using member value: {member} -> {options['members'][member]}")
            else:
                # Cari member berdasarkan substring
                matched = False
                for member_name, member_value in options['members'].items():
                    if member.lower() in member_name.lower():
                        data['memberID'] = member_value
                        if self.debug:
                            print(f"Debug - Found member by partial match: {member} -> {member_name} ({member_value})")
                        matched = True
                        break
                
                if not matched and self.debug:
                    print(f"Debug - Member '{member}' not found in available options")
        
        # Cari nilai breed
        if breed and options['breeds']:
            # Cek breed langsung
            if breed in options['breeds']:
                data['breedID'] = options['breeds'][breed]
                if self.debug:
                    print(f"Debug - Using breed value: {breed} -> {options['breeds'][breed]}")
            else:
                # Cari breed berdasarkan substring
                matched = False
                for breed_name, breed_value in options['breeds'].items():
                    if breed.lower() in breed_name.lower():
                        data['breedID'] = breed_value
                        if self.debug:
                            print(f"Debug - Found breed by partial match: {breed} -> {breed_name} ({breed_value})")
                        matched = True
                        break
                
                if not matched and self.debug:
                    print(f"Debug - Breed '{breed}' not found in available options")
        
        # Jika tidak ada filter yang berhasil ditambahkan, 
        # pastikan form tetap terkirim
        if not data:
            data = {'submit': 'Submit'}
        
        # Tambahkan nilai submit button jika ada
        submit_input = form_elements.get('submit_input')
        if submit_input and submit_input.get('name'):
            submit_name = submit_input.get('name')
            submit_value = submit_input.get('value', 'Submit')
            data[submit_name] = submit_value
            if self.debug:
                print(f"Debug - Adding submit button: {submit_name}={submit_value}")
        
        if self.debug:
            print(f"\nDebug - Data yang dikirim: {data}")
        
        # Kirim request
        response = self.session.post(self.base_url, data=data, headers=self.headers)
        
        if self.debug:
            print(f"Debug - Status code: {response.status_code}")
            print(f"Debug - Response URL: {response.url}")
            with open("debug/response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Debug - HTML response disimpan ke debug/response.html")
        
        # Parse hasil search
        results = self._parse_results(response.content)
        return results
    
    def _parse_results(self, html_content):
        """Parse hasil pencarian dari HTML untuk mencari tabel hasil"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Cari semua tabel di halaman
        tables = soup.find_all('table')
        if self.debug:
            print(f"Debug - Tables found: {len(tables)}")
        
        # Coba temukan tabel hasil
        result_table = None
        for i, table in enumerate(tables):
            # Cek apakah tabel ini berisi data yang relevan
            table_text = table.get_text()
            if self.debug:
                print(f"Debug - Table #{i} text preview: {table_text[:100]}...")
            
            # Mencari tabel yang berisi konten yang relevan
            if any(keyword in table_text.lower() for keyword in ['name', 'state', 'phone', 'farm']):
                result_table = table
                if self.debug:
                    print(f"Debug - Found result table #{i}")
                break
        
        # Jika tidak menemukan tabel dengan cara di atas, ambil tabel pertama jika ada
        if not result_table and tables:
            result_table = tables[0]
            if self.debug:
                print("Debug - Using first table as result table")
        
        # Jika tidak ada tabel, kembalikan hasil kosong
        if not result_table:
            if self.debug:
                print("Debug - No result table found")
            return {"header": [], "data": []}
        
        # Parse header
        headers = []
        header_row = result_table.find('thead')
        if header_row:
            # Ada thead, cari th di dalamnya
            header_cells = header_row.find_all('th')
            if header_cells:
                headers = [cell.get_text().strip() for cell in header_cells]
        
        # Jika tidak menemukan header di thead, cari di baris pertama
        if not headers:
            first_row = result_table.find('tr')
            if first_row:
                # Cari th di baris pertama
                header_cells = first_row.find_all('th')
                if header_cells:
                    headers = [cell.get_text().strip() for cell in header_cells]
                    # Skip baris ini saat mengambil data
                    rows = result_table.find_all('tr')[1:]
                else:
                    # Jika tidak ada th, mungkin td di baris pertama adalah header
                    header_cells = first_row.find_all('td')
                    if header_cells:
                        headers = [cell.get_text().strip() for cell in header_cells]
                        # Skip baris ini saat mengambil data
                        rows = result_table.find_all('tr')[1:]
            else:
                rows = result_table.find_all('tr')
        else:
            # Jika header sudah ditemukan di thead, ambil semua baris di tbody
            tbody = result_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # Jika tidak ada tbody, ambil semua tr kecuali yang pertama
                rows = result_table.find_all('tr')[1:]
        
        # Jika masih tidak ada header, gunakan default
        if not headers:
            if self.debug:
                print("Debug - Using default headers")
            headers = ["State", "Name", "Farm", "Phone", "Website"]
        
        # Parse data
        data = []
        for row in rows:
            cells = row.find_all('td')
            if cells:
                row_data = [cell.get_text().strip() for cell in cells]
                # Hanya tambahkan jika row data tidak kosong
                if any(cell for cell in row_data):
                    # Jika kolom pertama adalah Action dan nilainya kosong, isi dengan "navigate_pagination"
                    if headers and headers[0] == "Action" and (not row_data[0] or row_data[0] == ""):
                        row_data[0] = "navigate_pagination"
                    data.append(row_data)
        
        if self.debug:
            print(f"Debug - Headers found: {headers}")
            print(f"Debug - Data rows found: {len(data)}")
            if data:
                print(f"Debug - Sample data row: {data[0]}")
        
        return {
            "header": headers,
            "data": data
        }

def interactive_mode():
    """Mode interaktif untuk script"""
    print("=" * 50)
    print("MrScraper - AMGR Directory Scraper [Mode Interaktif]")
    print("=" * 50)
    
    # Aktifkan mode debug
    debug_mode = input("\nAktifkan mode debug? (y/n, default=n): ").lower().strip() == 'y'
    
    # Tanyakan apakah ingin menggunakan mode natural language
    use_nl = input("\nGunakan mode Natural Language? (y/n, default=n): ").lower().strip() == 'y'
    
    scraper = AMGRScraper(debug=debug_mode)
    
    print(f"\nLink: {scraper.base_url}")
    
    selected_state = None
    selected_member = None
    selected_breed = None
    
    if use_nl:
        # Cek apakah NLP tersedia
        if not NLP_AVAILABLE:
            print("Error: Fitur bahasa alami tidak tersedia. Pastikan nlp_processor.py ada dan dependensi terpenuhi.")
            print("Melanjutkan dengan mode interaktif reguler...")
        else:
            try:
                # Dapatkan API key dari environment variable
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    print("\nError: OPENAI_API_KEY tidak ditemukan di environment variables.")
                    
                    if not DOTENV_LOADED:
                        print("Catatan: Modul python-dotenv tidak terinstal atau gagal dimuat.")
                        print("Instal dengan: pip install python-dotenv")
                    
                    print("\nUntuk menggunakan fitur natural language, harap atur environment variable terlebih dahulu")
                    print("atau buat file .env dengan format:")
                    print("OPENAI_API_KEY=your-api-key-here")
                    print("\nContoh setting environment variable:")
                    print("  Untuk Windows: set OPENAI_API_KEY=your-api-key-here")
                    print("  Untuk Linux/Mac: export OPENAI_API_KEY=your-api-key-here")
                    print("\nMelanjutkan dengan mode interaktif reguler...")
                    use_nl = False
                
                if use_nl:
                    # Inisialisasi NLP processor
                    processor = NLPProcessor(api_key=api_key)
                    
                    # Minta input natural language
                    nl_query = input("\nMasukkan perintah pencarian dalam bahasa alami: ")
                    if nl_query.strip():
                        print(f"\nMenganalisis perintah: \"{nl_query}\"")
                        params = processor.parse_command(nl_query)
                        
                        # Set parameter dari hasil analisis
                        selected_state = params.get('state')
                        selected_member = params.get('member')
                        selected_breed = params.get('breed')
                        
                        print("\nHasil analisis:")
                        print(f"- State: {selected_state or 'tidak dispesifikasikan'}")
                        print(f"- Member: {selected_member or 'tidak dispesifikasikan'}")
                        print(f"- Breed: {selected_breed or 'tidak dispesifikasikan'}")
                        
                        # Konfirmasi hasil analisis
                        confirm = input("\nGunakan parameter ini? (y/n, default=y): ").lower().strip()
                        if confirm and confirm != 'y':
                            print("Melanjutkan dengan mode interaktif reguler...")
                            use_nl = False
                    else:
                        print("Perintah kosong. Melanjutkan dengan mode interaktif reguler...")
                        use_nl = False
            except Exception as e:
                print(f"Error saat memproses perintah bahasa alami: {e}")
                print("Melanjutkan dengan mode interaktif reguler...")
                use_nl = False
    
    # Jika tidak menggunakan natural language atau ada error, gunakan flow interaktif reguler
    if not use_nl:
        # Dapatkan opsi yang tersedia
        print("\nMengambil opsi yang tersedia dari situs...")
        options = scraper.get_options()
        
        # State selection
        print("\n--- Pilih State ---")
        states = list(options['states'].keys())
        for i, state in enumerate(states, 1):
            print(f"{i}. {state}")
        
        state_choice = input("\nPilih state (nomor atau nama, kosongkan untuk skip): ")
        
        if state_choice.strip():
            # Cek jika input adalah angka
            if state_choice.isdigit():
                idx = int(state_choice) - 1
                if 0 <= idx < len(states):
                    selected_state = states[idx]
                    print(f"Command: Select State: \"{selected_state}\"")
            # Cek jika input adalah nama state
            else:
                selected_state = state_choice
                print(f"Command: Select State: \"{selected_state}\"")
        
        # Member selection
        print("\n--- Pilih Member ---")
        members = list(options['members'].keys())
        for i, member in enumerate(members, 1):
            print(f"{i}. {member}")
        
        member_choice = input("\nPilih member (nomor atau nama, kosongkan untuk skip): ")
        
        if member_choice.strip():
            # Cek jika input adalah angka
            if member_choice.isdigit():
                idx = int(member_choice) - 1
                if 0 <= idx < len(members):
                    selected_member = members[idx]
                    print(f"Command: Select Member: \"{selected_member}\"")
            # Cek jika input adalah nama member
            else:
                selected_member = member_choice
                print(f"Command: Select Member: \"{selected_member}\"")
        
        # Breed selection
        print("\n--- Pilih Breed ---")
        breeds = list(options['breeds'].keys())
        for i, breed in enumerate(breeds, 1):
            print(f"{i}. {breed}")
        
        breed_choice = input("\nPilih breed (nomor atau nama, kosongkan untuk skip): ")
        
        if breed_choice.strip():
            # Cek jika input adalah angka
            if breed_choice.isdigit():
                idx = int(breed_choice) - 1
                if 0 <= idx < len(breeds):
                    selected_breed = breeds[idx]
                    print(f"Command: Select Breed: \"{selected_breed}\"")
            # Cek jika input adalah nama breed
            else:
                selected_breed = breed_choice
                print(f"Command: Select Breed: \"{selected_breed}\"")
    
    # Lakukan pencarian
    print("\nMelakukan pencarian...")
    results = scraper.search(selected_state, selected_member, selected_breed)
    
    # Tampilkan hasil
    print("\nHasil pencarian:")
    print(json.dumps(results, indent=2))

def main():
    # Cek apakah ada argumen yang diberikan
    if len(sys.argv) == 1:
        # Jika tidak ada argumen, jalankan mode interaktif
        interactive_mode()
        return
    
    # Jika ada argumen lain, jalankan mode command line seperti biasa
    parser = argparse.ArgumentParser(description='AMGR Directory Scraper')
    parser.add_argument('--state', type=str, help='State filter')
    parser.add_argument('--member', type=str, help='Member filter')
    parser.add_argument('--breed', type=str, help='Breed filter')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Tambahkan opsi untuk Natural Language Processing
    parser.add_argument('--nl', '--natural-language', type=str, dest='nl_query', 
                        help='Perintah pencarian dalam bahasa alami')
    
    args = parser.parse_args()
    
    # Proses perintah bahasa alami jika ada
    if args.nl_query:
        if not NLP_AVAILABLE:
            print("Error: Fitur bahasa alami tidak tersedia. Pastikan nlp_processor.py ada dan dependensi terpenuhi.")
            sys.exit(1)
        
        try:
            # Dapatkan API key dari env
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("Error: OPENAI_API_KEY tidak ditemukan di environment variables.")
                
                if not DOTENV_LOADED:
                    print("Catatan: Modul python-dotenv tidak terinstal atau gagal dimuat.")
                    print("Instal dengan: pip install python-dotenv")
                
                print("\nUntuk menggunakan fitur natural language, harap atur environment variable terlebih dahulu")
                print("atau buat file .env dengan format:")
                print("OPENAI_API_KEY=your-api-key-here")
                print("\nContoh setting environment variable:")
                print("  Untuk Windows: set OPENAI_API_KEY=your-api-key-here")
                print("  Untuk Linux/Mac: export OPENAI_API_KEY=your-api-key-here")
                sys.exit(1)
            
            # Inisialisasi NLP Processor
            processor = NLPProcessor(api_key=api_key)
            
            print(f"Menganalisis perintah: \"{args.nl_query}\"")
            params = processor.parse_command(args.nl_query)
            
            # Set parameter dari hasil analisis NLP
            args.state = params.get('state')
            args.member = params.get('member')
            args.breed = params.get('breed')
            
            print("Hasil analisis:")
            print(f"- State: {args.state or 'tidak dispesifikasikan'}")
            print(f"- Member: {args.member or 'tidak dispesifikasikan'}")
            print(f"- Breed: {args.breed or 'tidak dispesifikasikan'}")
            print()
            
        except Exception as e:
            print(f"Error saat memproses perintah bahasa alami: {e}")
            print("Melanjutkan dengan parameter yang diberikan secara langsung (jika ada).")
    
    scraper = AMGRScraper(debug=args.debug)
    
    print("Insert Link:", scraper.base_url)
    
    if args.state:
        print(f"Command: Select State: \"{args.state}\"")
    if args.member:
        print(f"Command: Select Member: \"{args.member}\"")
    if args.breed:
        print(f"Command: Select Breed: \"{args.breed}\"")
    
    results = scraper.search(args.state, args.member, args.breed)
    
    # Tampilkan hasil dalam format JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main() 
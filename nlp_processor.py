import os
import json
import requests
from typing import Dict, Optional, Any

class NLPProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """
        Inisialisasi NLP Processor untuk mengubah bahasa alami ke parameter scraping
        
        Args:
            api_key: OpenAI API key. Jika None, akan mencoba mengambil dari env OPENAI_API_KEY
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key diperlukan. Berikan sebagai parameter atau atur env OPENAI_API_KEY")
        
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4.1-mini"  
        
    def parse_command(self, query: str) -> Dict[str, Any]:
        """
        Mengubah query bahasa alami menjadi parameter scraping
        
        Args:
            query: Perintah dalam bahasa alami
            
        Returns:
            Dictionary berisi parameter scraping (state, member, breed)
        """
        system_prompt = """
        Kamu adalah asisten yang membantu mengubah perintah bahasa alami menjadi parameter untuk web scraping pada website AMGR Directory.
        
        Tugas kamu adalah mengekstrak parameter berikut dari perintah pengguna:
        - state: negara bagian di AS (contoh: Kansas, Texas)
        - member: nama anggota/peternak (contoh: Dwight Elmore, Smith)
        - breed: jenis breed (contoh: American Red, Ameri-Kiko)
        
        Hasil analisis harus dalam format JSON dengan parameter: state, member, breed.
        Jika parameter tidak disebutkan dalam perintah, berikan nilai null.
        
        Contoh:
        Perintah: "Cari peternak di Texas"
        Output: {"state": "Texas", "member": null, "breed": null}
        
        Perintah: "Tampilkan semua peternak bernama Smith di Kansas"
        Output: {"state": "Kansas", "member": "Smith", "breed": null}
        
        Perintah: "Cari peternak American Red di Alabama"
        Output: {"state": "Alabama", "member": null, "breed": "American Red"}
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.2,  # Nilai rendah untuk konsistensi
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Ambil teks respons dan parse sebagai JSON
            response_text = result["choices"][0]["message"]["content"]
            
            # Coba parse langsung jika sudah dalam format JSON
            try:
                parsed_params = json.loads(response_text)
            except json.JSONDecodeError:
                # Jika bukan format JSON, coba ekstrak bagian JSON dari teks
                import re
                json_match = re.search(r'{.*}', response_text, re.DOTALL)
                if json_match:
                    parsed_params = json.loads(json_match.group(0))
                else:
                    raise ValueError(f"Tidak dapat mengekstrak JSON dari respons: {response_text}")
            
            return parsed_params
            
        except requests.exceptions.RequestException as e:
            print(f"Error saat menghubungi OpenAI API: {e}")
            return {"state": None, "member": None, "breed": None}
        except Exception as e:
            print(f"Error saat memproses respons: {e}")
            return {"state": None, "member": None, "breed": None}

    def get_api_usage(self) -> Dict[str, Any]:
        """Mendapatkan informasi penggunaan API"""
        # Implementasi sederhana untuk menampilkan penggunaan API
        return {
            "model": self.model,
            "status": "active"
        }


if __name__ == "__main__":
    # Demo sederhana untuk testing
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Masukkan perintah pencarian: ")
    
    try:
        processor = NLPProcessor()
        result = processor.parse_command(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"Error: {e}")
        print("Pastikan API key sudah diatur dengan benar") 
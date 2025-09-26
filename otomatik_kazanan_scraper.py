#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OTOMATIK KAZANAN CIKTI SCRAPER
Mevcut JSON dosyalarindan at bilgilerini alip kazanan verilerini ceker
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
import json
from datetime import datetime
import time
import logging
import re
from pathlib import Path

# Logging ayari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OtomatikKazananScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_at_id_from_link(self, profil_link):
        """
        Profil linkinden at ID'sini cikar
        /at/94723/snow-show -> 94723
        """
        try:
            match = re.search(r'/at/(\d+)/', profil_link)
            if match:
                return match.group(1)
            return None
        except:
            return None
    
    def get_winner_horse_detailed_profile(self, horse_name):
        """
        Kazanan atın detaylı profil bilgilerini çek
        """
        try:
            logging.info(f"    Kazanan at profili cekiliyor: {horse_name}")
            
            # At profilini web'den çek (bu basitleştirilmiş bir yaklaşım)
            # Gerçek uygulamada at arama API'si kullanılabilir
            
            # Şimdilik dummy data döndürelim, gerçek profil çekme sistemi eklenebilir
            profile_data = {
                'At İsmi': horse_name,
                'Son Derece': 'Profil verisi çekilemedi',
                'Son Hipodrom': 'Bilinmiyor',
                'Son Mesafe': 'Bilinmiyor',
                'Son Kilo': 'Bilinmiyor',
                'Yaş': 'Bilinmiyor',
                'Cinsiyet': 'Bilinmiyor'
            }
            
            logging.info(f"    Profil verisi hazir: {horse_name}")
            return profile_data
            
        except Exception as e:
            logging.error(f"Kazanan at profil cekme hatasi: {e}")
            return None
    
    def parse_date_from_filename(self, filename):
        """
        Dosya adından tarihi cikar ve DD-MM-YYYY formatina cevir
        istanbul_atlari_20250925.json -> 25-09-2025
        """
        try:
            match = re.search(r'(\d{8})', filename)
            if match:
                date_str = match.group(1)  # 20250925
                year = date_str[:4]        # 2025
                month = date_str[4:6]      # 09
                day = date_str[6:8]        # 25
                return f"{day}-{month}-{year}"
            return None
        except:
            return None
    
    def get_city_from_filename(self, filename):
        """
        Dosya adından sehir adini cikar
        istanbul_atlari_20250925.json -> istanbul
        """
        try:
            city_match = re.match(r'([a-z]+)_atlari_', filename)
            if city_match:
                return city_match.group(1)
            return None
        except:
            return None
    
    def get_onceki_kosu_birincisi(self, onceki_kosu_url):
        """
        Verilen onceki kosu URL'sindeki birinci atin bilgilerini cek
        """
        try:
            logging.info(f"Onceki kosu birincisi cekiliyor: {onceki_kosu_url}")
            
            response = self.session.get(onceki_kosu_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Birinci ati bul (1. siradaki at)
            table = soup.find('table', class_='kosanAtlar')
            if not table:
                logging.error(f"Sonuc tablosu bulunamadi: {onceki_kosu_url}")
                return None
            
            tbody = table.find('tbody')
            if not tbody:
                logging.error("Tablo body bulunamadi")
                return None
            
            first_row = tbody.find('tr')
            if not first_row:
                logging.error("Ilk satir bulunamadi")
                return None
            
            cells = first_row.find_all('td')
            if len(cells) < 9:
                logging.error("Yeterli hucre bulunamadi")
                return None
            
            # Birinci at bilgileri
            sira = cells[0].get_text(strip=True)
            at_ismi_cell = cells[1].find('a', class_='atisimlink')
            at_ismi = at_ismi_cell.get_text(strip=True) if at_ismi_cell else "Bilinmiyor"
            derece = cells[8].get_text(strip=True) if cells[8] else "Bilinmiyor"
            ganyan = cells[9].get_text(strip=True) if len(cells) > 9 else "Bilinmiyor"
            
            result = {
                'birinci_at_ismi': at_ismi,
                'birinci_at_derece': derece,
                'birinci_at_ganyan': ganyan,
                'url': onceki_kosu_url
            }
            
            logging.info(f"Basarili: Onceki kosu birincisi: {at_ismi} ({derece})")
            return result
            
        except Exception as e:
            logging.error(f"Hata (onceki kosu birincisi): {e}")
            return None
    
    def get_onceki_kosu_url(self, at_id):
        """
        At ID'sinden onceki kosu URL'sini cek
        """
        try:
            # At profil sayfasini cek
            profil_url = f"https://yenibeygir.com/at/{at_id}"
            logging.info(f"At profili cekiliyor: {profil_url}")
            
            response = self.session.get(profil_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Kosu gecmisi tablosunu bul (at_Yarislar class'i)
            kosu_table = soup.find('table', class_='at_Yarislar')
            if not kosu_table:
                logging.warning(f"Kosu gecmisi tablosu bulunamadi: {profil_url}")
                return None
            
            # Tablodaki tum linkleri al
            links = kosu_table.find_all('a', href=True)
            if not links:
                logging.warning(f"Kosu linkleri bulunamadi: {profil_url}")
                return None
            
            # Onceki kosu linkini bul (bugunk u kosuyu atla)
            for link in links:
                href = link.get('href', '')
                if href.startswith('/') and '/sonuclar?at=' in href:
                    # Bugunun tarihini kontrol et (25-09-2025)
                    if '25-09-2025' in href:
                        continue  # Bugunku kosu, atla
                    
                    # Onceki kosu bulundu
                    full_url = f"https://yenibeygir.com{href}"
                    logging.info(f"Onceki kosu URL'si bulundu: {full_url}")
                    return full_url
            
            logging.warning(f"Onceki kosu URL'si bulunamadi: {profil_url}")
            return None
            
        except Exception as e:
            logging.error(f"At profili cekilemedi ({at_id}): {e}")
            return None
    
    def process_json_file(self, json_filepath):
        """
        JSON dosyasini isle ve her at icin gecmis kosu kazanan verilerini cek
        """
        try:
            logging.info(f"JSON dosyasi isleniyor: {json_filepath}")
            
            # Dosyayi oku
            with open(json_filepath, 'r', encoding='utf-8') as f:
                horses = json.load(f)
            
            if not horses:
                logging.error("JSON dosyasi bos")
                return []
            
            # Dosya adından bilgileri cikar
            filename = os.path.basename(json_filepath)
            bugun_tarih = self.parse_date_from_filename(filename)
            bugun_sehir = self.get_city_from_filename(filename)
            
            if not bugun_tarih or not bugun_sehir:
                logging.error(f"Dosya adından tarih/sehir cikarilamadi: {filename}")
                return []
            
            logging.info(f"Islenen dosya: {bugun_sehir} - {bugun_tarih}")
            logging.info(f"Toplam {len(horses)} at bulundu")
            
            # Her at icin gecmis kosu kazananini cek
            results = []
            processed_past_races = {}  # Ayni gecmis kosuyu birden fazla kez cekmeyi onle
            
            for i, horse in enumerate(horses, 1):
                try:
                    at_ismi = horse.get('At İsmi', 'Bilinmiyor')
                    profil_link = horse.get('Profil Linki', '')
                    at_id = self.get_at_id_from_link(profil_link) if profil_link else None
                    kosu_no = horse.get('Koşu', '')
                    
                    logging.info(f"[{i}/{len(horses)}] Isleniyor: {at_ismi}")
                    
                    if not at_id:
                        logging.warning(f"  At ID bulunamadi, atlanıyor")
                        continue
                    
                    # Bu atin onceki kosu URL'sini al
                    onceki_kosu_url = self.get_onceki_kosu_url(at_id)
                    
                    if not onceki_kosu_url:
                        logging.warning(f"  Onceki kosu URL'si bulunamadi, atlanıyor")
                        continue
                    
                    # Cache kontrolu
                    if onceki_kosu_url in processed_past_races:
                        cached_result = processed_past_races[onceki_kosu_url].copy()
                        cached_result['at_ismi'] = at_ismi
                        cached_result['at_id'] = at_id
                        cached_result['bugun_kosu_no'] = kosu_no
                        results.append(cached_result)
                        logging.info(f"  Cache'den alindi: {onceki_kosu_url}")
                        continue
                    
                    # Bu atin onceki kosusundaki birinci ati cek
                    birinci_result = self.get_onceki_kosu_birincisi(onceki_kosu_url)
                    
                    if birinci_result:
                        # Sonuc olustur
                        result = {
                            'at_ismi': at_ismi,
                            'at_id': at_id,
                            'bugun_kosu_no': kosu_no,
                            'bugun_tarih': bugun_tarih,
                            'bugun_sehir': bugun_sehir,
                            'onceki_kosu_url': onceki_kosu_url,
                            'json_dosyasi': filename,
                            # Onceki kosunun birincisi
                            'onceki_kosu_birinci_ismi': birinci_result['birinci_at_ismi'],
                            'onceki_kosu_birinci_derece': birinci_result['birinci_at_derece'],
                            'onceki_kosu_birinci_ganyan': birinci_result['birinci_at_ganyan']
                        }
                        
                        results.append(result)
                        
                        # Cache'e kaydet
                        processed_past_races[onceki_kosu_url] = result.copy()
                        
                        logging.info(f"  Basarili: {at_ismi} -> Onceki kosu birincisi: {birinci_result['birinci_at_ismi']} ({birinci_result['birinci_at_derece']})")
                    else:
                        logging.warning(f"  Onceki kosu birincisi bulunamadi")
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    at_ismi_safe = horse.get('At İsmi', 'Bilinmiyor At') if 'horse' in locals() else 'Bilinmiyor At'
                    logging.error(f"At isleme hatasi ({at_ismi_safe}): {e}")
                    continue
            
            logging.info(f"{bugun_sehir} tamamlandi: {len(results)}/{len(horses)} at basarili")
            return results
            
        except Exception as e:
            logging.error(f"JSON dosyasi isleme hatasi: {e}")
            return []
    
    def save_to_csv(self, data, filename=None):
        """
        At gecmis kosu kazanan verilerini CSV dosyasina kaydet
        """
        if not data:
            logging.warning("Kaydedilecek veri yok")
            return False
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"at_gecmis_kazanan_cikti_{timestamp}.csv"
        
        downloads_dir = os.path.join('static', 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        filepath = os.path.join(downloads_dir, filename)
        
        if isinstance(data, dict):
            data = [data]
        
        # Belirli siralama ile basliklar
        desired_fieldnames = [
            'at_ismi', 'at_id', 'bugun_tarih', 'bugun_sehir', 'bugun_kosu_no',
            'past_tarih', 'past_hipodrom', 'past_kosu_no', 'past_derece',
            'gecmis_kazanan_at_ismi', 'gecmis_kazanan_derece', 'gecmis_kazanan_ganyan',
            'kazanan_at_son_derece', 'kazanan_at_son_hipodrom', 'kazanan_at_son_mesafe',
            'kazanan_at_son_kilo', 'kazanan_at_yas', 'kazanan_at_cinsiyet',
            'gecmis_kosu_url', 'json_dosyasi'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if data:
                    # Mevcut alanlari kullan ama istenen sirayla
                    actual_fieldnames = list(data[0].keys())
                    # Istenen siralama ile birlestir
                    fieldnames = []
                    for field in desired_fieldnames:
                        if field in actual_fieldnames:
                            fieldnames.append(field)
                    # Kalan alanlari ekle
                    for field in actual_fieldnames:
                        if field not in fieldnames:
                            fieldnames.append(field)
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            logging.info(f"CSV kaydedildi: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"CSV kaydetme hatasi: {e}")
            return False
    
    def process_all_json_files(self, data_dir='data'):
        """
        data klasorundeki tum JSON dosyalarini isle
        """
        try:
            data_path = Path(data_dir)
            if not data_path.exists():
                logging.error(f"Data klasoru bulunamadi: {data_dir}")
                return []
            
            # JSON dosyalarini bul
            json_files = list(data_path.glob('*_atlari_*.json'))
            
            if not json_files:
                logging.error(f"JSON dosyasi bulunamadi: {data_dir}")
                return []
            
            logging.info(f"{len(json_files)} JSON dosyasi bulundu")
            
            all_results = []
            
            for json_file in json_files:
                logging.info(f"\n{'='*50}")
                logging.info(f"Isleniyor: {json_file.name}")
                
                results = self.process_json_file(str(json_file))
                all_results.extend(results)
                
                # Dosyalar arasi bekleme
                time.sleep(3)
            
            # Toplu CSV kaydet
            if all_results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"tum_dosyalar_kazanan_cikti_{timestamp}.csv"
                csv_file = self.save_to_csv(all_results, filename)
                
                # Ozet
                logging.info(f"\n{'='*50}")
                logging.info(f"TOPLU ISLEM TAMAMLANDI")
                logging.info(f"Toplam kazanan verisi: {len(all_results)}")
                logging.info(f"CSV dosyasi: {csv_file}")
                
                # Dosya bazinda ozet
                file_summary = {}
                for result in all_results:
                    json_file = result.get('json_dosyasi', 'bilinmiyor')
                    if json_file not in file_summary:
                        file_summary[json_file] = 0
                    file_summary[json_file] += 1
                
                for json_file, count in file_summary.items():
                    logging.info(f"  {json_file}: {count} kosu")
            
            return all_results
            
        except Exception as e:
            logging.error(f"Toplu islem hatasi: {e}")
            return []


def main():
    """Ana fonksiyon"""
    print("OTOMATIK KAZANAN CIKTI SCRAPER")
    print("=" * 50)
    print("Bu sistem data/ klasorundeki JSON dosyalarindan")
    print("otomatik olarak kazanan verilerini ceker.")
    print()
    
    scraper = OtomatikKazananScraper()
    
    while True:
        print("MENU:")
        print("1. Tek JSON dosyasi isle")
        print("2. Tum JSON dosyalarini isle")
        print("3. JSON dosyalarini listele")
        print("0. Cikis")
        
        choice = input("\nSeciminiz (0-3): ").strip()
        
        if choice == '0':
            print("Sistem kapatiliyor...")
            break
            
        elif choice == '1':
            # Tek dosya
            data_dir = Path('data')
            json_files = list(data_dir.glob('*_atlari_*.json'))
            
            if not json_files:
                print("JSON dosyasi bulunamadi!")
                continue
            
            print("\nMevcut JSON dosyalari:")
            for i, json_file in enumerate(json_files, 1):
                print(f"{i}. {json_file.name}")
            
            try:
                file_choice = int(input(f"\nDosya secin (1-{len(json_files)}): ")) - 1
                if 0 <= file_choice < len(json_files):
                    selected_file = json_files[file_choice]
                    print(f"\nSecilen dosya: {selected_file.name}")
                    
                    results = scraper.process_json_file(str(selected_file))
                    
                    if results:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{selected_file.stem}_kazanan_cikti_{timestamp}.csv"
                        csv_file = scraper.save_to_csv(results, filename)
                        print(f"\n{len(results)} kosu verisi cekildi")
                        print(f"CSV dosyasi: {csv_file}")
                    else:
                        print("Veri cekilemedi!")
                else:
                    print("Gecersiz secim!")
            except ValueError:
                print("Gecersiz giris!")
                
        elif choice == '2':
            # Tum dosyalar
            print("\nTum JSON dosyalari isleniyor...")
            print("Bu islem uzun surebilir!")
            
            confirm = input("Devam etmek istiyor musunuz? (y/N): ")
            if confirm.lower() == 'y':
                results = scraper.process_all_json_files()
                print(f"\nIslem tamamlandi: {len(results)} kazanan verisi cekildi")
            else:
                print("Islem iptal edildi")
                
        elif choice == '3':
            # Dosyalari listele
            data_dir = Path('data')
            json_files = list(data_dir.glob('*_atlari_*.json'))
            
            if json_files:
                print(f"\nMevcut JSON dosyalari ({len(json_files)} adet):")
                for i, json_file in enumerate(json_files, 1):
                    # Dosya bilgilerini goster
                    scraper_temp = OtomatikKazananScraper()
                    tarih = scraper_temp.parse_date_from_filename(json_file.name)
                    sehir = scraper_temp.get_city_from_filename(json_file.name)
                    
                    print(f"{i}. {json_file.name}")
                    print(f"   Sehir: {sehir}, Tarih: {tarih}")
                    
                    # At sayisini kontrol et
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            horses = json.load(f)
                            print(f"   At sayisi: {len(horses)}")
                    except:
                        print("   At sayisi: Okunamadi")
                    print()
            else:
                print("JSON dosyasi bulunamadi!")
                
        else:
            print("Gecersiz secim!")


if __name__ == "__main__":
    main()
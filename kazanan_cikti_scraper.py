#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KAZANAN CIKTI SCRAPER
At yarisi sonuclarindan kazanan atin derecesini ceker
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import time
import logging

# Logging ayari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sehir listesi
SEHIRLER = {
    '1': {'kod': 'istanbul', 'isim': 'Istanbul'},
    '2': {'kod': 'izmir', 'isim': 'Izmir'},
    '3': {'kod': 'ankara', 'isim': 'Ankara'},
    '4': {'kod': 'adana', 'isim': 'Adana'},
    '5': {'kod': 'bursa', 'isim': 'Bursa'},
    '6': {'kod': 'diyarbakir', 'isim': 'Diyarbakir'},
    '7': {'kod': 'elazig', 'isim': 'Elazig'},
    '8': {'kod': 'kocaeli', 'isim': 'Kocaeli'},
    '9': {'kod': 'sanliurfa', 'isim': 'Sanliurfa'}
}

class KazananCiktiScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_kazanan_derece(self, tarih, sehir, kosu_no, at_id):
        """
        Belirli bir at icin kazanan derecesini ceker
        
        Args:
            tarih: Yaris tarihi (DD-MM-YYYY formatinda)
            sehir: Sehir adi (izmir, istanbul, ankara vb.)
            kosu_no: Kosu numarasi
            at_id: Atin ID'si
        
        Returns:
            dict: At bilgileri ve kazanan derecesi
        """
        try:
            # URL olustur
            url = f"https://yenibeygir.com/{tarih}/{sehir}/{kosu_no}/sonuclar?at={at_id}"
            
            logging.info(f"Veri cekiliyor: {url}")
            
            # Sayfayi cek
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # HTML parse et
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Kazanan ati bul (1. siradaki at)
            table = soup.find('table', class_='kosanAtlar')
            if not table:
                logging.error("Sonuc tablosu bulunamadi")
                return None
            
            # Ilk satiri bul (kazanan at)
            tbody = table.find('tbody')
            if not tbody:
                logging.error("Tablo body bulunamadi")
                return None
            
            first_row = tbody.find('tr')
            if not first_row:
                logging.error("Ilk satir bulunamadi")
                return None
            
            # At ismini ve derecesini cek
            cells = first_row.find_all('td')
            if len(cells) < 9:
                logging.error("Yeterli hucre bulunamadi")
                return None
            
            # Sira numarasi (1. olmali)
            sira = cells[0].get_text(strip=True)
            
            # At ismi
            at_ismi_cell = cells[1].find('a', class_='atisimlink')
            at_ismi = at_ismi_cell.get_text(strip=True) if at_ismi_cell else "Bilinmiyor"
            
            # Derece (9. sutun)
            derece_cell = cells[8]
            derece = derece_cell.get_text(strip=True) if derece_cell else "Bilinmiyor"
            
            # Ganyan orani (10. sutun)
            ganyan = cells[9].get_text(strip=True) if len(cells) > 9 else "Bilinmiyor"
            
            result = {
                'tarih': tarih,
                'sehir': sehir,
                'kosu_no': kosu_no,
                'at_id': at_id,
                'kazanan_sira': sira,
                'kazanan_at_ismi': at_ismi,
                'kazanan_derece': derece,
                'kazanan_ganyan': ganyan,
                'url': url,
                'cekme_tarihi': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logging.info(f"Basarili: {at_ismi} - Sira: {sira} - Derece: {derece}")
            return result
            
        except requests.RequestException as e:
            logging.error(f"HTTP hatasi: {e}")
            return None
        except Exception as e:
            logging.error(f"Genel hata: {e}")
            return None
    
    def save_to_csv(self, data, filename=None):
        """
        Kazanan verilerini CSV dosyasina kaydet
        """
        if not data:
            logging.warning("Kaydedilecek veri yok")
            return False
        
        # Dosya adi olustur
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"kazanan_cikti_{timestamp}.csv"
        
        # Downloads klasoru yoksa olustur
        downloads_dir = os.path.join('static', 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        filepath = os.path.join(downloads_dir, filename)
        
        # Tek bir kayit ise listeye cevir
        if isinstance(data, dict):
            data = [data]
        
        # CSV'ye kaydet
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            logging.info(f"CSV kaydedildi: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"CSV kaydetme hatasi: {e}")
            return False
    
    def process_city_all_races(self, tarih, sehir, at_data_list):
        """
        Bir sehrin tum kosulari icin kazanan verilerini cek
        """
        results = []
        
        logging.info(f"{sehir.upper()} - {len(at_data_list)} kosu icin kazanan verileri cekiliyor...")
        
        for at_data in at_data_list:
            try:
                result = self.get_kazanan_derece(
                    tarih=tarih,
                    sehir=sehir,
                    kosu_no=at_data['kosu_no'],
                    at_id=at_data['at_id']
                )
                
                if result:
                    results.append(result)
                    logging.info(f"Basarili: {sehir} {at_data['kosu_no']}. kosu - Kazanan: {result['kazanan_at_ismi']}")
                else:
                    logging.warning(f"Basarisiz: {sehir} {at_data['kosu_no']}. kosu - Veri cekilemedi")
                
                # Rate limiting - sitede fazla yuk olusturmamak icin
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Kosu isleme hatasi ({sehir} {at_data['kosu_no']}): {e}")
                continue
        
        logging.info(f"{sehir.upper()} tamamlandi: {len(results)}/{len(at_data_list)} basarili")
        return results


def select_city():
    """Sehir secim menusu"""
    print("\nSEHIR SECIMI:")
    print("-" * 30)
    for key, sehir in SEHIRLER.items():
        print(f"{key}. {sehir['isim']}")
    print("0. Iptal")
    
    while True:
        secim = input("\nSehir numarasini secin (0-9): ").strip()
        
        if secim == '0':
            return None
        elif secim in SEHIRLER:
            selected = SEHIRLER[secim]
            print(f"Secildi: {selected['isim']}")
            return selected
        else:
            print("Gecersiz secim! Lutfen 0-9 arasi bir numara girin.")

def get_race_input():
    """Kosu bilgilerini kullanicidan al"""
    print("\nKOSU BILGILERI:")
    print("-" * 30)
    
    # Tarih
    while True:
        tarih = input("Yaris tarihi (DD-MM-YYYY formatinda, orn: 05-09-2025): ").strip()
        if len(tarih) == 10 and tarih.count('-') == 2:
            try:
                # Tarih formatini kontrol et
                day, month, year = tarih.split('-')
                if len(day) == 2 and len(month) == 2 and len(year) == 4:
                    break
                else:
                    print("Hatali format! DD-MM-YYYY seklinde girin.")
            except:
                print("Hatali format! DD-MM-YYYY seklinde girin.")
        else:
            print("Hatali format! DD-MM-YYYY seklinde girin.")
    
    # Kosu numarasi
    while True:
        kosu_no = input("Kosu numarasi (1-15 arasi): ").strip()
        if kosu_no.isdigit() and 1 <= int(kosu_no) <= 15:
            break
        else:
            print("Gecersiz kosu numarasi! 1-15 arasi bir sayi girin.")
    
    # At ID
    while True:
        at_id = input("At ID numarasi (orn: 94723): ").strip()
        if at_id.isdigit() and len(at_id) >= 4:
            break
        else:
            print("Gecersiz At ID! En az 4 haneli sayi girin.")
    
    return {
        'tarih': tarih,
        'kosu_no': kosu_no,
        'at_id': at_id
    }

def get_multiple_races_input():
    """Birden fazla kosu bilgisi al"""
    races = []
    
    print("\nCOKLU KOSU BILGILERI:")
    print("Her kosu icin bilgileri girin. Bitirmek icin kosu numarasina '0' yazin.")
    
    while True:
        print(f"\n--- {len(races) + 1}. Kosu ---")
        
        kosu_no = input("Kosu numarasi (1-15, bitirmek icin 0): ").strip()
        if kosu_no == '0':
            break
        
        if not kosu_no.isdigit() or not (1 <= int(kosu_no) <= 15):
            print("Gecersiz kosu numarasi!")
            continue
        
        at_id = input("At ID numarasi: ").strip()
        if not at_id.isdigit() or len(at_id) < 4:
            print("Gecersiz At ID!")
            continue
        
        races.append({'kosu_no': kosu_no, 'at_id': at_id})
        print(f"{len(races)}. kosu eklendi")
    
    return races

def test_single_race():
    """Tek kosu test - Kullanicidan bilgi al"""
    print("\nTEK KOSU TEST")
    print("=" * 40)
    
    # Sehir sec
    sehir = select_city()
    if not sehir:
        print("Islem iptal edildi")
        return
    
    # Kosu bilgilerini al
    race_info = get_race_input()
    
    print(f"\nVeri cekiliyor...")
    print(f"Sehir: {sehir['isim']}")
    print(f"Tarih: {race_info['tarih']}")
    print(f"Kosu: {race_info['kosu_no']}")
    print(f"At ID: {race_info['at_id']}")
    
    # Scraper'i calistir
    scraper = KazananCiktiScraper()
    result = scraper.get_kazanan_derece(
        tarih=race_info['tarih'],
        sehir=sehir['kod'],
        kosu_no=race_info['kosu_no'],
        at_id=race_info['at_id']
    )
    
    if result:
        print("\nBASARILI SONUC:")
        print("-" * 40)
        print(f"Kazanan At: {result['kazanan_at_ismi']}")
        print(f"Sira: {result['kazanan_sira']}")
        print(f"Derece: {result['kazanan_derece']}")
        print(f"Ganyan: {result['kazanan_ganyan']}")
        
        # CSV'ye kaydet
        csv_file = scraper.save_to_csv(result)
        print(f"\nCSV dosyasi: {csv_file}")
    else:
        print("\nVeri cekilemedi!")

def test_city_multiple_races():
    """Bir sehirin birden fazla kosusu"""
    print("\nBIR SEHIR - COKLU KOSU TEST")
    print("=" * 40)
    
    # Sehir sec
    sehir = select_city()
    if not sehir:
        print("Islem iptal edildi")
        return
    
    # Tarih al
    while True:
        tarih = input("\nYaris tarihi (DD-MM-YYYY formatinda): ").strip()
        if len(tarih) == 10 and tarih.count('-') == 2:
            break
        else:
            print("Hatali format! DD-MM-YYYY seklinde girin.")
    
    # Kosu bilgilerini al
    races = get_multiple_races_input()
    
    if not races:
        print("Hic kosu eklenmedi!")
        return
    
    print(f"\n{len(races)} kosu icin veri cekiliyor...")
    print(f"Sehir: {sehir['isim']}")
    print(f"Tarih: {tarih}")
    
    # Scraper'i calistir
    scraper = KazananCiktiScraper()
    results = scraper.process_city_all_races(tarih, sehir['kod'], races)
    
    print(f"\nSONUCLAR:")
    print("-" * 40)
    print(f"Basarili: {len(results)}/{len(races)} kosu")
    
    if results:
        # Sehir ozelinde CSV kaydet
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{sehir['kod']}_kazanan_cikti_{tarih.replace('-', '')}__{timestamp}.csv"
        csv_file = scraper.save_to_csv(results, filename)
        print(f"CSV dosyasi: {csv_file}")
        
        # Detaylari goster
        print("\nKAZANAN ATLAR:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['kosu_no']}. Kosu: {result['kazanan_at_ismi']} ({result['kazanan_derece']})")

def show_usage_guide():
    """Kullanim kilavuzu"""
    print("\nKULLANIM KILAVUZU")
    print("=" * 50)
    
    print("\nTEK KOSU VERI CEK:")
    print("- Bir yaris gununde tek bir kosunun kazanan bilgisini ceker")
    print("- Sehir, tarih, kosu no ve at ID gerekir")
    print("- Sonuc CSV dosyasina kaydedilir")
    
    print("\nBIR SEHIR - COKLU KOSU:")
    print("- Ayni sehirde ayni gun yapilan birden fazla kosu")
    print("- Her kosu icin kosu no ve at ID gerekir")
    print("- Tum sonuclar tek CSV dosyasinda birlestirilir")
    
    print("\nVERI FORMATLARI:")
    print("- Tarih: DD-MM-YYYY (orn: 05-09-2025)")
    print("- Kosu No: 1-15 arasi sayi")
    print("- At ID: En az 4 haneli sayi (orn: 94723)")
    
    print("\nSEHIRLER:")
    for key, sehir in SEHIRLER.items():
        print(f"- {sehir['isim']} ({sehir['kod']})")
    
    print("\nCSV CIKTI:")
    print("- Dosyalar: static/downloads/ klasorunde")
    print("- Icerik: Tarih, sehir, kosu no, kazanan at, derece, ganyan orani")
    
    print("\nDIKKAT:")
    print("- Site yuku olusturmamak icin aralarda bekleme var")
    print("- Cok fazla istek gondermeyin")
    print("- Gecersiz tarih/kosu no girmeyin")
    
    input("\nKilavuzu okudunuz. Devam etmek icin Enter'a basin...")

def test_scraper():
    """Ana test fonksiyonu - Interaktif menu"""
    print("KAZANAN CIKTI SCRAPER SISTEMI")
    print("=" * 50)
    print("Bu sistem at yarisi sonuclarindan kazanan verilerini ceker.")
    print("Lutfen dikkatli kullanin - site yuku olusturabilir!")
    
    while True:
        print("\n" + "=" * 50)
        print("ANA MENU:")
        print("1. Tek kosu veri cek")
        print("2. Bir sehir - Coklu kosu")
        print("3. Kullanim kilavuzu")
        print("0. Cikis")
        
        choice = input("\nSeciminiz (0-3): ").strip()
        
        if choice == '0':
            print("\nSistem kapatiliyor...")
            print("CSV dosyalari 'static/downloads' klasorunde saklandi.")
            break
        elif choice == '1':
            test_single_race()
        elif choice == '2':
            test_city_multiple_races()
        elif choice == '3':
            show_usage_guide()
        else:
            print("Gecersiz secim! Lutfen 0-3 arasi bir numara girin.")


if __name__ == "__main__":
    test_scraper()
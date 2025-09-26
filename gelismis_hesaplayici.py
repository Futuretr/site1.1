#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GELİŞTİRİLMİŞ HESAPLAMA SİSTEMİ - KAZANAN ÇIKTI DAHİL
Bu sistem tüm hesaplamaları yapar + her atın önceki koşu kazananını da ekler
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time
import os
import json
import csv
import re
import math
import logging
from pathlib import Path

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_weight(weight_str):
    """
    Kilo değerlerini normalize eder
    "50+2,0" -> "52.0"
    """
    if not weight_str or str(weight_str).strip() == '':
        return ''
    
    weight_str = str(weight_str).strip()
    
    # "50+2,0" formatını işle
    if '+' in weight_str:
        try:
            parts = weight_str.replace(',', '.').split('+')
            result = sum(float(p) for p in parts if p.strip())
            if result == int(result):
                return str(int(result))
            else:
                return str(round(result, 1))
        except Exception:
            return weight_str.replace(',', '.')
    
    # "52,5" formatını işle (virgülü noktaya çevir)
    if ',' in weight_str:
        try:
            result = float(weight_str.replace(',', '.'))
            if result == int(result):
                return str(int(result))
            else:
                return str(round(result, 1))
        except Exception:
            return weight_str
    
    # Zaten normal format
    try:
        result = float(weight_str)
        if result == int(result):
            return str(int(result))
        else:
            return str(round(result, 1))
    except:
        return weight_str

def get_horse_last_race(profil_linki, at_ismi, debug=False):
    """
    Atın son koşu verilerini geliştirilmiş algoritmla çeker
    """
    mesafe_onceki = pist_onceki = derece = kilo_onceki = son_hipodrom = ''
    
    try:
        time.sleep(0.3)
        at_url = f"https://yenibeygir.com{profil_linki}"
        at_resp = requests.get(at_url)
        at_resp.raise_for_status()
        at_soup = BeautifulSoup(at_resp.text, 'html.parser')
        
        bugun = datetime.now()
        bugun_tarih = bugun.date()
        
        # Tüm koşu satırlarını bul
        all_trs = at_soup.find_all('tr')
        tr_list = []
        
        for tr2 in all_trs:
            cells = tr2.find_all('td')
            if len(cells) > 0:
                first_cell_text = cells[0].get_text(strip=True)
                tarih_link = cells[0].find('a')
                
                tarih_text = None
                if tarih_link:
                    link_text = tarih_link.get_text(strip=True)
                    if '.' in link_text and len(link_text.split('.')) == 3:
                        tarih_text = link_text
                elif '.' in first_cell_text and len(first_cell_text.split('.')) == 3:
                    tarih_text = first_cell_text
                
                if tarih_text:
                    try:
                        date_parts = tarih_text.split('.')
                        if len(date_parts[0]) <= 2 and len(date_parts[1]) <= 2 and len(date_parts[2]) == 4:
                            tr_list.append((tarih_text, tr2))
                    except:
                        pass
        
        # Tarihe göre sırala
        tr_list_sorted = []
        for tarih_text, tr_item in tr_list:
            try:
                tarih_dt = datetime.strptime(tarih_text, '%d.%m.%Y')
                tr_list_sorted.append((tarih_dt, tr_item))
            except:
                pass
        
        tr_list_sorted.sort(reverse=True, key=lambda x: x[0])
        
        # En uygun koşuyu bul
        veri_tr = None
        for i, (tarih_dt, tr_item) in enumerate(tr_list_sorted):
            tds = tr_item.find_all('td')
            if len(tds) > 6:
                derece_val = tds[6].get_text(strip=True)
                kosu_tarih = tarih_dt.date()
                
                if kosu_tarih < bugun_tarih:
                    if derece_val and derece_val.strip():
                        gecersiz_durumlar = ['koşmaz', 'çekildi', 'düştü', 'diskalifiye', 'dns', 'dnf']
                        if derece_val.lower() not in gecersiz_durumlar:
                            if ('.' in derece_val and len(derece_val.replace('.', '')) >= 3) or derece_val.replace('.', '').isdigit():
                                veri_tr = tr_item
                                break
        
        # Veri çıkarımı
        if veri_tr:
            tds = veri_tr.find_all('td')
            if len(tds) > 10:
                mesafe_onceki = tds[3].get_text(strip=True)
                pist_onceki = tds[4].get_text(strip=True)
                derece = tds[6].get_text(strip=True)
                kilo_onceki = normalize_weight(tds[9].get_text(strip=True))
                son_hipodrom = tds[2].get_text(strip=True)
                
    except Exception as e:
        logger.warning(f"Son koşu verileri alınamadı [{at_ismi}]: {e}")
    
    return mesafe_onceki, pist_onceki, derece, kilo_onceki, son_hipodrom

def get_onceki_kosu_url(profil_url, bugun_tarih_str):
    """
    Atın profilinden önceki koşu URL'sini çıkarır
    """
    try:
        time.sleep(0.5)
        response = requests.get(profil_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # at_Yarislar tablosunu bul
        at_yarislar_table = None
        for table in soup.find_all('table'):
            if 'at_Yarislar' in str(table.get('id', '')):
                at_yarislar_table = table
                break
        
        if not at_yarislar_table:
            return None
        
        # Tüm linkleri bul
        links = at_yarislar_table.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            if '/sonuclar?' in href:
                # Bugünün tarihini kontrol et - bugünkü koşuyu atla
                if bugun_tarih_str not in href:
                    full_url = f"https://yenibeygir.com{href}"
                    return full_url
        
        return None
        
    except Exception as e:
        logger.warning(f"Önceki koşu URL'si alınamadı: {e}")
        return None

def get_onceki_kosu_birincisi(sonuc_url):
    """
    Yarış sonuç sayfasından birinci atı çıkarır
    """
    try:
        time.sleep(0.5)
        response = requests.get(sonuc_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # kosanAtlar tablosunu bul
        kosan_atlar_table = None
        for table in soup.find_all('table'):
            if 'kosanAtlar' in str(table.get('id', '')):
                kosan_atlar_table = table
                break
        
        if not kosan_atlar_table:
            return None, None, None
        
        # İlk satırı bul (birinci)
        tbody = kosan_atlar_table.find('tbody')
        if tbody:
            first_row = tbody.find('tr')
            if first_row:
                cells = first_row.find_all('td')
                if len(cells) >= 3:
                    birinci_isim = cells[1].get_text(strip=True)  # At ismi
                    birinci_derece = cells[2].get_text(strip=True)  # Derece
                    
                    # Ganyan değerini bul (genelde son sütunlarda)
                    ganyan = ""
                    if len(cells) > 10:
                        ganyan = cells[-1].get_text(strip=True)
                    
                    return birinci_isim, birinci_derece, ganyan
        
        return None, None, None
        
    except Exception as e:
        logger.warning(f"Birinci bilgisi alınamadı: {e}")
        return None, None, None

def get_kazanan_cikti(at_id, profil_linki, bugun_tarih):
    """
    Atın önceki koşusunun kazananını getirir
    """
    try:
        # Profil URL'sini oluştur
        profil_url = f"https://yenibeygir.com{profil_linki}"
        
        # Bugünün tarih string'ini oluştur (URL formatında)
        bugun_str = bugun_tarih.strftime('%d-%m-%Y')
        
        # Önceki koşu URL'sini al
        onceki_kosu_url = get_onceki_kosu_url(profil_url, bugun_str)
        
        if not onceki_kosu_url:
            return None, None, None, None
        
        # O koşunun birincisini al
        birinci_isim, birinci_derece, ganyan = get_onceki_kosu_birincisi(onceki_kosu_url)
        
        return onceki_kosu_url, birinci_isim, birinci_derece, ganyan
        
    except Exception as e:
        logger.warning(f"Kazanan çıktı alınamadı [{at_id}]: {e}")
        return None, None, None, None

class GelismisHesaplayici:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def process_json_file(self, json_file_path):
        """
        JSON dosyasını işler ve hesaplamalı + kazanan çıktılı CSV oluşturur
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                horses_data = json.load(f)
            
            if not horses_data:
                logger.warning(f"Boş JSON dosyası: {json_file_path}")
                return
            
            # Dosya bilgilerini çıkar
            file_name = Path(json_file_path).stem
            parts = file_name.split('_')
            sehir = parts[0]
            tarih_str = parts[2] if len(parts) > 2 else "20250925"
            
            # Tarihi parse et
            try:
                tarih = datetime.strptime(tarih_str, '%Y%m%d').date()
            except:
                tarih = datetime.now().date()
            
            logger.info(f"İşleniyor: {sehir} - {tarih.strftime('%d-%m-%Y')}")
            logger.info(f"Toplam {len(horses_data)} at bulundu")
            
            results = []
            
            for i, horse in enumerate(horses_data, 1):
                at_ismi = horse.get('At İsmi', 'Bilinmeyen')
                at_id = horse.get('At ID', '')
                profil_linki = horse.get('Profil Linki', '')
                kosu_no = horse.get('Koşu', '')
                
                logger.info(f"[{i}/{len(horses_data)}] İşleniyor: {at_ismi}")
                
                # Temel bilgiler
                result = {
                    'at_ismi': at_ismi,
                    'at_id': at_id,
                    'bugun_tarih': tarih.strftime('%d-%m-%Y'),
                    'bugun_sehir': sehir,
                    'bugun_kosu_no': kosu_no,
                    'json_dosyasi': Path(json_file_path).name,
                    'kilo': horse.get('Kilo', ''),
                    'jokey': horse.get('Jokey', ''),
                    'antrenor': horse.get('Antrenör', ''),
                    'sahip': horse.get('Sahip', '')
                }
                
                # Son koşu verilerini al
                if profil_linki:
                    try:
                        mesafe_onceki, pist_onceki, derece, kilo_onceki, son_hipodrom = get_horse_last_race(
                            profil_linki, at_ismi
                        )
                        
                        result.update({
                            'son_mesafe': mesafe_onceki,
                            'son_pist': pist_onceki, 
                            'son_derece': derece,
                            'son_kilo': kilo_onceki,
                            'son_hipodrom': son_hipodrom
                        })
                        
                        # Hesaplama yap
                        cikti = self.calculate_score(result, horse)
                        result['hesaplamali_cikti'] = cikti
                        
                    except Exception as e:
                        logger.warning(f"Son koşu verisi alınamadı [{at_ismi}]: {e}")
                        result.update({
                            'son_mesafe': '',
                            'son_pist': '',
                            'son_derece': '',
                            'son_kilo': '',
                            'son_hipodrom': '',
                            'hesaplamali_cikti': 'veri yok'
                        })
                
                # Kazanan çıktısını al
                if profil_linki and at_id:
                    try:
                        onceki_kosu_url, birinci_isim, birinci_derece, ganyan = get_kazanan_cikti(
                            at_id, profil_linki, tarih
                        )
                        
                        result.update({
                            'onceki_kosu_url': onceki_kosu_url or '',
                            'onceki_kosu_birinci_ismi': birinci_isim or '',
                            'onceki_kosu_birinci_derece': birinci_derece or '',
                            'onceki_kosu_birinci_ganyan': ganyan or ''
                        })
                        
                        if birinci_isim:
                            logger.info(f"  ✅ Kazanan çıktı: {birinci_isim} ({birinci_derece})")
                        else:
                            logger.warning(f"  ⚠️  Kazanan çıktı bulunamadı")
                            
                    except Exception as e:
                        logger.warning(f"Kazanan çıktı alınamadı [{at_ismi}]: {e}")
                        result.update({
                            'onceki_kosu_url': '',
                            'onceki_kosu_birinci_ismi': '',
                            'onceki_kosu_birinci_derece': '',
                            'onceki_kosu_birinci_ganyan': ''
                        })
                
                results.append(result)
                time.sleep(1)  # Rate limiting
            
            # CSV'ye kaydet
            self.save_to_csv(results, sehir, tarih)
            
            logger.info(f"✅ {sehir} işlemi tamamlandı: {len(results)} at")
            
        except Exception as e:
            logger.error(f"Dosya işlenirken hata: {e}")
    
    def calculate_score(self, result, horse_data):
        """
        Hesaplama mantığı - mevcut sistemdeki gibi
        """
        try:
            derece = result.get('son_derece', '')
            mesafe = result.get('son_mesafe', '')
            
            if not derece or not mesafe:
                return 'veri yok'
            
            # Basit hesaplama - gerçek mantığınızı buraya ekleyin
            try:
                if '.' in derece:
                    parts = derece.split('.')
                    if len(parts) >= 2:
                        dakika = float(parts[0])
                        saniye = float(parts[1] + '.' + '.'.join(parts[2:]) if len(parts) > 2 else parts[1])
                        total_seconds = dakika * 60 + saniye
                        
                        # Mesafe faktörü
                        mesafe_num = float(mesafe) if mesafe.replace('.', '').isdigit() else 1600
                        
                        # Basit skor hesaplama
                        score = (mesafe_num / total_seconds) * 100
                        return f"{score:.2f}"
                        
            except Exception:
                pass
            
            return 'hesaplanamadı'
            
        except Exception:
            return 'hata'
    
    def save_to_csv(self, results, sehir, tarih):
        """
        Sonuçları CSV'ye kaydeder
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"gelismis_{sehir}_atlari_{tarih.strftime('%Y%m%d')}_{timestamp}.csv"
            filepath = Path("static/downloads") / filename
            
            # Klasörü oluştur
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # CSV'ye yaz
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            
            logger.info(f"CSV kaydedildi: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"CSV kaydetme hatası: {e}")
            return None

def main():
    print("GELİŞTİRİLMİŞ HESAPLAMA SİSTEMİ")
    print("=" * 50)
    print("Bu sistem hem hesaplamalı hem de kazanan çıktı verileri üretir.")
    print()
    
    hesaplayici = GelismisHesaplayici()
    
    # JSON dosyalarını listele
    data_dir = Path("data")
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        print("data/ klasöründe JSON dosyası bulunamadı!")
        return
    
    print("Mevcut JSON dosyaları:")
    for i, file in enumerate(json_files, 1):
        print(f"{i}. {file.name}")
    
    print(f"\n0. Çıkış")
    print(f"99. Tümünü işle")
    
    while True:
        try:
            choice = input(f"\nSeçiminiz (0-{len(json_files)} veya 99): ").strip()
            
            if choice == '0':
                print("Çıkılıyor...")
                break
            elif choice == '99':
                print("\n🔄 Tüm dosyalar işleniyor...")
                for json_file in json_files:
                    print(f"\n📁 İşleniyor: {json_file.name}")
                    hesaplayici.process_json_file(str(json_file))
                print("\n✅ Tüm dosyalar işlendi!")
                break
            else:
                file_index = int(choice) - 1
                if 0 <= file_index < len(json_files):
                    selected_file = json_files[file_index]
                    print(f"\n📁 İşleniyor: {selected_file.name}")
                    hesaplayici.process_json_file(str(selected_file))
                    print("\n✅ İşlem tamamlandı!")
                else:
                    print("❌ Geçersiz seçim!")
                    
        except ValueError:
            print("❌ Geçerli bir numara girin!")
        except KeyboardInterrupt:
            print("\n\n⏹️  İşlem durduruldu!")
            break

if __name__ == "__main__":
    main()
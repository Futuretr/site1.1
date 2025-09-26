#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YENİ AT ÇEKME SİSTEMİ - TEMİZ VE ORTAK KOD
Tüm şehirler için ortak fonksiyon kullanır
Düzeltilmiş tarih karşılaştırması ile doğru son koşu verilerini çeker
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time
import os
import json
import re

def normalize_weight(weight_str):
    """
    Kilo değerlerini normalize eder
    "50+2,0" -> "52.0"
    "57+0,1" -> "57.1"  
    "52,5" -> "52.5"
    57 -> "57"
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
    Bugünkü koşuyu göz ardı eder ve gerçek son koşuyu bulur
    """
    mesafe_onceki = pist_onceki = derece = kilo_onceki = son_hipodrom = ''
    
    try:
        time.sleep(0.3)  # Rate limiting
        at_url = f"https://yenibeygir.com{profil_linki}"
        at_resp = requests.get(at_url)
        at_resp.raise_for_status()
        at_soup = BeautifulSoup(at_resp.text, 'html.parser')
        
        bugun = datetime.now()
        bugun_tarih = bugun.date()
        
        if debug:
            print(f"    🔍 {at_ismi} analiz ediliyor... (Bugün: {bugun_tarih.strftime('%d.%m.%Y')})")
        
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
        
        # Tarihe göre sırala (en yeni ilk)
        tr_list_sorted = []
        for tarih_text, tr_item in tr_list:
            try:
                tarih_dt = datetime.strptime(tarih_text, '%d.%m.%Y')
                tr_list_sorted.append((tarih_dt, tr_item))
            except:
                pass
        
        tr_list_sorted.sort(reverse=True, key=lambda x: x[0])
        
        if debug and tr_list_sorted:
            print(f"      📋 {len(tr_list_sorted)} koşu bulundu")
        
        # En uygun koşuyu bul - SIKI KONTROLLER
        veri_tr = None
        for i, (tarih_dt, tr_item) in enumerate(tr_list_sorted):
            tds = tr_item.find_all('td')
            if len(tds) > 6:
                derece_val = tds[6].get_text(strip=True)
                kosu_tarih = tarih_dt.date()
                
                if debug:
                    durum = "BUGÜN" if kosu_tarih == bugun_tarih else "GEÇMİŞ" if kosu_tarih < bugun_tarih else "GELECEK"
                    print(f"      {i+1}. {tarih_dt.strftime('%d.%m.%Y')} - Derece: '{derece_val}' - {durum}")
                
                # SIKI KONTROLLER
                if kosu_tarih < bugun_tarih:  # Sadece geçmiş koşular
                    if derece_val and derece_val.strip():  # Derece var mı?
                        # Geçersiz durumları filtrele
                        gecersiz_durumlar = ['koşmaz', 'çekildi', 'düştü', 'diskalifiye', 'dns', 'dnf']
                        if derece_val.lower() not in gecersiz_durumlar:
                            # Derece formatı kontrolü
                            try:
                                # Derece bir zaman formatında olmalı (1.32.91) veya sayısal
                                if ('.' in derece_val and len(derece_val.replace('.', '')) >= 3) or derece_val.replace('.', '').isdigit():
                                    if debug:
                                        print(f"      ✅ KOŞU SEÇİLDİ: {tarih_dt.strftime('%d.%m.%Y')} - Derece: {derece_val}")
                                    veri_tr = tr_item
                                    break
                                else:
                                    if debug:
                                        print(f"      ❌ Geçersiz derece formatı: '{derece_val}'")
                            except:
                                if debug:
                                    print(f"      ❌ Derece parse hatası: '{derece_val}'")
                        else:
                            if debug:
                                print(f"      ❌ Geçersiz durum: '{derece_val}'")
                    else:
                        if debug:
                            print(f"      ❌ Derece bilgisi yok")
                elif kosu_tarih == bugun_tarih:
                    if debug:
                        print(f"      ⚠️ Bugünkü koşu atlandı")
                else:
                    if debug:
                        print(f"      ⚠️ Gelecek tarihli koşu atlandı")
        
        if veri_tr:
            tds = veri_tr.find_all('td')
            
            # Hipodrom bilgisi
            if len(tds) > 1:
                son_hipodrom = tds[1].get_text(strip=True)
            
            # Pist ve mesafe bilgisi
            pist_span = (
                veri_tr.find('span', class_='kumpist') or
                veri_tr.find('span', class_='cimpist') or
                veri_tr.find('span', class_='sentetikpist')
            )
            if pist_span:
                mesafe_onceki = pist_span.get('data-mesafe', '').strip()
                pist_onceki = pist_span.get('data-pist', '').strip()
            
            # Derece bilgisi
            if len(tds) > 6:
                derece = tds[6].get_text(strip=True)
            
            # Kilo bilgisi
            if len(tds) > 10:
                kilo_span = tds[10].find('span')
                if kilo_span:
                    kilo_onceki_raw = kilo_span.get_text(strip=True)
                    kilo_onceki = normalize_weight(kilo_onceki_raw)
        else:
            if debug:
                print(f"      ❌ {at_ismi} için uygun son koşu bulunamadı")
                
    except Exception as e:
        if debug:
            print(f"      ⚠️ Hata: {at_ismi} için veri çekilemedi: {e}")
    
    return mesafe_onceki, pist_onceki, derece, kilo_onceki, son_hipodrom

def get_city_races_unified(sehir_adi, url_suffix, debug=False):
    """
    Tüm şehirler için birleşik at verisi çekme fonksiyonu
    
    Args:
        sehir_adi: Şehir adı (Türkçe)
        url_suffix: URL'de kullanılacak şehir kodu
        debug: Debug bilgilerini göster
    
    Returns:
        list: At bilgileri listesi
    """
    bugun = datetime.now()
    tarih_str = bugun.strftime('%d-%m-%Y')
    url = f"https://yenibeygir.com/{tarih_str}/{url_suffix}"
    
    if debug:
        print(f"🏇 {sehir_adi} at verileri çekiliyor: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ {sehir_adi} sayfasına erişilemedi: {e}")
        return []
        
    soup = BeautifulSoup(response.text, 'html.parser')
    horses = []
    
    for yaris_header in soup.find_all('div', class_='yarisHeader'):
        # Koşu numarası
        yaris_no_div = yaris_header.find('div', class_='yarisNo')
        kosu_no = yaris_no_div.find('span').get_text(strip=True) if yaris_no_div else ''
        
        # Mesafe ve pist bilgisi
        mesafe = ''
        pist = ''
        mesafe_pist_div = yaris_header.find('div', class_='yarisMesafePist')
        if mesafe_pist_div:
            pist_span = mesafe_pist_div.find('span', class_='kumpist')
            if not pist_span:
                pist_span = mesafe_pist_div.find('span', class_='cimpist')
            if not pist_span:
                pist_span = mesafe_pist_div.find('span', class_='sentetikpist')
            if pist_span:
                pist_mesafe_text = pist_span.get_text(strip=True)
                parts = pist_mesafe_text.split()
                if len(parts) >= 2:
                    mesafe = parts[0]
                    pist = parts[1]
                    if 'sentetik' in pist_mesafe_text.lower():
                        pist = 'Sentetik'
        
        # Atları işle
        table = yaris_header.find_next('table')
        if table:
            if debug:
                print(f"  📊 Koşu {kosu_no} işleniyor...")
                
            for tr in table.find_all('tr'):
                a = tr.find('a', class_='atisimlink')
                if not a:
                    continue
                    
                at_ismi = a.get_text(strip=True)
                profil_linki = a['href']
                
                if debug:
                    print(f"    🐎 {at_ismi}")
                
                # Jokey
                jokey = ''
                jokey_a = tr.find('a', class_='bult-black')
                if jokey_a:
                    jokey = jokey_a.get_text(strip=True)
                
                # Bugünkü kilo
                kilo = ''
                kilo_td = tr.find('td', class_='kilocell')
                if kilo_td:
                    kilo_raw = kilo_td.get_text(strip=True)
                    kilo = normalize_weight(kilo_raw)
                
                # Son koşu verilerini geliştirilmiş fonksiyonla çek
                mesafe_onceki, pist_onceki, derece, kilo_onceki, son_hipodrom = get_horse_last_race(
                    profil_linki, at_ismi, debug
                )
                
                horses.append({
                    'Koşu': kosu_no,
                    'At İsmi': at_ismi,
                    'Profil Linki': profil_linki,
                    'Jokey': jokey,
                    'Son Kilo': kilo,
                    'Son Mesafe': mesafe_onceki,
                    'Son Pist': pist_onceki,
                    'Son Derece': derece,
                    'Kilo': kilo_onceki,
                    'Bugünkü Mesafe': mesafe,
                    'Bugünkü Pist': pist,
                    'Şehir': sehir_adi,
                    'Son Hipodrom': son_hipodrom
                })
    
    if debug:
        basarili = sum(1 for h in horses if h['Son Derece'])
        oran = (basarili / len(horses) * 100) if horses else 0
        print(f"✅ {sehir_adi} - {len(horses)} at, {basarili} başarılı (%{oran:.1f})")
    
    return horses

# ŞEHİR FONKSİYONLARI - Ortak fonksiyonu kullanır
def get_adana_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Adana", "adana", debug)

def get_istanbul_races_and_horse_last_race(debug=False):
    return get_city_races_unified("İstanbul", "istanbul", debug)

def get_ankara_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Ankara", "ankara", debug)

def get_izmir_races_and_horse_last_race(debug=False):
    return get_city_races_unified("İzmir", "izmir", debug)

def get_bursa_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Bursa", "bursa", debug)

def get_kocaeli_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Kocaeli", "kocaeli", debug)

def get_sanliurfa_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Şanlıurfa", "sanliurfa", debug)

def get_diyarbakir_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Diyarbakır", "diyarbakir", debug)

def get_elazig_races_and_horse_last_race(debug=False):
    return get_city_races_unified("Elazığ", "elazig", debug)

# TOPLU İŞLEMLER
def get_all_cities_data(debug=False):
    """
    Tüm şehirlerden at verilerini çek
    """
    print("🏇 TÜM ŞEHİRLER İÇİN AT VERİLERİ ÇEKİLİYOR...")
    print("=" * 60)
    
    city_functions = [
        ("Adana", get_adana_races_and_horse_last_race),
        ("İstanbul", get_istanbul_races_and_horse_last_race),
        ("Ankara", get_ankara_races_and_horse_last_race),
        ("İzmir", get_izmir_races_and_horse_last_race),
        ("Bursa", get_bursa_races_and_horse_last_race),
        ("Kocaeli", get_kocaeli_races_and_horse_last_race),
        ("Şanlıurfa", get_sanliurfa_races_and_horse_last_race),
        ("Diyarbakır", get_diyarbakir_races_and_horse_last_race),
        ("Elazığ", get_elazig_races_and_horse_last_race)
    ]
    
    all_horses = []
    city_stats = {}
    
    for city_name, city_func in city_functions:
        try:
            horses = city_func(debug)
            all_horses.extend(horses)
            
            basarili = sum(1 for h in horses if h['Son Derece'])
            oran = (basarili / len(horses) * 100) if horses else 0
            city_stats[city_name] = {
                'toplam': len(horses),
                'basarili': basarili,
                'oran': oran
            }
            
            print(f"✅ {city_name}: {basarili}/{len(horses)} (%{oran:.1f})")
            
        except Exception as e:
            print(f"❌ {city_name} hatası: {e}")
            city_stats[city_name] = {'hata': str(e)}
    
    # Genel istatistik
    toplam_at = len(all_horses)
    toplam_basarili = sum(1 for h in all_horses if h['Son Derece'])
    genel_oran = (toplam_basarili / toplam_at * 100) if toplam_at else 0
    
    print(f"\n🏆 GENEL SONUÇ:")
    print(f"   Toplam at: {toplam_at}")
    print(f"   Başarılı: {toplam_basarili}")
    print(f"   Genel başarı oranı: %{genel_oran:.1f}")
    
    return all_horses, city_stats

def create_all_csv_files(debug=False):
    """
    Tüm şehirler için CSV dosyaları oluştur
    """
    print("📄 TÜM ŞEHİRLER İÇİN CSV DOSYALARI OLUŞTURULUYOR...")
    print("=" * 60)
    
    city_functions = [
        ("Adana", "adana_atlari_yeni.csv", get_adana_races_and_horse_last_race),
        ("İstanbul", "istanbul_atlari_yeni.csv", get_istanbul_races_and_horse_last_race),
        ("Ankara", "ankara_atlari_yeni.csv", get_ankara_races_and_horse_last_race),
        ("İzmir", "izmir_atlari_yeni.csv", get_izmir_races_and_horse_last_race),
        ("Bursa", "bursa_atlari_yeni.csv", get_bursa_races_and_horse_last_race),
        ("Kocaeli", "kocaeli_atlari_yeni.csv", get_kocaeli_races_and_horse_last_race),
        ("Şanlıurfa", "sanliurfa_atlari_yeni.csv", get_sanliurfa_races_and_horse_last_race),
        ("Diyarbakır", "diyarbakir_atlari_yeni.csv", get_diyarbakir_races_and_horse_last_race),
        ("Elazığ", "elazig_atlari_yeni.csv", get_elazig_races_and_horse_last_race)
    ]
    
    for city_name, filename, city_func in city_functions:
        try:
            print(f"\n🏇 {city_name} işleniyor...")
            horses = city_func(debug)
            
            if horses:
                df = pd.DataFrame(horses)
                df.to_csv(filename, index=False, encoding='utf-8')
                
                basarili = sum(1 for h in horses if h['Son Derece'])
                oran = (basarili / len(horses) * 100)
                
                print(f"✅ {filename} oluşturuldu - {basarili}/{len(horses)} (%{oran:.1f})")
            else:
                print(f"❌ {city_name} için veri bulunamadı")
                
        except Exception as e:
            print(f"❌ {city_name} CSV hatası: {e}")
    
    print(f"\n🎉 Tüm CSV dosyaları oluşturuldu!")

# TEST FONKSİYONU
def test_system():
    """
    Sistemi test et
    """
    print("🧪 YENİ SİSTEM TEST EDİLİYOR")
    print("=" * 50)
    
    # Sadece İstanbul'u test et
    horses = get_istanbul_races_and_horse_last_race(debug=True)
    
    if horses:
        # LOSTRA'yı kontrol et
        lostra = next((h for h in horses if 'LOSTRA' in h['At İsmi'].upper()), None)
        if lostra:
            print(f"\n🎯 LOSTRA TEST SONUCU:")
            print(f"   At: {lostra['At İsmi']}")
            print(f"   Son Derece: '{lostra['Son Derece']}'")
            print(f"   Son Hipodrom: '{lostra['Son Hipodrom']}'")
            print(f"   Son Mesafe: '{lostra['Son Mesafe']}'")
            
            if lostra['Son Derece'] == '1.49.26':
                print(f"   ✅ BAŞARILI! Doğru son koşu verisi çekildi!")
            else:
                print(f"   ⚠️ Beklenmeyen değer, kontrol edilmeli")
    
    return horses

# ========================================
# HESAPLAMA FONKSİYONLARI
# ========================================

def load_normalization_coefficients():
    """Pist bazlı ve şehir bazlı normalizasyon katsayılarını yükle"""
    pist_katsayilari = {}
    sehir_katsayilari = {
        'ankara': 1.018,
        'istanbul': 1.000,
        'izmir': 1.015,
        'bursa': 1.012,
        'adana': 1.020,
        'kocaeli': 1.010,
        'elazig': 1.025,
        'diyarbakir': 1.030,
        'sanliurfa': 1.035
    }
    return pist_katsayilari, sehir_katsayilari

PIST_KATSAYILARI, SEHIR_KATSAYILARI = load_normalization_coefficients()

def time_to_seconds(time_str):
    """Derece string'ini saniyeye çevir"""
    if not time_str or str(time_str).strip() in ['', '-', '0']:
        return 0
    
    time_str = str(time_str).strip()
    
    # Nokta sayısını kontrol et
    if time_str.count('.') == 1:
        # Format: SS.HH (saniye.salise) - 1.20.30 gibi değil
        if len(time_str.split('.')) == 2:
            parts = time_str.split('.')
            if len(parts[0]) <= 2 and len(parts[1]) <= 2:
                try:
                    seconds = int(parts[0])
                    hundredths = int(parts[1])
                    return seconds + hundredths / 100.0
                except:
                    pass
    
    # Format: M.SS.HH (dakika.saniye.salise)
    if time_str.count('.') == 2:
        parts = time_str.split('.')
        if len(parts) == 3:
            try:
                minutes = int(parts[0])
                seconds = int(parts[1])
                hundredths = int(parts[2])
                return minutes * 60 + seconds + hundredths / 100.0
            except:
                pass
    
    return 0

def calculate_average_time(run1, surface1, distance1, distance3, surface3):
    time1 = time_to_seconds(run1)
    base_time_per_100 = time1 / (distance1 / 100)
    if surface1 != surface3:
        surface_transition = {
            (2, 1): -0.30,
            (2, 3): -0.12,
            (1, 2): +0.30,
            (1, 3): +0.12,
            (3, 2): +0.12,
            (3, 1): -0.12
        }
        transition_adjustment = surface_transition.get((surface1, surface3), 0)
        new_time_per_100 = base_time_per_100 + transition_adjustment
    else:
        new_time_per_100 = base_time_per_100
    distance_diff = distance3 - distance1
    if distance_diff != 0:
        if surface3 == 1:
            distance_factor = 0.03
        elif surface3 == 2:
            distance_factor = 0.05
        elif surface3 == 3:
            distance_factor = 0.04
        else:
            distance_factor = 0
        if distance_diff > 0:
            new_time_per_100 += (distance_diff / 100) * distance_factor
        else:
            new_time_per_100 -= (abs(distance_diff) / 100) * distance_factor
    final_time = (distance3 / 100) * new_time_per_100
    return final_time

def calculate_time_per_100m(total_seconds, distance):
    num_hundreds = distance / 100
    avg_time_per_100 = total_seconds / num_hundreds
    return avg_time_per_100

def pist_to_int(pist):
    pist = pist.lower()
    if 'çim' in pist:
        return 1
    elif 'kum' in pist and 'sentetik' not in pist:
        return 2
    elif 'sentetik' in pist:
        return 3
    return 0

def get_sehir_pist_key(sehir, pist):
    """Şehir ve pist türünden anahtar oluştur"""
    if not sehir or not pist:
        return "unknown_unknown"
    
    # Şehir normalleştirme
    sehir_clean = str(sehir).lower().strip()
    
    # Unicode normalleştirme
    import unicodedata
    sehir_clean = unicodedata.normalize('NFD', sehir_clean)
    sehir_clean = ''.join(c for c in sehir_clean if not unicodedata.combining(c))
    
    # Türkçe karakterleri temizle
    replacements = {
        'ı': 'i', 'ş': 's', 'ğ': 'g', 'ü': 'u', 'ö': 'o', 'ç': 'c',
        'İ': 'i', 'Ş': 's', 'Ğ': 'g', 'Ü': 'u', 'Ö': 'o', 'Ç': 'c'
    }
    for old, new in replacements.items():
        sehir_clean = sehir_clean.replace(old, new)
    
    # Şehir ismi normalize et
    if any(x in sehir_clean for x in ['istanbul', 'istanbu']):
        sehir_clean = 'istanbul'
    elif any(x in sehir_clean for x in ['ankara', 'ankar']):
        sehir_clean = 'ankara'
    elif any(x in sehir_clean for x in ['izmir', 'izmi']):
        sehir_clean = 'izmir'
    elif any(x in sehir_clean for x in ['bursa', 'burs']):
        sehir_clean = 'bursa'
    elif any(x in sehir_clean for x in ['adana', 'adan']):
        sehir_clean = 'adana'
    elif any(x in sehir_clean for x in ['kocaeli', 'kocael']):
        sehir_clean = 'kocaeli'
    elif any(x in sehir_clean for x in ['elazig', 'elazi']):
        sehir_clean = 'elazig'
    elif any(x in sehir_clean for x in ['diyarbakir', 'diyarba']):
        sehir_clean = 'diyarbakir'
    elif any(x in sehir_clean for x in ['sanliurfa', 'urfa', 'sanli']):
        sehir_clean = 'sanliurfa'
    
    # Pist normalleştirme
    pist_clean = str(pist).lower().strip()
    pist_clean = unicodedata.normalize('NFD', pist_clean)
    pist_clean = ''.join(c for c in pist_clean if not unicodedata.combining(c))
    
    for old, new in replacements.items():
        pist_clean = pist_clean.replace(old, new)
    
    # Pist türü normalleştir
    if any(x in pist_clean for x in ['cim', 'çim']):
        pist_clean = 'çim'
    elif 'kum' in pist_clean and 'sentetik' not in pist_clean:
        pist_clean = 'kum'
    elif any(x in pist_clean for x in ['sentetik', 'sentet']):
        pist_clean = 'sentetik'
    else:
        pist_clean = 'unknown'
    
    return f"{sehir_clean}_{pist_clean}"

# Şehir + Pist kombinasyonları için ortalama hızlar (m/s)
SEHIR_PIST_HIZLARI = {
    'adana_kum': 14.7505,
    'adana_çim': 15.7531,
    'adana_sentetik': 15.2500,  # Eklendi
    'ankara_kum': 14.7742,
    'ankara_çim': 15.7185,
    'ankara_sentetik': 15.2400,  # Eklendi
    'bursa_kum': 14.9345,
    'bursa_çim': 15.8318,
    'bursa_sentetik': 15.3800,  # Eklendi
    'diyarbakir_kum': 13.6108,
    'diyarbakir_çim': 14.6100,  # Eklendi
    'diyarbakir_sentetik': 14.1000,  # Eklendi
    'elazig_kum': 14.0952,
    'elazig_çim': 15.0900,  # Eklendi
    'elazig_sentetik': 14.5900,  # Eklendi
    'istanbul_kum': 14.9100,  # Eklendi
    'istanbul_sentetik': 15.5146,
    'istanbul_çim': 15.7403,
    'izmir_kum': 14.9163,
    'izmir_çim': 15.7113,
    'izmir_sentetik': 15.3100,  # Eklendi
    'kocaeli_kum': 14.8824,
    'kocaeli_çim': 15.8800,  # Eklendi
    'kocaeli_sentetik': 15.3800,  # Eklendi
    'sanliurfa_kum': 13.9314,
    'sanliurfa_çim': 14.9300,  # Eklendi
    'sanliurfa_sentetik': 14.4300  # Eklendi
}

def calculate_kadapt(gecmis_sehir, gecmis_pist, hedef_sehir, hedef_pist):
    """k_adapt hesapla"""
    hedef_key = get_sehir_pist_key(hedef_sehir, hedef_pist)
    gecmis_key = get_sehir_pist_key(gecmis_sehir, gecmis_pist)
    hedef_hiz = SEHIR_PIST_HIZLARI.get(hedef_key, None)
    gecmis_hiz = SEHIR_PIST_HIZLARI.get(gecmis_key, None)
    if hedef_hiz is None or gecmis_hiz is None:
        hedef_sehir_clean = get_sehir_pist_key(hedef_sehir, "").replace("_", "")
        gecmis_sehir_clean = get_sehir_pist_key(gecmis_sehir, "").replace("_", "")
        katsayi = SEHIR_KATSAYILARI.get(hedef_sehir_clean, 1.0) / SEHIR_KATSAYILARI.get(gecmis_sehir_clean, 1.0)
        return katsayi
    kadapt = gecmis_hiz / hedef_hiz
    return kadapt

def process_calculation_for_city(horses_list, city_name):
    """Şehir için hesaplama işlemi yap"""
    import math
    
    # Hesaplama için gerekli değişkenler
    data = []
    group = []
    group_kosu = None
    son_hipodrom_map = {}
    
    # Son hipodrom mapping'i oluştur
    for horse in horses_list:
        key = (str(horse['Koşu']), str(horse['At İsmi']))
        son_hipodrom_map[key] = horse.get('Son Hipodrom', '')
    
    def add_group_sorted(group, group_kosu):
        if not group:
            return
        valid = [x for x in group if x['Çıktı'] != 'geçersiz']
        invalid = [x for x in group if x['Çıktı'] == 'geçersiz']
        valid_sorted = sorted(valid, key=lambda x: float(x['Çıktı']) if x['Çıktı'] != 'geçersiz' else float('inf'))
        data.append({'At İsmi': '', 'Koşu': f"{group_kosu}. Koşu", 'Çıktı': '', 'Son Mesafe': '', 'Son Pist': '', 'Son Kilo': '', 'Kilo': '', 'Son Hipodrom': ''})
        for x in valid_sorted:
            x2 = x.copy()
            x2['Koşu'] = ''
            key = (str(group_kosu), str(x2.get('At İsmi', '')))
            x2['Son Hipodrom'] = son_hipodrom_map.get(key, '')
            data.append(x2)
        for x in invalid:
            x2 = x.copy()
            x2['Koşu'] = ''
            key = (str(group_kosu), str(x2.get('At İsmi', '')))
            x2['Son Hipodrom'] = son_hipodrom_map.get(key, '')
            data.append(x2)
    
    # Her at için hesaplama yap
    for horse in horses_list:
        kosu = horse['Koşu']
        if group_kosu is None:
            group_kosu = kosu
        if kosu != group_kosu:
            add_group_sorted(group, group_kosu)
            group = []
            group_kosu = kosu
        
        at_adi = horse.get('At İsmi','')
        derece_raw = str(horse.get('Son Derece', '')).strip()
        
        if derece_raw.lower().replace('.', '').replace(' ', '') == 'drcsiz':
            cikti = 'geçersiz'
        else:
            derece = derece_raw
            
            def clean_float(val):
                import re
                s = str(val).replace('"','').replace("'",'').replace(' ','').replace(',','.')
                s = re.sub(r'[^0-9\.]+', '', s)
                return float(s) if s else None
            
            son_mesafe_raw = horse.get('Son Mesafe', '')
            bugun_mesafe_raw = horse.get('Bugünkü Mesafe', '')
            son_mesafe = clean_float(son_mesafe_raw)
            bugun_mesafe = clean_float(bugun_mesafe_raw)
            son_pist = str(horse.get('Son Pist', '')).strip()
            bugun_pist = str(horse.get('Bugünkü Pist', '')).strip()
            
            if (not derece or derece in ['-', '0', '0.0', '0,0'] or son_mesafe is None or bugun_mesafe is None or son_mesafe <= 0 or bugun_mesafe <= 0):
                cikti = 'geçersiz'
            else:
                try:
                    pist1 = pist_to_int(son_pist)
                    pist3 = pist_to_int(bugun_pist)
                    toplam_sure = calculate_average_time(derece, pist1, son_mesafe, bugun_mesafe, pist3)
                    ort_100m_sure = calculate_time_per_100m(toplam_sure, bugun_mesafe)
                    
                    gecmis_sehir = horse.get('Son Hipodrom', city_name)
                    hedef_sehir = city_name
                    kadapt = calculate_kadapt(gecmis_sehir, son_pist, hedef_sehir, bugun_pist)
                    
                    raw_score = ort_100m_sure
                    adjusted_score = raw_score * kadapt
                    
                    def clean_kilo(val):
                        import re
                        s = str(val).replace('"','').replace("'",'').replace(' ','').replace(',','.')
                        match = re.match(r'([0-9]+\.?[0-9]*)', s)
                        if match:
                            return float(match.group(1))
                        return None
                    
                    kilo_onceki = clean_kilo(horse.get('Son Kilo', ''))
                    kilo_bugun = clean_kilo(horse.get('Kilo', ''))
                    
                    cikti_deger = adjusted_score
                    if kilo_onceki is not None and kilo_bugun is not None:
                        kilo_fark = kilo_bugun - kilo_onceki
                        cikti_deger -= kilo_fark * 0.02
                    
                    if cikti_deger is None or cikti_deger <= 0:
                        cikti = 'geçersiz'
                    else:
                        cikti_deger_trunc = math.trunc(cikti_deger * 100) / 100
                        cikti = f"{cikti_deger_trunc:.2f}"
                except Exception as e:
                    print(f"[HESAPLAMA HATASI] {at_adi}: {e}")
                    cikti = 'geçersiz'
        
        group.append({
            'At İsmi': at_adi,
            'Koşu': kosu,
            'Çıktı': cikti,
            'Son Mesafe': horse.get('Son Mesafe', ''),
            'Son Pist': horse.get('Son Pist', ''),
            'Son Kilo': horse.get('Son Kilo', ''),
            'Kilo': horse.get('Kilo', '')
        })
    
    # Son grubu ekle
    if group:
        add_group_sorted(group, group_kosu)
    
    return data


def get_winner_data_from_url(race_url):
    """Verilen yarış URL'inden kazanan at bilgilerini çeker - SADECE DERCEYİ ÇEK"""
    try:
        print(f"[KAZANAN VERİSİ] URL çekiliyor: {race_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(race_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[KAZANAN VERİSİ HATASI] HTTP {response.status_code}: {race_url}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # kosanAtlar tablosunu bul
        result_table = soup.find('table', class_='kosanAtlar')
        if not result_table:
            print(f"[KAZANAN VERİSİ HATASI] kosanAtlar tablosu bulunamadı: {race_url}")
            return None
            
        tbody = result_table.find('tbody')
        if not tbody:
            print(f"[KAZANAN VERİSİ HATASI] tbody bulunamadı: {race_url}")
            return None
            
        # İlk sıradaki (1. olan) at bilgilerini al
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 9:  # En az 9 kolon olmalı
                # Sıra numarasını kontrol et (ilk hücre)
                sira_cell = cells[0]
                sira = sira_cell.get_text(strip=True)
                
                if sira == '1':
                    # At adını al (2. hücre, içindeki atisimlink'den)
                    at_cell = cells[1]
                    at_link = at_cell.find('a', class_='atisimlink')
                    if at_link:
                        at_adi = at_link.get_text(strip=True)
                    else:
                        at_adi = at_cell.get_text(strip=True)
                    
                    # Derece (9. hücre - "Derece" kolonu)
                    derece_cell = cells[8]
                    derece = derece_cell.get_text(strip=True)
                    
                    # Ganyan (10. hücre - "Gny" kolonu)
                    ganyan = ""
                    if len(cells) > 9:
                        ganyan_cell = cells[9]
                        ganyan = ganyan_cell.get_text(strip=True)
                    
                    # Yarış bilgilerini de al
                    yarış_mesafe = ""
                    yarış_pist = ""
                    
                    # Pist ve mesafe bilgisi için span'larda ara
                    pist_spans = soup.find_all('span', class_=['kumpist', 'cimpist', 'sentetikpist'])
                    for pist_span in pist_spans:
                        span_text = pist_span.get_text().strip()
                        span_class = ' '.join(pist_span.get('class', []))
                        
                        # Span text'inden mesafe ve pist çıkar: "1700 Çim" formatında
                        import re
                        if span_text:
                            # Mesafe ara (sayı + boşluk + pist türü)
                            match = re.match(r'(\d+)\s*(Çim|Kum|Sentetik)', span_text)
                            if match:
                                yarış_mesafe = match.group(1)
                                yarış_pist = match.group(2)
                                break
                    
                    # Eğer span text'inde bulamazsa class adından pist türünü çıkar
                    if not yarış_pist and pist_spans:
                        first_span = pist_spans[0]
                        span_class = ' '.join(first_span.get('class', []))
                        if 'kumpist' in span_class:
                            yarış_pist = "Kum"
                        elif 'cimpist' in span_class:
                            yarış_pist = "Çim"
                        elif 'sentetikpist' in span_class:
                            yarış_pist = "Sentetik"
                        
                        # Mesafe için span text'inde sadece sayı ara
                        if not yarış_mesafe and pist_spans:
                            span_text = first_span.get_text().strip()
                            mesafe_match = re.search(r'(\d+)', span_text)
                            if mesafe_match:
                                yarış_mesafe = mesafe_match.group(1)
                    
                    print(f"[KAZANAN BULUNDU] {at_adi} - {derece} - {ganyan} (Mesafe: {yarış_mesafe}, Pist: {yarış_pist})")
                    return {
                        'birinci_ismi': at_adi,
                        'birinci_derece': derece,
                        'birinci_ganyan': ganyan,
                        'yarış_mesafe': yarış_mesafe,
                        'yarış_pist': yarış_pist
                    }
        
        print(f"[KAZANAN VERİSİ HATASI] Birinci bulunamadı: {race_url}")
        return None
        
    except Exception as e:
        print(f"[KAZANAN VERİSİ HATASI] {race_url}: {e}")
        return None

def get_horse_rank_from_url(race_url, horse_name):
    """Verilen yarış URL'inden belirli atın derecesini çeker"""
    try:
        print(f"[AT DERECESİ] {horse_name} için {race_url} kontrol ediliyor...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(race_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[AT DERECESİ HATASI] HTTP {response.status_code}: {race_url}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # kosanAtlar tablosunu bul
        result_table = soup.find('table', class_='kosanAtlar')
        if not result_table:
            print(f"[AT DERECESİ HATASI] kosanAtlar tablosu bulunamadı: {race_url}")
            return None
            
        tbody = result_table.find('tbody')
        if not tbody:
            print(f"[AT DERECESİ HATASI] tbody bulunamadı: {race_url}")
            return None
            
        # Tüm satırları kontrol et ve atı bul
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 9:  # En az 9 kolon olmalı
                # At adını al (2. hücre, içindeki atisimlink'den)
                at_cell = cells[1]
                at_link = at_cell.find('a', class_='atisimlink')
                if at_link:
                    at_adi = at_link.get_text(strip=True)
                else:
                    at_adi = at_cell.get_text(strip=True)
                
                # Eğer aradığımız at buysa
                if at_adi.upper() == horse_name.upper():
                    # Sıra numarasını al (ilk hücre)
                    sira_cell = cells[0]
                    sira = sira_cell.get_text(strip=True)
                    
                    # Derece (9. hücre - "Derece" kolonu)
                    derece_cell = cells[8]
                    derece = derece_cell.get_text(strip=True)
                    
                    print(f"[AT DERECESİ BULUNDU] {horse_name}: {sira}. sıra, derece: {derece}")
                    return {
                        'sira': sira,
                        'derece': derece
                    }
        
        print(f"[AT DERECESİ HATASI] {horse_name} bulunamadı: {race_url}")
        return None
        
    except Exception as e:
        print(f"[AT DERECESİ HATASI] {horse_name} - {race_url}: {e}")
        return None


def get_last_race_url_from_profile(profile_link):
    """At profil linkinden son koşu URL'sini çeker"""
    try:
        # Profil linkini tam URL'e çevir
        base_url = "https://yenibeygir.com"
        if profile_link.startswith('/'):
            full_profile_url = base_url + profile_link
        else:
            full_profile_url = profile_link
            
        print(f"[PROFİL URL] Çekiliyor: {full_profile_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(full_profile_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[PROFİL URL HATASI] HTTP {response.status_code}: {full_profile_url}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # at_Yarislar tablosunu bul
        races_table = soup.find('table', class_='at_Yarislar')
        if races_table:
            tbody = races_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 1:
                        # İlk hücredeki linki al (tarih hücresi)
                        date_cell = cells[0]
                        link = date_cell.find('a')
                        if link and link.get('href'):
                            href = link.get('href')
                            # "Bugün" linkini atla, geçmiş yarışları al
                            link_text = link.get_text(strip=True)
                            if link_text != 'Bugün' and href:
                                # Tarihi kontrol et - sadece geçmiş tarihler
                                try:
                                    # URL'den tarihi çıkar (örn: /19-09-2025/istanbul/...)
                                    href_str = str(href)
                                    if '/' in href_str:
                                        date_part = href_str.split('/')[1]  # 19-09-2025
                                        if len(date_part.split('-')) == 3:
                                            day, month, year = date_part.split('-')
                                            race_date = datetime(int(year), int(month), int(day))
                                            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                                            
                                            # Sadece geçmiş tarihli koşuları al
                                            if race_date < today:
                                                # Eğer href tam URL değilse base_url ekle
                                                if href_str.startswith('/'):
                                                    race_url = base_url + href_str
                                                else:
                                                    race_url = href_str
                                                print(f"[SON KOŞU URL] Bulundu: {race_url}")
                                                return race_url
                                            else:
                                                print(f"[SON KOŞU URL] Gelecek tarih atlandı: {date_part}")
                                except ValueError:
                                    # Tarih parse edilemezse, URL'i kontrol etmeye devam et
                                    pass
        
        print(f"[SON KOŞU URL] at_Yarislar tablosu bulunamadı: {full_profile_url}")
        return None
        
    except Exception as e:
        print(f"[PROFİL URL HATASI] {profile_link}: {e}")
        return None


def process_kazanan_cikti_for_json(json_file_path, city_name, output_date):
    """JSON dosyasındaki her at için kazanan çıktı verilerini çeker"""
    try:
        print(f"[KAZANAN ANALİZİ] {city_name} için kazanan verileri çekiliyor...")
        
        # JSON dosyasını oku
        with open(json_file_path, 'r', encoding='utf-8') as f:
            horses_data = json.load(f)
        
        kazanan_data = []
        
        for horse in horses_data:
            at_ismi = horse.get('At İsmi', '')
            at_id = horse.get('At ID', '')
            kosu_no = horse.get('Koşu', '')  # JSON'da "Koşu" alanı var
            profil_linki = horse.get('Profil Linki', '')
            
            # Kazanan bilgilerini varsayılan olarak boş bırak
            kazanan_row = {
                'at_ismi': at_ismi,
                'at_id': at_id,
                'bugun_tarih': output_date,
                'bugun_sehir': city_name.lower(),
                'bugun_kosu_no': kosu_no,
                'json_dosyasi': os.path.basename(json_file_path),
                'onceki_kosu_url': '',
                'at_derece': '',  # Atın kendi derecesi
                'at_sira': '',    # Atın kendi sırası
                'onceki_kosu_birinci_ismi': '',
                'onceki_kosu_birinci_derece': '',
                'onceki_kosu_birinci_ganyan': '',
                'onceki_kosu_mesafe': '',  # Yarış mesafesi
                'onceki_kosu_pist': ''     # Yarış pist türü
            }
            
            # Profil linkinden son koşu URL'sini çek
            if profil_linki and profil_linki.strip():
                son_kosu_url = get_last_race_url_from_profile(profil_linki.strip())
                kazanan_row['onceki_kosu_url'] = son_kosu_url or ''
                
                # Eğer son koşu URL'i bulunduysa hem kazanan hem de atın kendi derecesini çek
                if son_kosu_url:
                    # Kazanan verilerini çek
                    winner_data = get_winner_data_from_url(son_kosu_url)
                    if winner_data:
                        kazanan_row['onceki_kosu_birinci_ismi'] = winner_data.get('birinci_ismi', '')
                        kazanan_row['onceki_kosu_birinci_derece'] = winner_data.get('birinci_derece', '')
                        kazanan_row['onceki_kosu_birinci_ganyan'] = winner_data.get('birinci_ganyan', '')
                        kazanan_row['onceki_kosu_mesafe'] = winner_data.get('yarış_mesafe', '')
                        kazanan_row['onceki_kosu_pist'] = winner_data.get('yarış_pist', '')
                    
                    # Bu atın kendi derecesini çek
                    horse_rank = get_horse_rank_from_url(son_kosu_url, at_ismi)
                    if horse_rank:
                        kazanan_row['at_derece'] = horse_rank.get('derece', '')
                        kazanan_row['at_sira'] = horse_rank.get('sira', '')
                        print(f"[AT DERECESİ] {at_ismi}: {horse_rank.get('sira', 'X')}. sıra ({horse_rank.get('derece', 'Derece yok')})")
                    else:
                        print(f"[AT DERECESİ] {at_ismi}: Derece bulunamadı")
                else:
                    print(f"[KAZANAN] {at_ismi}: Son koşu URL bulunamadı")
            else:
                print(f"[KAZANAN] {at_ismi}: Profil linki yok")
            
            kazanan_data.append(kazanan_row)
            
            # Rate limiting - çok hızlı istekleri önle
            time.sleep(1.0)  # Biraz daha yavaş yapalım
        
        print(f"[KAZANAN ANALİZİ] {city_name} için {len(kazanan_data)} at işlendi")
        return kazanan_data
        
    except Exception as e:
        print(f"[KAZANAN ANALİZİ HATASI] {city_name}: {e}")
        return []


def save_kazanan_cikti_csv(kazanan_data, city_name, output_date):
    """Kazanan çıktı verilerini CSV dosyasına kaydet"""
    try:
        if not kazanan_data:
            print(f"[KAZANAN CSV] {city_name}: Kaydedilecek veri yok")
            return None
            
        # DataFrame oluştur
        df = pd.DataFrame(kazanan_data)
        
        # Dosya adı oluştur
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{city_name.lower()}_kazanan_cikti_{output_date}_{timestamp}.csv"
        filepath = os.path.join('static', 'downloads', filename)
        
        # Downloads klasörü yoksa oluştur
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # CSV olarak kaydet
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"[KAZANAN CSV] {city_name}: {filename} kaydedildi ({len(kazanan_data)} kayıt)")
        return filepath
        
    except Exception as e:
        print(f"[KAZANAN CSV HATASI] {city_name}: {e}")
        return None

# KULLANILMIYOR - calculate_average_time ile değiştirildi
# def calculate_winner_score(winner_derece, winner_mesafe, winner_pist, bugun_mesafe, bugun_pist, city_name):
#     """Birincinin derecesini bugünkü koşullara göre hesapla"""
#     # Bu fonksiyon artık kullanılmıyor - tüm atlar için calculate_average_time kullanılıyor
#     pass

def get_kazanan_data_for_city(city_name):
    """Şehir için en son kazanan verilerini oku"""
    try:
        downloads_dir = os.path.join('static', 'downloads')
        bugun_tarih = datetime.now().strftime('%Y%m%d')
        
        # Bu şehir ve tarih için kazanan dosyalarını ara
        kazanan_files = []
        for filename in os.listdir(downloads_dir):
            if filename.startswith(f"{city_name.lower()}_kazanan_cikti_{bugun_tarih}_") and filename.endswith('.csv'):
                filepath = os.path.join(downloads_dir, filename)
                timestamp = os.path.getmtime(filepath)
                kazanan_files.append((timestamp, filepath, filename))
        
        if not kazanan_files:
            print(f"[KAZANAN VERİSİ] {city_name} için bugünkü kazanan dosyası bulunamadı")
            return {}
        
        # En son dosyayı al
        kazanan_files.sort(reverse=True)  # En yeni dosya ilk
        latest_file = kazanan_files[0][1]
        
        print(f"[KAZANAN VERİSİ] {city_name} kazanan verisi okunuyor: {os.path.basename(latest_file)}")
        
        df = pd.read_csv(latest_file)
        
        # At ismine göre dictionary oluştur
        kazanan_dict = {}
        for _, row in df.iterrows():
            at_ismi = row.get('at_ismi', '').strip()
            if at_ismi:
                kazanan_dict[at_ismi] = {
                    # Ham veriler
                    'at_derece': row.get('at_derece', ''),
                    'at_sira': row.get('at_sira', ''),
                    'kazanan_ismi': row.get('onceki_kosu_birinci_ismi', ''),
                    'kazanan_derece': row.get('onceki_kosu_birinci_derece', ''),
                    'kazanan_ganyan': row.get('onceki_kosu_birinci_ganyan', ''),
                    'onceki_mesafe': row.get('onceki_kosu_mesafe', ''),
                    'onceki_pist': row.get('onceki_kosu_pist', '')
                }
        
        print(f"[KAZANAN VERİSİ] {len(kazanan_dict)} at için kazanan verisi bulundu")
        return kazanan_dict
        
    except Exception as e:
        print(f"[KAZANAN VERİSİ HATASI] {city_name}: {e}")
        return {}
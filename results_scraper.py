#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SONUÇ ÇEKME SİSTEMİ
Gece saat 12'den sonra bir önceki günün sonuçlarını çeker
ve tahminlerle karşılaştırır
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json
import os
import re
import pandas as pd

# Horse scraper modülünden gerekli fonksiyonları import et
try:
    from horse_scraper import are_names_similar, clean_horse_name
except ImportError:
    # Eğer import edilemezse basit versiyonları tanımla
    def clean_horse_name(name):
        if not name:
            return ""
        return str(name).strip().upper()
    
    def are_names_similar(name1, name2):
        if not name1 or not name2:
            return False
        return clean_horse_name(name1) == clean_horse_name(name2)

# Horse scraper modülünden time_to_seconds fonksiyonunu import et
def time_to_seconds(time_str):
    """
    Zaman stringini saniyeye çevirir
    Örnek: "1.32.43" -> 92.43
    """
    if not time_str or str(time_str).strip() == '':
        return 0
    
    try:
        time_str = str(time_str).strip()
        parts = time_str.split('.')
        
        if len(parts) == 3:  # "1.32.43" formatı
            minutes = int(parts[0])
            seconds = int(parts[1])
            hundredths = int(parts[2])
            return minutes * 60 + seconds + hundredths / 100
        elif len(parts) == 2:  # "92.43" formatı
            return float(time_str.replace('.', '.'))
        else:
            return float(time_str)
    except:
        return 0

def seconds_to_time_format(seconds):
    """
    Saniyeyi zaman formatına çevirir
    Örnek: 92.43 -> "1.32.43"
    """
    if not seconds:
        return "0.00.00"
    
    try:
        total_seconds = float(seconds)
        minutes = int(total_seconds // 60)
        remaining_seconds = total_seconds % 60
        seconds_part = int(remaining_seconds)
        hundredths = int((remaining_seconds - seconds_part) * 100)
        
        return f"{minutes}.{seconds_part:02d}.{hundredths:02d}"
    except:
        return "0.00.00"

def get_previous_day_results(city, debug=False):
    """
    Bir önceki günün koşu sonuçlarını çeker
    
    Args:
        city (str): Şehir adı (bursa, istanbul, ankara, vb.)
        debug (bool): Debug modu
    
    Returns:
        dict: Koşu sonuçları {race_number: [{'at_ismi': '', 'derece': '', 'sira': 1}, ...]}
    """
    try:
        # Bir önceki güne ait tarihi hesapla
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%d-%m-%Y')
        
        # URL'yi oluştur
        url = f"https://yenibeygir.com/{date_str}/{city}/sonuclar"
        
        if debug:
            print(f"[SONUÇ] {city.upper()} sonuçları çekiliyor: {url}")
        
        # Sayfayı çek
        response = requests.get(url, timeout=10)
        
        if debug:
            print(f"[SONUÇ] HTTP Status: {response.status_code}")
        
        if response.status_code == 404:
            if debug:
                print(f"[SONUÇ] Sayfa bulunamadı: {url}")
            return {}
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sonuç verilerini parse et
        results = parse_results_page(soup, debug)
        
        if debug:
            print(f"[SONUÇ] {len(results)} koşu sonucu bulundu")
            if not results:
                print(f"[SONUÇ] Sayfa içeriği parse edilemedi veya sonuç yok")
        
        return results
        
    except Exception as e:
        if debug:
            print(f"[HATA] Sonuç çekme hatası: {str(e)}")
        return {}

def parse_results_page(soup, debug=False):
    """
    Sonuç sayfasını parse eder ve koşu sonuçlarını döndürür
    
    Args:
        soup: BeautifulSoup objesi
        debug (bool): Debug modu
    
    Returns:
        dict: Koşu sonuçları
    """
    results = {}
    
    try:
        # Tüm tabloları bul
        tables = soup.find_all('table')
        
        if debug:
            print(f"[PARSE] {len(tables)} tablo bulundu")
        
        race_number = 0
        
        for table in tables:
            tbody = table.find('tbody')
            if not tbody:
                continue
                
            rows = tbody.find_all('tr')
            if len(rows) < 2:  # En az 2 satır olmalı (başlık + 1 sonuç)
                continue
            
            # Bu tabloda sonuç var mı kontrol et
            has_results = False
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Sıra, At adı, vs.
                    # İlk sütunun sayısal olup olmadığını kontrol et
                    first_cell = cells[0].get_text(strip=True)
                    if first_cell.isdigit():
                        has_results = True
                        break
            
            if not has_results:
                continue
                
            race_number += 1
            race_results = []
            
            if debug:
                print(f"  [KOŞU {race_number}] Parse ediliyor...")
            
            # Sonuç satırlarını parse et
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 9:  # Yeterli sütun var mı?
                    try:
                        # Sıra (ilk sütun)
                        sira_text = cells[0].get_text(strip=True)
                        if not sira_text.isdigit():
                            continue
                        
                        sira = int(sira_text)
                        
                        # At ismi (ikinci sütun) - genelde bağlantı içinde
                        at_cell = cells[1]
                        at_link = at_cell.find('a')
                        if at_link:
                            at_ismi_full = at_link.get_text(strip=True)
                        else:
                            at_ismi_full = at_cell.get_text(strip=True)
                        
                        # At ismini temizle - parantez içindeki kısımları ve ek bilgileri çıkar
                        at_ismi = clean_horse_name(at_ismi_full)
                        
                        # Derece (8. sütun genelde)
                        derece = cells[8].get_text(strip=True) if len(cells) > 8 else ""
                        
                        if at_ismi and derece:
                            race_results.append({
                                'sira': sira,
                                'at_ismi': at_ismi,
                                'derece': derece,
                                'at_ismi_full': at_ismi_full
                            })
                            
                            if debug:
                                print(f"    {sira}. {at_ismi} - {derece}")
                    
                    except Exception as e:
                        if debug:
                            print(f"    [HATA] Satır parse hatası: {str(e)}")
                        continue
            
            if race_results:
                results[race_number] = race_results
        
        return results
        
    except Exception as e:
        if debug:
            print(f"[HATA] Parse hatası: {str(e)}")
        return {}

def clean_horse_name(full_name):
    """
    At ismini temizler - parantez içindeki bilgileri ve ek sembolleri çıkarır
    
    Args:
        full_name (str): Tam at ismi
    
    Returns:
        str: Temizlenmiş at ismi
    """
    if not full_name:
        return ""
    
    # Parantez içindeki kısımları çıkar
    cleaned = re.sub(r'\([^)]*\)', '', full_name)
    
    # Özel karakterleri ve ek bilgileri çıkar
    cleaned = re.sub(r'\s+(SK|DB|K|SKG|GKR|YP|ÖG|SGKR)\s*', ' ', cleaned)
    
    # Fazla boşlukları temizle
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def compare_predictions_with_results(city, debug=False):
    """
    Tahminleri sonuçlarla karşılaştırır
    
    Args:
        city (str): Şehir adı
        debug (bool): Debug modu
    
    Returns:
        dict: Karşılaştırma sonuçları
    """
    try:
        # Dünün tarihini hesapla
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y%m%d')
        
        # Tahmin dosyasını bul
        prediction_file = f"data/{city}_atlari_{date_str}.json"
        
        if not os.path.exists(prediction_file):
            if debug:
                print(f"[UYARI] Tahmin dosyası bulunamadı: {prediction_file}")
            return {'error': 'Tahmin dosyası bulunamadı'}
        
        # Tahminleri yükle
        with open(prediction_file, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        # Sonuçları çek
        results = get_previous_day_results(city, debug)
        
        if not results:
            return {'error': 'Sonuçlar çekilemedi'}
        
        # Karşılaştırmayı yap
        comparison = perform_comparison(predictions, results, debug)
        
        return comparison
        
    except Exception as e:
        if debug:
            print(f"[HATA] Karşılaştırma hatası: {str(e)}")
        return {'error': str(e)}

def get_detailed_race_comparison(city, debug=False):
    """
    Her koşuda tüm atların detaylı karşılaştırmasını yapar
    
    Args:
        city (str): Şehir adı
        debug (bool): Debug modu
    
    Returns:
        dict: Detaylı karşılaştırma sonuçları
    """
    try:
        # Dünün tarihini hesapla
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y%m%d')
        
        # Tahmin dosyasını bul
        prediction_file = f"data/{city}_atlari_{date_str}.json"
        
        if not os.path.exists(prediction_file):
            if debug:
                print(f"[UYARI] Tahmin dosyası bulunamadı: {prediction_file}")
            return {'error': 'Tahmin dosyası bulunamadı'}
        
        # Tahminleri yükle
        with open(prediction_file, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        # Sonuçları çek
        results = get_previous_day_results(city, debug)
        
        if not results:
            return {'error': 'Sonuçlar çekilemedi'}
        
        # Detaylı karşılaştırmayı yap
        detailed_comparison = perform_detailed_comparison(predictions, results, debug)
        
        return detailed_comparison
        
    except Exception as e:
        if debug:
            print(f"[HATA] Detaylı karşılaştırma hatası: {str(e)}")
        return {'error': str(e)}

def perform_detailed_comparison(predictions, results, debug=False):
    """
    Tüm atların detaylı karşılaştırmasını yapar
    
    Args:
        predictions (list): Tahmin verileri
        results (dict): Sonuç verileri
        debug (bool): Debug modu
    
    Returns:
        dict: Detaylı karşılaştırma sonuçları
    """
    comparison_results = {
        'total_races': 0,
        'successful_predictions': 0,
        'detailed_races': [],
        'success_rate': 0.0,
        'city': predictions[0].get('Şehir', 'Bilinmeyen') if predictions else 'Bilinmeyen'
    }
    
    try:
        # Tahminleri koşu numarasına göre grupla
        predictions_by_race = {}
        for prediction in predictions:
            race_num = prediction.get('Koşu') or prediction.get('kos_no') or prediction.get('race_number', 0)
            
            try:
                if isinstance(race_num, str):
                    race_num = int(race_num)
            except (ValueError, TypeError):
                continue
            
            if race_num and race_num > 0:
                if race_num not in predictions_by_race:
                    predictions_by_race[race_num] = []
                predictions_by_race[race_num].append(prediction)
        
        if debug:
            print(f"[DETAYLI ANALIZ] {len(predictions_by_race)} koşu analiz ediliyor")
        
        # Her koşu için detaylı analiz
        for race_num, race_predictions in predictions_by_race.items():
            if race_num not in results:
                continue
            
            comparison_results['total_races'] += 1
            race_results = results[race_num]
            
            # Kazanan atı bul
            winner = None
            for result in race_results:
                if result['sira'] == 1:
                    winner = result
                    break
            
            if not winner:
                continue
            
            # Tüm atları işle
            all_horses = []
            predicted_winner = None
            best_calculated_time = float('inf')
            
            for prediction in race_predictions:
                # At bilgilerini al
                horse_name = clean_horse_name(prediction.get('At İsmi', ''))
                cikti_str = str(prediction.get('Çıktı', '')).strip()
                mesafe_str = str(prediction.get('Bugünkü Mesafe', '')).strip()
                
                # Çıktı hesapla
                calculated_time = 0
                cikti_value = 0
                
                if not cikti_str or cikti_str == 'geçersiz':
                    son_derece = str(prediction.get('Son Derece', '')).strip()
                    son_mesafe = str(prediction.get('Son Mesafe', '')).strip()
                    
                    if son_derece and son_mesafe:
                        try:
                            derece_saniye = time_to_seconds(son_derece)
                            son_mesafe_value = float(son_mesafe.replace(',', '.'))
                            if son_mesafe_value > 0:
                                cikti_value = derece_saniye / (son_mesafe_value / 100)
                                if debug:
                                    print(f"    [HESAPLANDI] {horse_name}: {son_derece} ({derece_saniye}s) / {son_mesafe_value}m = {cikti_value:.2f}")
                        except:
                            cikti_value = 0
                else:
                    try:
                        cikti_value = float(cikti_str.replace(',', '.'))
                    except:
                        cikti_value = 0
                
                # Tahmini süreyi hesapla
                if cikti_value > 0 and mesafe_str:
                    try:
                        mesafe_value = float(mesafe_str.replace(',', '.'))
                        calculated_time = cikti_value * (mesafe_value / 100)
                    except:
                        calculated_time = 0
                
                # Gerçek sonucu bul
                actual_position = None
                actual_time = None
                for i, result in enumerate(race_results, 1):
                    if are_names_similar(horse_name, clean_horse_name(result['at_ismi'])):
                        actual_position = result['sira']
                        actual_time = result['derece']
                        break
                
                # Ek bilgileri al
                son_mesafe = prediction.get('Son Mesafe', '')
                pist_turu = prediction.get('Son Pist', '')
                
                horse_data = {
                    'name': horse_name,
                    'predicted_time': seconds_to_time_format(calculated_time) if calculated_time > 0 else '',
                    'calculated_score': cikti_value,
                    'distance': mesafe_str,
                    'calculation_distance': son_mesafe,  # Hesaplama için kullanılan mesafe
                    'track_type': pist_turu,  # Pist türü
                    'actual_position': actual_position,
                    'actual_time': actual_time,
                    'is_winner_prediction': False,
                    'is_actual_winner': actual_position == 1 if actual_position else False
                }
                
                all_horses.append(horse_data)
                
                # En iyi tahmini bul
                if calculated_time > 0 and calculated_time < best_calculated_time:
                    best_calculated_time = calculated_time
                    predicted_winner = horse_data
            
            # En iyi tahmini işaretle
            if predicted_winner:
                predicted_winner['is_winner_prediction'] = True
            
            # Atları skorlarına göre sırala (tüm atlara sıra ver)
            sorted_horses = sorted(all_horses, key=lambda x: x['calculated_score'] if x['calculated_score'] > 0 else 999)
            top_3_predictions = sorted_horses[:3]
            
            # Tüm atlara tahmin sırası ver
            for i, horse in enumerate(sorted_horses, 1):
                if horse['calculated_score'] > 0:  # Geçerli skor varsa
                    horse['prediction_rank'] = i
            
            # Başarılı tahmin kontrolü - İlk 3 tahminimizden biri kazandı mı?
            is_successful = False
            successful_horse = None
            
            for horse in top_3_predictions:
                if horse.get('calculated_score', 0) > 0 and horse.get('is_actual_winner', False):
                    is_successful = True
                    successful_horse = horse
                    comparison_results['successful_predictions'] += 1
                    break
            
            # Koşu verilerini ekle
            race_data = {
                'race_number': race_num,
                'horses': sorted_horses,
                'predicted_winner': predicted_winner['name'] if predicted_winner else '',
                'actual_winner': clean_horse_name(winner['at_ismi']),
                'top_3_predictions': [h['name'] for h in top_3_predictions if h.get('calculated_score', 0) > 0],
                'successful_horse': successful_horse['name'] if successful_horse else None,
                'is_successful': is_successful
            }
            
            comparison_results['detailed_races'].append(race_data)
            
            if debug:
                status = "✓ DOĞRU" if race_data['is_successful'] else "✗ YANLIŞ"
                print(f"[KOŞU {race_num}] {status}")
                print(f"  İlk 3 Tahmin: {', '.join(race_data['top_3_predictions'])}")
                print(f"  Gerçek Kazanan: {race_data['actual_winner']}")
                if race_data['successful_horse']:
                    print(f"  Başarılı Tahmin: {race_data['successful_horse']}")
                print(f"  Toplam At: {len(all_horses)}")
        
        # Başarı oranını hesapla
        if comparison_results['total_races'] > 0:
            comparison_results['success_rate'] = (
                comparison_results['successful_predictions'] / comparison_results['total_races']
            ) * 100
        
        return comparison_results
        
    except Exception as e:
        if debug:
            print(f"[HATA] Detaylı karşılaştırma hatası: {str(e)}")
        return {'error': str(e)}

def perform_comparison(predictions, results, debug=False):
    """
    Tahminler ile sonuçları karşılaştırır
    
    Args:
        predictions (list): Tahmin verileri
        results (dict): Sonuç verileri
        debug (bool): Debug modu
    
    Returns:
        dict: Karşılaştırma sonuçları
    """
    comparison_results = {
        'total_races': 0,
        'successful_predictions': 0,
        'detailed_results': [],
        'success_rate': 0
    }
    
    try:
        # Tahminleri koşu numarasına göre grupla
        predictions_by_race = {}
        for prediction in predictions:
            # Koşu numarasını al - farklı alan adları deneyebiliriz
            race_num = prediction.get('Koşu') or prediction.get('kos_no') or prediction.get('race_number', 0)
            
            # String ise integer'a çevir
            try:
                if isinstance(race_num, str):
                    race_num = int(race_num)
            except (ValueError, TypeError):
                continue
            
            if race_num and race_num > 0:
                if race_num not in predictions_by_race:
                    predictions_by_race[race_num] = []
                predictions_by_race[race_num].append(prediction)
        
        if debug:
            print(f"[TAHMIN GRUPLARI] {len(predictions_by_race)} koşu grubu oluşturuldu: {list(predictions_by_race.keys())}")
        
        # Her koşu için karşılaştır
        for race_num, race_predictions in predictions_by_race.items():
            if race_num not in results:
                if debug:
                    print(f"[KOŞU {race_num}] Sonuç bulunamadı")
                continue
            
            comparison_results['total_races'] += 1
            race_results = results[race_num]
            
            # 1. sıradaki atı bul
            winner = None
            for result in race_results:
                if result['sira'] == 1:
                    winner = result
                    break
            
            if not winner:
                if debug:
                    print(f"[KOŞU {race_num}] Kazanan bulunamadı")
                continue
            
            # En iyi tahminimizi bul - çıktı değeri * mesafe ile hesaplanan en düşük skor
            predicted_winner = None
            best_calculated_time = float('inf')
            
            for prediction in race_predictions:
                # Çıktı değeri ve mesafe bilgilerini al
                cikti_str = str(prediction.get('Çıktı', '')).strip()
                mesafe_str = str(prediction.get('Bugünkü Mesafe', '')).strip()
                
                # Eğer Çıktı yoksa, Son Derece'yi kullanarak çıktı hesapla
                if not cikti_str or cikti_str == 'geçersiz':
                    son_derece = str(prediction.get('Son Derece', '')).strip()
                    son_mesafe = str(prediction.get('Son Mesafe', '')).strip()
                    
                    if son_derece and son_mesafe:
                        try:
                            # Son derece'yi saniyeye çevir
                            derece_saniye = time_to_seconds(son_derece)
                            son_mesafe_value = float(son_mesafe.replace(',', '.'))
                            
                            if derece_saniye > 0 and son_mesafe_value > 0:
                                # 100m başına süreyi hesapla
                                cikti_value = derece_saniye / (son_mesafe_value / 100)
                                cikti_str = f"{cikti_value:.2f}"
                                if debug:
                                    at_ismi = prediction.get('At İsmi', '')
                                    print(f"    [HESAPLANDI] {at_ismi}: {son_derece} ({derece_saniye}s) / {son_mesafe}m = {cikti_value:.2f}")
                        except:
                            continue
                
                if cikti_str and cikti_str != 'geçersiz' and mesafe_str:
                    try:
                        # Çıktı değerini float'a çevir
                        cikti_value = float(cikti_str.replace(',', '.'))
                        # Mesafeyi float'a çevir  
                        mesafe_value = float(mesafe_str.replace(',', '.'))
                        
                        # Tahmini süreyi hesapla: çıktı * (mesafe/100)
                        calculated_time = cikti_value * (mesafe_value / 100)
                        
                        if calculated_time < best_calculated_time:
                            best_calculated_time = calculated_time
                            predicted_winner = prediction
                            predicted_winner['calculated_time'] = calculated_time
                            predicted_winner['calculated_cikti'] = cikti_value  # Hesaplanan çıktıyı kaydet
                            
                    except (ValueError, TypeError):
                        continue
            
            if not predicted_winner:
                if debug:
                    print(f"[KOŞU {race_num}] Geçerli tahmin bulunamadı")
                continue
            
            # At isimlerini karşılaştır
            predicted_name = clean_horse_name(predicted_winner.get('At İsmi', ''))
            actual_name = clean_horse_name(winner['at_ismi'])
            
            is_successful = are_names_similar(predicted_name, actual_name)
            
            if is_successful:
                comparison_results['successful_predictions'] += 1
            
            # Tahmini süreyi formatla
            predicted_time_formatted = ""
            if 'calculated_time' in predicted_winner:
                predicted_time_formatted = seconds_to_time_format(predicted_winner['calculated_time'])
            
            race_detail = {
                'race_number': race_num,
                'predicted_winner': predicted_name,
                'actual_winner': actual_name,
                'is_successful': is_successful,
                'predicted_time': predicted_time_formatted,
                'actual_time': winner['derece'],
                'prediction_details': {
                    'cikti': predicted_winner.get('Çıktı', ''),
                    'mesafe': predicted_winner.get('Bugünkü Mesafe', ''),
                    'calculated_time': seconds_to_time_format(predicted_winner.get('calculated_time', 0))
                }
            }
            
            comparison_results['detailed_results'].append(race_detail)
            
            if debug:
                status = "✓ DOĞRU" if is_successful else "✗ YANLIŞ"
                cikti = predicted_winner.get('Çıktı', '')
                mesafe = predicted_winner.get('Bugünkü Mesafe', '')
                calc_time = predicted_winner.get('calculated_time', 0)
                calc_time_formatted = seconds_to_time_format(calc_time)
                print(f"[KOŞU {race_num}] {status}")
                print(f"  Tahmin: {predicted_name} (Çıktı: {cikti}, Mesafe: {mesafe}m, Hesaplanan: {calc_time_formatted})")
                print(f"  Gerçek: {actual_name} (Derece: {winner['derece']})")
        
        # Başarı oranını hesapla
        if comparison_results['total_races'] > 0:
            comparison_results['success_rate'] = (
                comparison_results['successful_predictions'] / 
                comparison_results['total_races'] * 100
            )
        
        return comparison_results
        
    except Exception as e:
        if debug:
            print(f"[HATA] Karşılaştırma işlemi hatası: {str(e)}")
        return comparison_results

def are_names_similar(name1, name2, threshold=0.8):
    """
    İki at isminin benzer olup olmadığını kontrol eder
    
    Args:
        name1 (str): İlk at ismi
        name2 (str): İkinci at ismi
        threshold (float): Benzerlik eşiği
    
    Returns:
        bool: Benzer ise True
    """
    if not name1 or not name2:
        return False
    
    # Basit string karşılaştırması
    name1_clean = name1.upper().strip()
    name2_clean = name2.upper().strip()
    
    # Tam eşleşme
    if name1_clean == name2_clean:
        return True
    
    # Levenshtein benzerliği (basit implementasyon)
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()
    
    return similarity >= threshold

def schedule_midnight_check():
    """
    Gece saat 12'den sonra otomatik kontrol yapacak fonksiyon
    Bu fonksiyon sürekli çalışacak bir servis olarak tasarlanmalı
    """
    cities = ['bursa', 'istanbul', 'ankara', 'izmir', 'adana', 'kocaeli', 'sanliurfa', 'diyarbakir', 'elazig']
    
    while True:
        now = datetime.now()
        
        # Gece 00:30'da kontrol yap (yarış sonuçları kesinleşsin diye biraz bekle)
        if now.hour == 0 and now.minute == 30:
            print(f"[OTOMATIK] {now.strftime('%d.%m.%Y %H:%M')} - Önceki gün sonuçları kontrol ediliyor...")
            
            for city in cities:
                try:
                    print(f"\n=== {city.upper()} SONUÇLARI ===")
                    comparison = compare_predictions_with_results(city, debug=True)
                    
                    if 'error' not in comparison:
                        success_rate = comparison['success_rate']
                        total_races = comparison['total_races']
                        successful = comparison['successful_predictions']
                        
                        print(f"BAŞARI ORANI: {success_rate:.1f}% ({successful}/{total_races})")
                        
                        # Sonuçları kaydet
                        save_comparison_results(city, comparison)
                    else:
                        print(f"HATA: {comparison['error']}")
                
                except Exception as e:
                    print(f"HATA ({city}): {str(e)}")
            
            # Bir sonraki gün için bekle
            time.sleep(24 * 60 * 60)  # 24 saat bekle
        
        # 1 dakika bekle ve tekrar kontrol et
        time.sleep(60)

def save_comparison_results(city, comparison_data):
    """
    Karşılaştırma sonuçlarını dosyaya kaydet
    
    Args:
        city (str): Şehir adı
        comparison_data (dict): Karşılaştırma verileri
    """
    try:
        # Sonuçlar klasörü oluştur
        results_dir = "data/comparisons"
        os.makedirs(results_dir, exist_ok=True)
        
        # Dosya adı
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y%m%d')
        filename = f"{results_dir}/{city}_comparison_{date_str}.json"
        
        # Kaydet
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, ensure_ascii=False, indent=2)
        
        print(f"[KAYIT] Sonuçlar kaydedildi: {filename}")
        
    except Exception as e:
        print(f"[HATA] Sonuç kayıt hatası: {str(e)}")

# Test fonksiyonu
def test_result_scraper():
    """Test fonksiyonu - manuel çalıştırma için"""
    print("=== SONUÇ ÇEKME TESTİ ===")
    
    # Bursa sonuçlarını test et
    results = get_previous_day_results('bursa', debug=True)
    
    if results:
        print(f"\n{len(results)} koşu sonucu bulundu:")
        for race_num, race_results in results.items():
            print(f"\nKoşu {race_num}:")
            for i, result in enumerate(race_results[:3], 1):  # İlk 3'ü göster
                print(f"  {i}. {result['at_ismi']} - {result['derece']}")
    
    # Karşılaştırma testi
    print("\n=== KARŞILAŞTIRMA TESTİ ===")
    comparison = compare_predictions_with_results('bursa', debug=True)
    
    if 'error' not in comparison:
        print(f"\nBaşarı Oranı: {comparison['success_rate']:.1f}%")
        print(f"Toplam Koşu: {comparison['total_races']}")
        print(f"Doğru Tahmin: {comparison['successful_predictions']}")

if __name__ == "__main__":
    test_result_scraper()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AT YARIŞI ANALİZ SİSTEMİ - PRODUCTION         return f"At Yarişı Analiz Sistemi çalışıyor! Hata: {str(e)}", 500ERSION
VPS üzerinde sürekli çalışması için optimize edilmiş
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import json

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Production ayarları
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
else:
    app.config['DEBUG'] = True

# At yarışı analiz modüllerini import et
try:
    from horse_scraper import (
        get_adana_races_and_horse_last_race,
        get_ankara_races_and_horse_last_race,
        get_bursa_races_and_horse_last_race,
        get_diyarbakir_races_and_horse_last_race,
        get_elazig_races_and_horse_last_race,
        get_istanbul_races_and_horse_last_race,
        get_izmir_races_and_horse_last_race,
        get_kocaeli_races_and_horse_last_race,
        get_sanliurfa_races_and_horse_last_race,
        process_calculation_for_city
    )
    logging.info("At yarışı modülleri başarıyla yüklendi")
except ImportError as e:
    logging.error(f"At yarışı modülleri yüklenemedi: {e}")
    # Fallback - eğer import edilemezse boş fonksiyonlar tanımla
    def get_adana_races_and_horse_last_race(debug=False):
        return []
    def get_ankara_races_and_horse_last_race(debug=False):
        return []
    def get_bursa_races_and_horse_last_race(debug=False):
        return []
    def get_diyarbakir_races_and_horse_last_race(debug=False):
        return []
    def get_elazig_races_and_horse_last_race(debug=False):
        return []
    def get_istanbul_races_and_horse_last_race(debug=False):
        return []
    def get_izmir_races_and_horse_last_race(debug=False):
        return []
    def get_kocaeli_races_and_horse_last_race(debug=False):
        return []
    def get_sanliurfa_races_and_horse_last_race(debug=False):
        return []
    def process_calculation_for_city(horses_list, city_name):
        return []

# Şehir fonksiyonları mapping
CITY_FUNCTIONS = {
    'adana': ('Adana', get_adana_races_and_horse_last_race),
    'ankara': ('Ankara', get_ankara_races_and_horse_last_race),
    'bursa': ('Bursa', get_bursa_races_and_horse_last_race),
    'diyarbakir': ('Diyarbakır', get_diyarbakir_races_and_horse_last_race),
    'elazig': ('Elazığ', get_elazig_races_and_horse_last_race),
    'istanbul': ('İstanbul', get_istanbul_races_and_horse_last_race),
    'izmir': ('İzmir', get_izmir_races_and_horse_last_race),
    'kocaeli': ('Kocaeli', get_kocaeli_races_and_horse_last_race),
    'sanliurfa': ('Şanlıurfa', get_sanliurfa_races_and_horse_last_race),
}

@app.route('/')
def index():
    """Ana sayfa"""
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Ana sayfa hatası: {e}")
        return f"At Yarışı Analiz Sistemi çalışıyor! Hata: {str(e)}", 500

@app.route('/health')
def health_check():
    """Sistem durumu kontrolü - VPS monitoring için"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'message': 'At Yarışı Analiz Sistemi çalışıyor!'
    }

@app.route('/api/cities')
def get_cities():
    """Desteklenen şehirleri listele"""
    cities = [{'id': key, 'name': value[0]} for key, value in CITY_FUNCTIONS.items()]
    return jsonify({'cities': cities})

@app.route('/api/scrape_and_save', methods=['POST'])
def scrape_and_save():
    """At verilerini çek ve kaydet"""
    try:
        data = request.get_json()
        city = data.get('city', '').lower()
        debug = data.get('debug', False)
        
        if city not in CITY_FUNCTIONS:
            return jsonify({
                'status': 'error',
                'message': f'Desteklenmeyen şehir: {city}'
            }), 400
        
        city_name, city_function = CITY_FUNCTIONS[city]
        
        logging.info(f"{city_name} at verileri çekiliyor...")
        
        # At verilerini çek
        horses = city_function(debug)
        
        if horses:
            # Data klasörü oluştur
            os.makedirs('data', exist_ok=True)
            
            # Bugünkü tarih için JSON dosyasına kaydet
            today = datetime.now().strftime('%Y%m%d')
            saved_filename = f"{city}_atlari_{today}.json"
            saved_filepath = os.path.join('data', saved_filename)
            
            with open(saved_filepath, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            
            # Ham veri CSV'si de oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            raw_df = pd.DataFrame(horses)
            raw_filename = f"{city}_ham_veri_{timestamp}.csv"
            raw_filepath = os.path.join('static', 'downloads', raw_filename)
            
            # Downloads klasörü yoksa oluştur
            os.makedirs(os.path.dirname(raw_filepath), exist_ok=True)
            raw_df.to_csv(raw_filepath, index=False, encoding='utf-8-sig')
            
            # İstatistikler
            basarili = sum(1 for h in horses if h['Son Derece'])
            oran = round((basarili / len(horses)) * 100, 1) if horses else 0
            
            logging.info(f"[OK] {city_name}: {len(horses)} at, {basarili} başarılı (%{oran})")
            
            return jsonify({
                'status': 'success',
                'data': {
                    'city': city_name,
                    'total_horses': len(horses),
                    'successful_horses': basarili,
                    'success_rate': oran,
                    'saved_filename': saved_filename,
                    'raw_download_url': f'/download/{raw_filename}',
                    'raw_filename': raw_filename,
                    'source': 'fresh_scrape'
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'{city_name} için veri çekilemedi'
            }), 500
            
    except Exception as e:
        logging.error(f"Veri çekme hatası: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/check_saved_data', methods=['POST'])
def check_saved_data():
    """Kaydedilmiş veri var mı kontrol et"""
    try:
        data = request.get_json()
        city = data.get('city', '').lower()
        
        if city not in CITY_FUNCTIONS:
            return jsonify({
                'status': 'error',
                'message': f'Desteklenmeyen şehir: {city}'
            }), 400
        
        city_name, _ = CITY_FUNCTIONS[city]
        
        # Bugünkü tarih için dosya adı oluştur
        today = datetime.now().strftime('%Y%m%d')
        saved_filename = f"{city}_atlari_{today}.json"
        saved_filepath = os.path.join('data', saved_filename)
        
        if os.path.exists(saved_filepath):
            # Dosyayı oku
            with open(saved_filepath, 'r', encoding='utf-8') as f:
                horses_data = json.load(f)
            
            # İstatistikleri hesapla
            total_horses = len(horses_data)
            successful = sum(1 for h in horses_data if h.get('Son Derece'))
            success_rate = round((successful / total_horses) * 100, 1) if total_horses > 0 else 0
            
            return jsonify({
                'status': 'success',
                'has_data': True,
                'data': {
                    'city': city_name,
                    'total_horses': total_horses,
                    'successful_horses': successful,
                    'success_rate': success_rate,
                    'file_date': today
                }
            })
        else:
            return jsonify({
                'status': 'success',
                'has_data': False,
                'message': f'{city_name} için bugünkü veri bulunamadı'
            })
            
    except Exception as e:
        logging.error(f"Veri kontrol hatası: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/calculate_from_saved', methods=['POST'])
def calculate_from_saved():
    """Kaydedilmiş verilerden hesaplama yap"""
    try:
        data = request.get_json()
        city = data.get('city', '').lower()
        
        if city not in CITY_FUNCTIONS:
            return jsonify({
                'status': 'error',
                'message': f'Desteklenmeyen şehir: {city}'
            }), 400
        
        city_name, _ = CITY_FUNCTIONS[city]
        
        # Bugünkü tarih için dosya adı oluştur
        today = datetime.now().strftime('%Y%m%d')
        saved_filename = f"{city}_atlari_{today}.json"
        saved_filepath = os.path.join('data', saved_filename)
        
        if not os.path.exists(saved_filepath):
            return jsonify({
                'status': 'error',
                'message': f'{city_name} için kaydedilmiş veri bulunamadı. Önce veri çekin.'
            }), 404
        
        # Kaydedilmiş veriyi oku
        with open(saved_filepath, 'r', encoding='utf-8') as f:
            horses = json.load(f)
        
        logging.info(f"{city_name} için kaydedilmiş veriden hesaplama yapılıyor...")
        
        # Hesaplama yap
        calculated_data = process_calculation_for_city(horses, city_name)
        
        # Verileri koşu bazında grupla
        races_data = {}
        for item in calculated_data:
            if item['Koşu'] and 'Koşu' in item['Koşu']:  # Koşu başlığı
                race_number = item['Koşu'].replace('. Koşu', '').strip()
                if race_number:
                    races_data[race_number] = {'horses': []}
            elif item['At İsmi']:  # At verisi
                # En son koşuya at ekle
                if races_data:
                    last_race = list(races_data.keys())[-1]
                    horse_data = {
                        'at_adi': item['At İsmi'],
                        'skor': float(item['Çıktı']) if item['Çıktı'] != 'geçersiz' else 'Veri yok',
                        'jokey': '',  
                        'yas': '',
                        'agirlik': item.get('Kilo', ''),
                        'son_mesafe': item.get('Son Mesafe', ''),
                        'son_pist': item.get('Son Pist', ''),
                        'son_kilo': item.get('Son Kilo', ''),
                        'son_hipodrom': item.get('Son Hipodrom', ''),
                        'son_derece': item.get('Son Derece', '')
                    }
                    races_data[last_race]['horses'].append(horse_data)
        
        # JSON formatına çevir
        races_list = []
        for race_num in sorted(races_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            races_list.append({
                'race_number': race_num,
                'horses': races_data[race_num]['horses']
            })
        
        # İstatistikler
        total_horses = sum(len(race['horses']) for race in races_list)
        valid_horses = sum(1 for race in races_list for horse in race['horses'] 
                          if isinstance(horse['skor'], (int, float)) and horse['skor'] != 'Veri yok')
        success_rate = round((valid_horses / total_horses) * 100, 1) if total_horses > 0 else 0
        
        logging.info(f"[OK] {city_name} hesaplama tamamlandı: {total_horses} at, {valid_horses} geçerli")
        
        return jsonify({
            'status': 'success',
            'city': city_name,
            'races': races_list,
            'total_horses': total_horses,
            'valid_horses': valid_horses,
            'success_rate': success_rate,
            'source': 'saved_data'
        })
        
    except Exception as e:
        logging.error(f"Hesaplama hatası: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Hesaplama hatası: {str(e)}'
        }), 500

@app.route('/api/scrape_and_calculate', methods=['POST'])
def scrape_and_calculate():
    """Tek şehir için at verilerini çek VE hesapla"""
    try:
        data = request.get_json()
        city = data.get('city', '').lower()
        debug = data.get('debug', False)
        
        if city not in CITY_FUNCTIONS:
            return jsonify({
                'status': 'error',
                'message': f'Desteklenmeyen şehir: {city}'
            }), 400
        
        city_name, city_function = CITY_FUNCTIONS[city]
        
        logging.info(f"{city_name} at verileri çekiliyor ve hesaplanıyor...")
        
        # At verilerini çek
        horses = city_function(debug)
        
        if horses:
            # Hesaplama yap
            logging.info(f"{city_name} için hesaplama yapılıyor...")
            calculated_data = process_calculation_for_city(horses, city_name)
            
            # Verileri koşu bazında grupla
            races_data = {}
            for item in calculated_data:
                if item['Koşu'] and 'Koşu' in item['Koşu']:  # Koşu başlığı
                    race_number = item['Koşu'].replace('. Koşu', '').strip()
                    if race_number:
                        races_data[race_number] = {'horses': []}
                elif item['At İsmi']:  # At verisi
                    # En son koşuya at ekle
                    if races_data:
                        last_race = list(races_data.keys())[-1]
                        horse_data = {
                            'at_adi': item['At İsmi'],
                            'skor': float(item['Çıktı']) if item['Çıktı'] != 'geçersiz' else 'Veri yok',
                            'jokey': '',  
                            'yas': '',
                            'agirlik': item.get('Kilo', ''),
                            'son_mesafe': item.get('Son Mesafe', ''),
                            'son_pist': item.get('Son Pist', ''),
                            'son_kilo': item.get('Son Kilo', ''),
                            'son_hipodrom': item.get('Son Hipodrom', ''),
                            'son_derece': item.get('Son Derece', '')
                        }
                        races_data[last_race]['horses'].append(horse_data)
            
            # JSON formatına çevir
            races_list = []
            for race_num in sorted(races_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                races_list.append({
                    'race_number': race_num,
                    'horses': races_data[race_num]['horses']
                })
            
            # İstatistikler
            total_horses = sum(len(race['horses']) for race in races_list)
            valid_horses = sum(1 for race in races_list for horse in race['horses'] 
                              if isinstance(horse['skor'], (int, float)) and horse['skor'] != 'Veri yok')
            success_rate = round((valid_horses / total_horses) * 100, 1) if total_horses > 0 else 0
            
            logging.info(f"[OK] {city_name} tamamlandı: {total_horses} at, {valid_horses} geçerli")
            
            return jsonify({
                'status': 'success',
                'city': city_name,
                'races': races_list,
                'total_horses': total_horses,
                'valid_horses': valid_horses,
                'success_rate': success_rate,
                'source': 'fresh_scrape_and_calc'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'{city_name} için veri çekilemedi'
            }), 500
            
    except Exception as e:
        logging.error(f"Çek ve hesapla hatası: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Dosya indirme"""
    try:
        file_path = os.path.join('static', 'downloads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return "Dosya bulunamadı", 404
    except Exception as e:
        logging.error(f"Dosya indirme hatası: {e}")
        return f"İndirme hatası: {str(e)}", 500

@app.route('/download_csv/<city>')
def download_csv(city):
    """CSV indirme"""
    try:
        # En son oluşturulan CSV dosyasını bul
        downloads_dir = os.path.join('static', 'downloads')
        if not os.path.exists(downloads_dir):
            return "İndirme klasörü bulunamadı", 404
            
        csv_files = [f for f in os.listdir(downloads_dir) if f.startswith(city) and f.endswith('.csv')]
        if not csv_files:
            return "CSV dosyası bulunamadı", 404
            
        # En son dosyayı al
        latest_file = sorted(csv_files)[-1]
        file_path = os.path.join(downloads_dir, latest_file)
        
        return send_file(file_path, as_attachment=True, download_name=f"{city}_analiz_sonuclari.csv")
    except Exception as e:
        logging.error(f"CSV indirme hatası: {e}")
        return f"CSV indirme hatası: {str(e)}", 500

@app.errorhandler(404)
def not_found(error):
    """404 hata sayfası"""
    return jsonify({'error': 'Sayfa bulunamadı', 'status': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 hata sayfası"""
    logging.error(f"Internal server error: {error}")
    return jsonify({'error': 'Sunucu hatası', 'status': 500}), 500

if __name__ == '__main__':
    # Gerekli klasörleri oluştur
    os.makedirs('data', exist_ok=True)
    os.makedirs('static/downloads', exist_ok=True)
    
    # Uygulama başlatma
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logging.info(f"At Yarışı Analiz Sistemi başlatılıyor...")
    logging.info(f"Host: {host}:{port}")
    logging.info(f"Debug Mode: {app.config['DEBUG']}")
    
    # Production'da debug=False, geliştirmede debug=True
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG'],
        threaded=True  # Çoklu istek desteği
    )
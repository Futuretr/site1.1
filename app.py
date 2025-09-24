from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
import pandas as pd
from horse_scraper import (
    get_istanbul_races_and_horse_last_race,
    get_ankara_races_and_horse_last_race,
    get_izmir_races_and_horse_last_race,
    get_adana_races_and_horse_last_race,
    get_bursa_races_and_horse_last_race,
    get_kocaeli_races_and_horse_last_race,
    get_sanliurfa_races_and_horse_last_race,
    get_diyarbakir_races_and_horse_last_race,
    get_elazig_races_and_horse_last_race,
    get_all_cities_data,
    test_system,
    process_calculation_for_city
)

app = Flask(__name__)

# Şehir fonksiyonları mapping
CITY_FUNCTIONS = {
    'istanbul': ('İstanbul', get_istanbul_races_and_horse_last_race),
    'ankara': ('Ankara', get_ankara_races_and_horse_last_race),
    'izmir': ('İzmir', get_izmir_races_and_horse_last_race),
    'adana': ('Adana', get_adana_races_and_horse_last_race),
    'bursa': ('Bursa', get_bursa_races_and_horse_last_race),
    'kocaeli': ('Kocaeli', get_kocaeli_races_and_horse_last_race),
    'sanliurfa': ('Şanlıurfa', get_sanliurfa_races_and_horse_last_race),
    'diyarbakir': ('Diyarbakır', get_diyarbakir_races_and_horse_last_race),
    'elazig': ('Elazığ', get_elazig_races_and_horse_last_race)
}

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/scrape_city', methods=['POST'])
def scrape_city():
    """Tek şehir için at verilerini çek"""
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
        
        print(f"🏇 {city_name} at verileri çekiliyor...")
        
        # At verilerini çek
        horses = city_function(debug)
        
        if horses:
            # CSV dosyası oluştur
            df = pd.DataFrame(horses)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{city}_atlari_{timestamp}.csv"
            filepath = os.path.join('static', 'downloads', filename)
            
            # Downloads klasörü yoksa oluştur
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # İstatistik hesapla
            basarili = sum(1 for h in horses if h['Son Derece'])
            oran = (basarili / len(horses) * 100) if horses else 0
            
            return jsonify({
                'status': 'success',
                'message': f'{city_name} verileri başarıyla çekildi!',
                'data': {
                    'city': city_name,
                    'total_horses': len(horses),
                    'successful': basarili,
                    'success_rate': round(oran, 1),
                    'horses': horses[:10],  # İlk 10 atı önizleme olarak gönder
                    'download_url': f'/download/{filename}',
                    'filename': filename
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'{city_name} için veri çekilemedi'
            }), 500
            
    except Exception as e:
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
            success_rate = (successful / total_horses * 100) if total_horses else 0
            
            return jsonify({
                'status': 'success',
                'has_data': True,
                'message': f'{city_name} için bugünkü veriler mevcut!',
                'data': {
                    'city': city_name,
                    'total_horses': total_horses,
                    'successful': successful,
                    'success_rate': round(success_rate, 1),
                    'filename': saved_filename,
                    'file_date': today
                }
            })
        else:
            return jsonify({
                'status': 'success',
                'has_data': False,
                'message': f'{city_name} için bugünkü veri henüz çekilmemiş',
                'data': {
                    'city': city_name
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/calculate_from_saved', methods=['POST'])
def calculate_from_saved():
    """Kaydedilmiş veriden hesaplama yap"""
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
        
        print(f"🧮 {city_name} için kaydedilmiş veriden hesaplama yapılıyor...")
        
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
                        'jokey': '',  # Bu veri yok ama uyumlu olması için
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
        
        # Hesaplanmış CSV dosyası oluştur
        calc_df = pd.DataFrame(calculated_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        calc_filename = f"{city}_hesaplamali_{timestamp}.csv"
        calc_filepath = os.path.join('static', 'downloads', calc_filename)
        
        # Downloads klasörü yoksa oluştur
        os.makedirs(os.path.dirname(calc_filepath), exist_ok=True)
        
        # Kolonları düzenle
        cols = ['Koşu', 'Çıktı', 'At İsmi', 'Son Mesafe', 'Son Pist', 'Son Kilo', 'Kilo', 'Son Hipodrom']
        for col in cols:
            if col not in calc_df.columns:
                calc_df[col] = ''
        calc_df = calc_df.reindex(columns=cols)
        calc_df.to_csv(calc_filepath, index=False, encoding='utf-8-sig')
        
        # İstatistikler
        total_horses = len(horses)
        successful_data = sum(1 for h in horses if h.get('Son Derece'))
        success_rate = (successful_data / total_horses * 100) if total_horses else 0
        
        # Hesaplanabilir atlar
        hesaplanabilir = sum(1 for d in calculated_data if d['Çıktı'] and d['Çıktı'] != 'geçersiz')
        gecersiz = sum(1 for d in calculated_data if d['Çıktı'] == 'geçersiz')
        
        return jsonify({
            'status': 'success',
            'message': f'{city_name} kaydedilmiş veriden hesaplandı! (Çok hızlı)',
            'city': city_name,
            'races': races_list,
            'total_horses': total_horses,
            'successful_data': successful_data,
            'success_rate': round(success_rate, 1),
            'calculated_horses': hesaplanabilir,
            'invalid_calculations': gecersiz,
            'calculated_download_url': f'/download/{calc_filename}',
            'calculated_filename': calc_filename,
            'source': 'saved_data'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/scrape_and_save', methods=['POST'])
def scrape_and_save():
    """At verilerini çek ve kaydet (hesaplama yapmadan)"""
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
        
        print(f"🏇 {city_name} at verileri çekiliyor ve kaydediliyor...")
        
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
            oran = (basarili / len(horses) * 100) if horses else 0
            
            return jsonify({
                'status': 'success',
                'message': f'{city_name} verileri çekildi ve kaydedildi!',
                'data': {
                    'city': city_name,
                    'total_horses': len(horses),
                    'successful_data': basarili,
                    'success_rate': round(oran, 1),
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
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
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
        
        print(f"🏇 {city_name} at verileri çekiliyor ve hesaplanıyor...")
        
        # At verilerini çek
        horses = city_function(debug)
        
        if horses:
            # Hesaplama yap
            print(f"🧮 {city_name} için hesaplama yapılıyor...")
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
                            'jokey': '',  # Bu veri yok ama uyumlu olması için
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
            
            # Hesaplanmış CSV dosyası oluştur
            calc_df = pd.DataFrame(calculated_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            calc_filename = f"{city}_hesaplamali_{timestamp}.csv"
            calc_filepath = os.path.join('static', 'downloads', calc_filename)
            
            # Downloads klasörü yoksa oluştur
            os.makedirs(os.path.dirname(calc_filepath), exist_ok=True)
            
            # Kolonları düzenle
            cols = ['Koşu', 'Çıktı', 'At İsmi', 'Son Mesafe', 'Son Pist', 'Son Kilo', 'Kilo', 'Son Hipodrom']
            for col in cols:
                if col not in calc_df.columns:
                    calc_df[col] = ''
            calc_df = calc_df.reindex(columns=cols)
            calc_df.to_csv(calc_filepath, index=False, encoding='utf-8-sig')
            
            # Ham veri CSV'si de oluştur
            raw_df = pd.DataFrame(horses)
            raw_filename = f"{city}_ham_veri_{timestamp}.csv"
            raw_filepath = os.path.join('static', 'downloads', raw_filename)
            raw_df.to_csv(raw_filepath, index=False, encoding='utf-8-sig')
            
            # İstatistikler
            basarili = sum(1 for h in horses if h['Son Derece'])
            oran = (basarili / len(horses) * 100) if horses else 0
            
            # Hesaplanabilir atlar
            hesaplanabilir = sum(1 for d in calculated_data if d['Çıktı'] and d['Çıktı'] != 'geçersiz')
            gecersiz = sum(1 for d in calculated_data if d['Çıktı'] == 'geçersiz')
            
            return jsonify({
                'status': 'success',
                'message': f'{city_name} verileri çekildi ve hesaplandı!',
                'city': city_name,
                'races': races_list,
                'total_horses': len(horses),
                'successful_data': basarili,
                'success_rate': round(oran, 1),
                'calculated_horses': hesaplanabilir,
                'invalid_calculations': gecersiz,
                'raw_download_url': f'/download/{raw_filename}',
                'calculated_download_url': f'/download/{calc_filename}',
                'raw_filename': raw_filename,
                'calculated_filename': calc_filename
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'{city_name} için veri çekilemedi'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/scrape_all', methods=['POST'])
def scrape_all_cities():
    """Tüm şehirler için at verilerini çek"""
    try:
        data = request.get_json()
        debug = data.get('debug', False)
        
        print("🏇 TÜM ŞEHİRLER İÇİN AT VERİLERİ ÇEKİLİYOR...")
        
        # Tüm şehirlerden veri çek
        all_horses, city_stats = get_all_cities_data(debug)
        
        if all_horses:
            # CSV dosyası oluştur
            df = pd.DataFrame(all_horses)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tum_sehirler_atlari_{timestamp}.csv"
            filepath = os.path.join('static', 'downloads', filename)
            
            # Downloads klasörü yoksa oluştur
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # Genel istatistik
            toplam_at = len(all_horses)
            toplam_basarili = sum(1 for h in all_horses if h['Son Derece'])
            genel_oran = (toplam_basarili / toplam_at * 100) if toplam_at else 0
            
            return jsonify({
                'status': 'success',
                'message': 'Tüm şehirler için veriler başarıyla çekildi!',
                'data': {
                    'total_horses': toplam_at,
                    'successful': toplam_basarili,
                    'success_rate': round(genel_oran, 1),
                    'city_stats': city_stats,
                    'horses_preview': all_horses[:20],  # İlk 20 atı önizleme
                    'download_url': f'/download/{filename}',
                    'filename': filename
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Hiçbir şehirden veri çekilemedi'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/test', methods=['POST'])
def test_system_api():
    """Sistem testi yap"""
    try:
        print("🧪 SİSTEM TEST EDİLİYOR...")
        horses = test_system()
        
        return jsonify({
            'status': 'success',
            'message': 'Test tamamlandı',
            'data': {
                'test_results': horses[:5] if horses else [],
                'total_found': len(horses) if horses else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Test hatası: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    """CSV dosyasını indir"""
    try:
        filepath = os.path.join('static', 'downloads', filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'Dosya bulunamadı'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_data():
    """Genel veri işleme endpoint'i"""
    try:
        data = request.get_json()
        
        result = {
            'status': 'success',
            'message': 'At çekme sistemi hazır!',
            'available_cities': list(CITY_FUNCTIONS.keys()),
            'data': data
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Dosya yükleme endpoint'i"""
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    # Dosyayı işleme
    # Burada dosyayı mevcut Python kodunuzla işleyebilirsiniz
    
    return jsonify({'message': 'Dosya başarıyla yüklendi ve işlendi'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
import pandas as pd
import math
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
    process_calculation_for_city,
    process_kazanan_cikti_for_json,
    save_kazanan_cikti_csv,
    get_kazanan_data_for_city,
    calculate_time_per_100m,
    calculate_kadapt,
    time_to_seconds
)

app = Flask(__name__)

def clean_json_data(obj):
    """JSON serialize edilebilir hale getir - NaN ve None değerlerini temizle"""
    if isinstance(obj, dict):
        return {k: clean_json_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_data(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif obj is None:
        return None
    else:
        return obj

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

@app.route('/test')
def test():
    return {'status': 'ok', 'message': 'Flask çalışıyor'}

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
        
        print(f"[AT] {city_name} at verileri çekiliyor...")
        
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
            
            # JSON dosyası da kaydet (analiz için gerekli)
            today = datetime.now().strftime('%Y%m%d')
            json_filename = f"{city}_atlari_{today}.json"
            json_filepath = os.path.join('data', json_filename)
            
            # Data klasörü yoksa oluştur
            os.makedirs('data', exist_ok=True)
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            
            print(f"[DOSYA] {city_name} verileri kaydedildi:")
            print(f"   CSV: {filepath}")
            print(f"   JSON: {json_filepath}")
            
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
        
        print(f"[HESAP] {city_name} için kaydedilmiş veriden hesaplama yapılıyor...")
        print(f"[DEBUG] Ham veri sayısı: {len(horses)}")
        print(f"[DEBUG] İlk ham veri örneği: {horses[0] if horses else 'Yok'}")
        
        # Kazanan verilerini oku
        kazanan_data = get_kazanan_data_for_city(city_name)
        print(f"[STAT] {len(kazanan_data)} at için kazanan verisi bulundu")
        
        # Hesaplama yap
        print(f"[HESAP-DEBUG] process_calculation_for_city çağrılıyor...")
        calculated_data = process_calculation_for_city(horses, city_name)
        print(f"[HESAP-DEBUG] Hesaplama tamamlandı. Sonuç sayısı: {len(calculated_data)}")
        
        # Verileri koşu bazında grupla
        races_data = {}
        for item in calculated_data:
            if item['Koşu'] and 'Koşu' in item['Koşu']:  # Koşu başlığı
                race_number = item['Koşu'].replace('. Koşu', '').strip()
                if race_number:
                    races_data[race_number] = {'horses': []}
                    print(f"[KOŞU GRUBU] {race_number}. Koşu oluşturuldu")
            elif item['At İsmi']:  # At verisi
                # En son koşuya at ekle
                if races_data:
                    last_race = list(races_data.keys())[-1]
                    
                    # Bu atın kazanan verilerini kontrol et
                    at_ismi = item['At İsmi']
                    kazanan_info = kazanan_data.get(at_ismi, {})
                    
                    # O atın bugünkü koşu bilgilerini bul
                    horse_today = next((h for h in horses if h.get('At İsmi') == at_ismi), {})
                    bugun_mesafe = horse_today.get('Bugünkü Mesafe', '')
                    bugun_pist = horse_today.get('Bugünkü Pist', '')
                    
                    # Birincinin hesaplanmış derecesini çek
                    calculated_winner_score = ''
                    
                    # PARİSLİ için debug
                    if item['At İsmi'] == 'PARİSLİ':
                        print(f"\n[PARİSLİ DEBUG] kazanan_info: {kazanan_info}")
                        print(f"[PARİSLİ DEBUG] Son Mesafe: {item.get('Son Mesafe')}")
                        print(f"[PARİSLİ DEBUG] Son Pist: {item.get('Son Pist')}")
                    
                    # Birincinin mesafe/pist bilgilerini kontrol et
                    onceki_mesafe = str(kazanan_info.get('onceki_mesafe', '')).strip()
                    onceki_pist = str(kazanan_info.get('onceki_pist', '')).strip()
                    
                    # Eğer birincinin mesafe/pist bilgisi boşsa, ana atın (CAN DENİZİM) bilgilerini kullan
                    # Çünkü birinci at hesaplamasında aynı koşudaki atın mesafe/pist bilgileri kullanılmalı
                    if not onceki_mesafe or onceki_mesafe == 'nan' or onceki_mesafe == '':
                        onceki_mesafe = item.get('Son Mesafe', '')
                        print(f"[MESAFE TAMAMLANDI] {at_ismi} için ana atın mesafesi kullanıldı: {onceki_mesafe}")
                    
                    if not onceki_pist or onceki_pist == 'nan' or onceki_pist == '':
                        onceki_pist = item.get('Son Pist', '')
                        print(f"[PİST TAMAMLANDI] {at_ismi} için ana atın pisti kullanıldı: {onceki_pist}")
                    
                    if kazanan_info.get('kazanan_derece') and onceki_mesafe and onceki_pist:
                        # Pist değerlerini integer'a çevir
                        def pist_to_int(pist):
                            pist = str(pist).lower()
                            if 'çim' in pist:
                                return 1
                            elif 'kum' in pist and 'sentetik' not in pist:
                                return 2
                            elif 'sentetik' in pist:
                                return 3
                            return 1
                        
                        pist1 = pist_to_int(onceki_pist)
                        pist3 = pist_to_int(bugun_pist)
                        
                        # Mesafe değerlerini float'a çevir
                        try:
                            onceki_clean = str(onceki_mesafe).replace(',', '.').strip()
                            bugun_clean = str(bugun_mesafe).replace(',', '.').strip()
                            
                            son_mesafe_float = float(onceki_clean) if onceki_clean and onceki_clean != '' else 1200
                            bugun_mesafe_float = float(bugun_clean) if bugun_clean and bugun_clean != '' else 1200
                        except Exception as e:
                            print(f"[MESAFE HATASI] {at_ismi}: onceki='{onceki_mesafe}', bugun='{bugun_mesafe}', hata: {e}")
                            son_mesafe_float = 1200
                            bugun_mesafe_float = 1200
                        
                        # 1. Mesafe farkını hesapla (pist geçişi calculate_kadapt'ta)
                        derece_saniye = time_to_seconds(kazanan_info.get('kazanan_derece'))
                        if derece_saniye <= 0:
                            continue
                        
                        # Mesafe farklılığını hesapla
                        mesafe_farki = bugun_mesafe_float - son_mesafe_float
                        if mesafe_farki != 0:
                            # Mesafe başına zaman farkı (100m başına)
                            mevcut_100m_sure = derece_saniye / (son_mesafe_float / 100)
                            
                            # Mesafe uzatma/kısaltma faktörü
                            if mesafe_farki > 0:  # Uzun mesafe
                                mesafe_faktoru = 0.04  # 100m başına +0.04 saniye
                            else:  # Kısa mesafe
                                mesafe_faktoru = -0.03  # 100m başına -0.03 saniye
                            
                            # Yeni 100m süresi
                            yeni_100m_sure = mevcut_100m_sure + (abs(mesafe_farki) / 100) * mesafe_faktoru
                            toplam_sure = yeni_100m_sure * (bugun_mesafe_float / 100)
                        else:
                            toplam_sure = derece_saniye
                        
                        if toplam_sure and toplam_sure > 0:
                            # 2. 100m ortalama süreyi hesapla
                            ort_100m_sure = toplam_sure / (bugun_mesafe_float / 100)

                            # 3. Şehir+Pist adaptasyonu hesapla
                            gecmis_sehir = city_name  # Aynı şehir varsayımı
                            hedef_sehir = city_name
                            kadapt = calculate_kadapt(gecmis_sehir, onceki_pist, hedef_sehir, bugun_pist)
                            if item['At İsmi'].strip().upper() == 'DEHLİN':
                                print(f"[KADAPT-DEHLİN] geçmiş: {gecmis_sehir} ({onceki_pist}), hedef: {hedef_sehir} ({bugun_pist}), kadapt: {kadapt}")

                            # 4. Kadapt uygula
                            raw_score = ort_100m_sure
                            adjusted_score = raw_score * kadapt

                            # 5. Kilo etkisi (gerçek kilo)
                            def safe_float_kilo(value, default=50.5):
                                if value is None or str(value).strip() == '':
                                    return default
                                try:
                                    return float(str(value).replace(',', '.'))
                                except (ValueError, TypeError):
                                    return default
                            
                            kilo_onceki = safe_float_kilo(item.get('Son Kilo'), 50.5)
                            kilo_bugun = safe_float_kilo(item.get('Kilo'), 50.5)
                            if item['At İsmi'] == 'PARİSLİ':
                                print(f"[PARISLI-ÇIKTI] onceki_mesafe: {onceki_mesafe}, bugun_mesafe: {bugun_mesafe}, onceki_pist: {onceki_pist}, bugun_pist: {bugun_pist}, kilo_onceki: {kilo_onceki}, kilo_bugun: {kilo_bugun}")
                            kilo_fark = kilo_bugun - kilo_onceki
                            calc_score = adjusted_score - (kilo_fark * 0.02)
                        else:
                            calc_score = None
                        
                        if calc_score and not (math.isnan(calc_score) or math.isinf(calc_score)):
                            calculated_winner_score = f"{calc_score:.2f}"
                    
                    # Skor hesapla: (Çıktı + Birinci Derece) / 2
                    skor_value = 'Veri yok'
                    at_adi = item['At İsmi']
                    
                    # Debug için mevcut değerleri kontrol et
                    print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Çıktı='{item.get('Çıktı', '')}', Birinci='{calculated_winner_score}', Skor='{item.get('Skor', '')}'")
                    
                    try:
                        # Önce hesaplanmış Skor değerini kontrol et
                        skor_str = str(item.get('Skor', '')).strip()
                        if skor_str and skor_str != 'geçersiz' and skor_str != '':
                            try:
                                skor_value = float(skor_str.replace(',', '.'))
                                print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Hesaplanmış skor kullanıldı: {skor_value}")
                            except ValueError:
                                print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Skor parse hatası: {skor_str}")
                                pass
                        
                        # Skor yoksa, Çıktı ve Birinci Derece ile hesapla
                        if skor_value == 'Veri yok':
                            cikti_str = str(item.get('Çıktı', '')).strip()
                            birinci_derece_str = str(calculated_winner_score).strip()
                            
                            if (cikti_str and cikti_str != 'geçersiz' and cikti_str.strip() and
                                birinci_derece_str and birinci_derece_str != 'geçersiz' and birinci_derece_str.strip()):
                                try:
                                    # Boş string kontrolü
                                    cikti_clean = cikti_str.replace(',', '.').strip()
                                    birinci_clean = birinci_derece_str.replace(',', '.').strip()
                                    
                                    if cikti_clean and birinci_clean:
                                        cikti_val = float(cikti_clean)
                                        birinci_derece_val = float(birinci_clean)
                                        
                                        # Skor hesapla: (Çıktı + Birinci Derece) / 2
                                        skor = (cikti_val + birinci_derece_val) / 2
                                        if not (skor != skor):  # NaN kontrolü (NaN != NaN is True)
                                            skor_value = skor
                                            print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Manuel skor hesaplandı: {cikti_val} + {birinci_derece_val} = {skor}")
                                except ValueError as e:
                                    print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Hesaplama hatası: {e}")
                                    pass
                            
                            # Hâlâ yoksa, sadece Çıktı değerini kullan (fallback)
                            if skor_value == 'Veri yok' and cikti_str and cikti_str != 'geçersiz' and cikti_str.strip():
                                try:
                                    cikti_clean = cikti_str.strip()
                                    if cikti_clean:
                                        skor_float = float(cikti_clean)
                                        if not (skor_float != skor_float):  # NaN kontrolü (NaN != NaN is True)
                                            skor_value = skor_float
                                            print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Fallback Çıktı kullanıldı: {skor_value}")
                                except ValueError:
                                    print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Çıktı parse hatası: {cikti_str}")
                                    pass
                    except (ValueError, TypeError) as e:
                        print(f"[SAVED-WEB-SKOR-DEBUG] {at_adi}: Genel hata: {e}")
                        pass
                    
                    horse_data = {
                        'at_adi': item['At İsmi'],
                        'skor': skor_value,
                        'cikti_degeri': item.get('Çıktı', ''),  # Ham çıktı değeri
                        'jokey': '',  # Bu veri yok ama uyumlu olması için
                        'yas': '',
                        'agirlik': item.get('Kilo', ''),
                        'son_mesafe': item.get('Son Mesafe', ''),
                        'son_pist': item.get('Son Pist', ''),
                        'son_kilo': item.get('Son Kilo', ''),
                        'son_hipodrom': item.get('Son Hipodrom', ''),
                        'son_derece': item.get('Son Derece', ''),
                        # Birincinin hesaplanmış derecesi (sadece hesaplananlar)
                        'kazanan_ismi': calculated_winner_score,  # Sadece hesaplanmış değer
                        'kazanan_derece': kazanan_info.get('kazanan_derece', ''),  # Doğru field
                        'kazanan_ganyan': kazanan_info.get('kazanan_ganyan', '')  # Doğru field
                    }
                    races_data[last_race]['horses'].append(horse_data)
        
        # JSON formatına çevir
        races_list = []
        for race_num in sorted(races_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            # Her atın skor değerini debug et
            for horse in races_data[race_num]['horses']:
                print(f"[JSON-DEBUG] {horse.get('at_adi', '')}: skor={horse.get('skor', 'YOK')}")
            
            races_list.append({
                'race_number': race_num,
                'horses': races_data[race_num]['horses']
            })
        
        print(f"[YARISSONUC] Oluşturulan koşu sayısı: {len(races_list)}")
        for i, race in enumerate(races_list):
            print(f"[YARISSONUC] Koşu {race['race_number']}: {len(race['horses'])} at")
        
        # Hesaplanmış CSV dosyası oluştur
        print(f"[DF-DEBUG] DataFrame oluşturuluyor. Veri sayısı: {len(calculated_data)}")
        calc_df = pd.DataFrame(calculated_data)
        print(f"[DF-DEBUG] DataFrame oluşturuldu. Shape: {calc_df.shape}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        calc_filename = f"{city}_hesaplamali_{timestamp}.csv"
        print(f"[DF-DEBUG] CSV dosya adı: {calc_filename}")
        calc_filepath = os.path.join('static', 'downloads', calc_filename)
        
        # Downloads klasörü yoksa oluştur
        os.makedirs(os.path.dirname(calc_filepath), exist_ok=True)
        
        # Önceki yarışın birincisinin hesaplanmış derecesini calculated_data'ya ekle
        for i, item in enumerate(calculated_data):
            if item['At İsmi']:  # At verisi ise
                at_ismi = item['At İsmi']
                kazanan_info = kazanan_data.get(at_ismi, {})
                
                # O atın bugünkü koşu bilgilerini bul
                horse_today = next((h for h in horses if h.get('At İsmi') == at_ismi), {})
                bugun_mesafe = horse_today.get('Bugünkü Mesafe', '')
                bugun_pist = horse_today.get('Bugünkü Pist', '')
                
                # Birincinin hesaplanmış derecesini çek
                calculated_winner_score = ''
                
                # Debug: Kazanan bilgisi kontrolü
                if not kazanan_info.get('kazanan_derece'):
                    print(f"[KAZANAN EKSİK] {at_ismi}: kazanan_derece yok")
                
                # Birincinin mesafe/pist bilgilerini kontrol et
                onceki_mesafe = str(kazanan_info.get('onceki_mesafe', '')).strip()
                onceki_pist = str(kazanan_info.get('onceki_pist', '')).strip()
                
                # Eğer boşsa (CSV'de nan/boş) ana atın bilgilerini kullan (aynı koşu)
                if not onceki_mesafe or onceki_mesafe == 'nan':
                    onceki_mesafe = item.get('Son Mesafe', '')
                if not onceki_pist or onceki_pist == 'nan':
                    onceki_pist = item.get('Son Pist', '')
                
                # Kazanan derecesi ve mesafe/pist bilgileri geçerliyse hesapla
                if (kazanan_info.get('kazanan_derece') and 
                    onceki_mesafe and onceki_pist and 
                    str(onceki_mesafe) != 'nan' and str(onceki_pist) != 'nan' and
                    str(kazanan_info.get('kazanan_derece')) != 'nan'):
                    # Pist değerlerini integer'a çevir
                    def pist_to_int_local(pist):
                        pist = str(pist).lower()
                        if 'çim' in pist:
                            return 1
                        elif 'kum' in pist and 'sentetik' not in pist:
                            return 2
                        elif 'sentetik' in pist:
                            return 3
                        return 1
                    
                    pist1 = pist_to_int_local(onceki_pist)
                    pist3 = pist_to_int_local(bugun_pist)
                    
                    # Mesafe değerlerini float'a çevir
                    try:
                        # Birincinin mesafesi (eski koşu)
                        onceki_mesafe_float = float(str(onceki_mesafe).replace(',', '.'))
                        # Ana atın bugünkü mesafesi (hesaplama için bu kullanılacak)
                        bugun_mesafe_float = float(str(bugun_mesafe).replace(',', '.'))
                    except:
                        onceki_mesafe_float = 1200
                        bugun_mesafe_float = 1200
                    
                    # Debug için
                    print(f"[BİRİNCİ DERECE DEBUG] {at_ismi}")
                    print(f"  kazanan_derece: {kazanan_info.get('kazanan_derece')}")
                    print(f"  onceki_mesafe_float: {onceki_mesafe_float}")
                    print(f"  bugun_mesafe_float: {bugun_mesafe_float}")
                    print(f"  pist1 (önceki): {pist1}, pist3 (bugün): {pist3}")
                    
                    # Mesafe farkını hesapla (pist geçişi calculate_kadapt'ta)
                    derece_saniye = time_to_seconds(kazanan_info.get('kazanan_derece'))
                    if derece_saniye <= 0:
                        continue
                    
                    # Mesafe farklılığını hesapla
                    mesafe_farki = bugun_mesafe_float - onceki_mesafe_float
                    if mesafe_farki != 0:
                        # Mesafe başına zaman farkı (100m başına)
                        mevcut_100m_sure = derece_saniye / (onceki_mesafe_float / 100)
                        
                        # Mesafe uzatma/kısaltma faktörü
                        if mesafe_farki > 0:  # Uzun mesafe
                            mesafe_faktoru = 0.04  # 100m başına +0.04 saniye
                        else:  # Kısa mesafe
                            mesafe_faktoru = -0.03  # 100m başına -0.03 saniye
                        
                        # Yeni 100m süresi
                        yeni_100m_sure = mevcut_100m_sure + (abs(mesafe_farki) / 100) * mesafe_faktoru
                        toplam_sure = yeni_100m_sure * (bugun_mesafe_float / 100)
                    else:
                        toplam_sure = derece_saniye
                    
                    print(f"  toplam_sure: {toplam_sure}")
                    
                    if toplam_sure and toplam_sure > 0:
                        ort_100m_sure = calculate_time_per_100m(toplam_sure, bugun_mesafe_float)
                        
                        # BİRİNCİNİN GERÇEK ŞEHRİNİ KULLAN
                        birinci_sehir = kazanan_info.get('sehir', city_name)  # Kazanan veriden şehir al
                        gecmis_sehir = birinci_sehir  # Birincinin gerçek şehri
                        hedef_sehir = city_name       # Bugünkü koşu şehri
                        
                        print(f"  birinci_sehir: {birinci_sehir}")
                        kadapt = calculate_kadapt(gecmis_sehir, onceki_pist, hedef_sehir, bugun_pist)
                        raw_score = ort_100m_sure
                        adjusted_score = raw_score * kadapt
                        
                        # Gerçek kilo değerlerini kullan (varsayılan değil)
                        def safe_float(value, default=50.5):
                            if value is None or str(value).strip() == '':
                                return default
                            try:
                                return float(str(value).replace(',', '.'))
                            except (ValueError, TypeError):
                                return default
                        
                        kilo_onceki = safe_float(item.get('Son Kilo'), 50.5)  # Atın geçmiş kilosu
                        kilo_bugun = safe_float(item.get('Kilo'), 50.5)      # Atın bugünkü kilosu
                        kilo_fark = kilo_bugun - kilo_onceki
                        calc_score = adjusted_score - (kilo_fark * 0.02)
                        
                        print(f"  kilo_onceki: {kilo_onceki}, kilo_bugun: {kilo_bugun}")
                        print(f"  kilo_fark: {kilo_fark}, kilo_etkisi: {kilo_fark * 0.02}")
                        print(f"  ort_100m_sure: {ort_100m_sure}")
                        print(f"  kadapt: {kadapt}")
                        print(f"  adjusted_score: {adjusted_score}")
                        print(f"  calc_score: {calc_score}")
                    else:
                        calc_score = None
                        print(f"  calc_score: None (toplam_sure geçersiz)")
                    if calc_score and not (math.isnan(calc_score) or math.isinf(calc_score)):
                        calculated_winner_score = f"{calc_score:.2f}"
                        print(f"  calculated_winner_score: {calculated_winner_score}")
                    else:
                        print(f"  calculated_winner_score: '' (geçersiz calc_score)")
                
                calculated_data[i]['Birinci Derece'] = calculated_winner_score  # Sadece hesaplanmış değer
        
        # Skor hesapla: (Çıktı + Birinci Derece) / 2
        for i, item in enumerate(calculated_data):
            skor_value = ""
            at_ismi = item.get('At İsmi', '')
            
            try:
                cikti_str = str(item.get('Çıktı', '')).strip()
                birinci_derece_str = str(item.get('Birinci Derece', '')).strip()
                
                # Debug için log ekle
                if at_ismi and 'Koşu' not in str(item.get('Koşu', '')):
                    print(f"[SKOR-DEBUG] {at_ismi}: Çıktı='{cikti_str}', Birinci='{birinci_derece_str}'")
                
                # Sayısal kontrolü daha güvenli yap
                def is_numeric_string(s):
                    try:
                        float(s.replace(',', '.'))
                        return True
                    except ValueError:
                        return False
                
                # Sadece sayısal değerleri işle, koşu başlıklarını ve geçersizleri atla
                if (cikti_str and cikti_str != 'geçersiz' and is_numeric_string(cikti_str) and
                    birinci_derece_str and birinci_derece_str != 'geçersiz' and is_numeric_string(birinci_derece_str)):
                    
                    cikti_val = float(cikti_str.replace(',', '.'))
                    birinci_derece_val = float(birinci_derece_str.replace(',', '.'))
                    
                    # Skor hesapla: (Çıktı + Birinci Derece) / 2
                    skor = (cikti_val + birinci_derece_val) / 2
                    skor_value = f"{skor:.2f}"
                    
                    if at_ismi and 'Koşu' not in str(item.get('Koşu', '')):
                        print(f"[SKOR-DEBUG] {at_ismi}: {cikti_val} + {birinci_derece_val} = {cikti_val + birinci_derece_val}, /2 = {skor}, Final: {skor_value}")
                    
            except (ValueError, TypeError) as e:
                if at_ismi and 'Koşu' not in str(item.get('Koşu', '')):
                    print(f"[SKOR-HATA] {at_ismi}: {e}")
                skor_value = ""
            
            calculated_data[i]['Skor'] = skor_value
        
        # DataFrame'i yeniden oluştur
        calc_df = pd.DataFrame(calculated_data)
        
        # Kolonları düzenle - Skor'u Birinci Derece'den sonra ekle
        cols = ['Koşu', 'Çıktı', 'Birinci Derece', 'Skor', 'At İsmi', 'Son Mesafe', 'Son Pist', 'Son Kilo', 'Kilo', 'Son Hipodrom']
        for col in cols:
            if col not in calc_df.columns:
                calc_df[col] = ''
        calc_df = calc_df.reindex(columns=cols)
        
        print(f"[CSV-DEBUG] CSV dosyası oluşturuluyor: {calc_filepath}")
        print(f"[CSV-DEBUG] DataFrame shape: {calc_df.shape}")
        
        try:
            calc_df.to_csv(calc_filepath, index=False, encoding='utf-8-sig')
            print(f"[CSV-SUCCESS] CSV dosyası başarıyla oluşturuldu: {calc_filename}")
        except Exception as csv_error:
            print(f"[CSV-ERROR] CSV dosyası oluşturulamadı: {csv_error}")
            raise csv_error
        
        # İstatistikler
        total_horses = len(horses)
        successful_data = sum(1 for h in horses if h.get('Son Derece'))
        success_rate = (successful_data / total_horses * 100) if total_horses else 0
        
        # Hesaplanabilir atlar
        hesaplanabilir = sum(1 for d in calculated_data if d['Çıktı'] and d['Çıktı'] != 'geçersiz')
        gecersiz = sum(1 for d in calculated_data if d['Çıktı'] == 'geçersiz')
        
        # JSON response'u temizle (NaN değerlerini kaldır)
        response_data = {
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
        }
        
        return jsonify(clean_json_data(response_data))
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        trace = traceback.format_exc()
        print(f"[HATA] calculate_from_saved exception: {error_msg}")
        print(f"[TRACEBACK] {trace}")
        
        # Console'a da yazdır
        import sys
        sys.stderr.write(f"FLASK ERROR: {error_msg}\n")
        sys.stderr.write(f"FLASK TRACEBACK: {trace}\n")
        sys.stderr.flush()
        
        return jsonify({
            'status': 'error',
            'message': f'Hata: {error_msg}'
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
        
        print(f"[AT] {city_name} at verileri çekiliyor ve kaydediliyor...")
        
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
            
            # KAZANAN ÇIKTI VERİLERİNİ ÇEK
            print(f"[KAZANAN] {city_name} için kazanan verileri çekiliyor...")
            kazanan_data = process_kazanan_cikti_for_json(saved_filepath, city_name, today)
            kazanan_csv_path = save_kazanan_cikti_csv(kazanan_data, city_name, today)
            
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
        
        print(f"[AT] {city_name} at verileri çekiliyor ve hesaplanıyor...")
        
        # At verilerini çek
        horses = city_function(debug)
        
        if horses:
            # Hesaplama yap
            print(f"[HESAP] {city_name} için hesaplama yapılıyor...")
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
                        # Skor değerini al (hesaplanmış Skor değeri)
                        skor_value = 'Veri yok'
                        at_adi = item['At İsmi']
                        
                        # Debug için mevcut değerleri kontrol et
                        print(f"[WEB-SKOR-DEBUG] {at_adi}: Çıktı='{item.get('Çıktı', '')}', Birinci='{item.get('Birinci Derece', '')}', Skor='{item.get('Skor', '')}'")
                        
                        try:
                            # Önce Skor değerini kontrol et (önceden hesaplanmışsa)
                            skor_str = str(item.get('Skor', '')).strip()
                            if skor_str and skor_str != 'geçersiz' and skor_str != '':
                                try:
                                    skor_value = float(skor_str.replace(',', '.'))
                                    print(f"[WEB-SKOR-DEBUG] {at_adi}: Hesaplanmış skor kullanıldı: {skor_value}")
                                except ValueError:
                                    print(f"[WEB-SKOR-DEBUG] {at_adi}: Skor parse hatası: {skor_str}")
                                    pass
                            
                            # Skor yoksa, fallback olarak Çıktı değerini kullan
                            if skor_value == 'Veri yok':
                                cikti_str = str(item.get('Çıktı', '')).strip()
                                if cikti_str and cikti_str != 'geçersiz':
                                    try:
                                        skor_float = float(cikti_str.replace(',', '.'))
                                        # NaN kontrolü
                                        if not (skor_float != skor_float):  # NaN kontrolü (NaN != NaN is True)
                                            skor_value = skor_float
                                            print(f"[WEB-SKOR-DEBUG] {at_adi}: Fallback Çıktı kullanıldı: {skor_value}")
                                    except ValueError:
                                        print(f"[WEB-SKOR-DEBUG] {at_adi}: Çıktı parse hatası: {cikti_str}")
                                        pass
                        except (ValueError, TypeError) as e:
                            print(f"[WEB-SKOR-DEBUG] {at_adi}: Genel hata: {e}")
                            pass
                        
                        horse_data = {
                            'at_adi': item['At İsmi'],
                            'skor': skor_value,
                            'cikti_degeri': item.get('Çıktı', ''),  # Ham çıktı değeri
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
            
            # Skor hesapla: (Çıktı + Birinci Derece) / 2
            for i, item in enumerate(calculated_data):
                skor_value = ""
                try:
                    cikti_str = str(item.get('Çıktı', '')).strip()
                    birinci_derece_str = str(item.get('Birinci Derece', '')).strip()
                    
                    # Sayısal kontrolü daha güvenli yap
                    def is_numeric_string(s):
                        try:
                            float(s.replace(',', '.'))
                            return True
                        except ValueError:
                            return False
                    
                    # Sadece sayısal değerleri işle, koşu başlıklarını ve geçersizleri atla
                    if (cikti_str and cikti_str != 'geçersiz' and is_numeric_string(cikti_str) and
                        birinci_derece_str and birinci_derece_str != 'geçersiz' and is_numeric_string(birinci_derece_str)):
                        
                        cikti_val = float(cikti_str.replace(',', '.'))
                        birinci_derece_val = float(birinci_derece_str.replace(',', '.'))
                        
                        # Skor hesapla: (Çıktı + Birinci Derece) / 2
                        skor = (cikti_val + birinci_derece_val) / 2
                        skor_value = f"{skor:.2f}"
                        
                except (ValueError, TypeError):
                    skor_value = ""
                
                calculated_data[i]['Skor'] = skor_value
            
            # Kolonları düzenle - Skor'u Birinci Derece'den sonra ekle
            cols = ['Koşu', 'Çıktı', 'Birinci Derece', 'Skor', 'At İsmi', 'Son Mesafe', 'Son Pist', 'Son Kilo', 'Kilo', 'Son Hipodrom']
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
            
            # JSON response'u temizle (NaN değerlerini kaldır)
            response_data = {
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
            }
            
            return jsonify(clean_json_data(response_data))
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
        
        print("[AT] TÜM ŞEHİRLER İÇİN AT VERİLERİ ÇEKİLİYOR...")
        
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
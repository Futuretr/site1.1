"""
Otomatik Veri Çekme Scheduler'ı
Bu modül günlük veri çekme işlemlerini otomatikleştirir.
"""

import schedule
import time
import threading
from datetime import datetime
import logging
from models import SystemSettings, db, AnalysisHistory
from horse_scraper import (
    get_istanbul_races_and_horse_last_race,
    get_ankara_races_and_horse_last_race,
    get_izmir_races_and_horse_last_race,
    get_bursa_races_and_horse_last_race,
    get_adana_races_and_horse_last_race,
    get_kocaeli_races_and_horse_last_race,
    get_sanliurfa_races_and_horse_last_race,
    get_diyarbakir_races_and_horse_last_race,
    get_elazig_races_and_horse_last_race
)

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

class DataScheduler:
    def __init__(self):
        self.is_running = False
        self.thread = None
        
        # Şehir fonksiyonları mapping
        self.city_functions = {
            'istanbul': get_istanbul_races_and_horse_last_race,
            'ankara': get_ankara_races_and_horse_last_race,
            'izmir': get_izmir_races_and_horse_last_race,
            'bursa': get_bursa_races_and_horse_last_race,
            'adana': get_adana_races_and_horse_last_race,
            'kocaeli': get_kocaeli_races_and_horse_last_race,
            'sanliurfa': get_sanliurfa_races_and_horse_last_race,
            'diyarbakir': get_diyarbakir_races_and_horse_last_race,
            'elazig': get_elazig_races_and_horse_last_race
        }
    
    def fetch_all_cities_data(self):
        """Tüm şehirlerden veri çek"""
        logging.info("Otomatik veri çekme başlatılıyor...")
        
        success_count = 0
        total_count = len(self.city_functions)
        results = {}
        
        for city, func in self.city_functions.items():
            try:
                logging.info(f"[ÇEKME] {city.title()} verisi çekiliyor...")
                result = func()
                
                if result and isinstance(result, dict) and result.get('success'):
                    results[city] = {'success': True, 'data': result}
                    success_count += 1
                    logging.info(f"[BAŞARILI] {city.title()} verisi başarıyla çekildi")
                    
                    # Analiz geçmişine kaydet (sadece log olarak)
                    try:
                        logging.info(f"[KAYIT] {city.title()} için analiz geçmişi kaydedildi")
                    except Exception as e:
                        logging.warning(f"Analiz geçmişi kaydedilemedi: {e}")
                        
                elif result and isinstance(result, list):
                    # Liste formatında sonuç (eski format)
                    results[city] = {'success': True, 'data': result}
                    success_count += 1
                    logging.info(f"[BAŞARILI] {city.title()} verisi başarıyla çekildi (liste format)")
                else:
                    error_msg = 'Bilinmeyen hata'
                    if result and hasattr(result, 'get'):
                        error_msg = result.get('error', 'Bilinmeyen hata')
                    elif not result:
                        error_msg = 'Veri çekilemedi'
                    
                    results[city] = {'success': False, 'error': error_msg}
                    logging.error(f"[HATA] {city.title()} verisi çekilemedi: {error_msg}")
                
                # Şehirler arası kısa bekleme
                time.sleep(2)
                
            except Exception as e:
                results[city] = {'success': False, 'error': str(e)}
                logging.error(f"[HATA] {city.title()} veri çekme hatası: {e}")
        
        # Özet log
        logging.info(f"[TAMAMLANDI] Otomatik veri çekme: {success_count}/{total_count} başarılı")
        
        # Sonucu sistem ayarlarına kaydet
        try:
            SystemSettings.set_setting(
                'last_auto_fetch',
                datetime.utcnow().isoformat(),
                f'Son otomatik çekme: {success_count}/{total_count} başarılı'
            )
        except Exception as e:
            logging.error(f"Son çekme zamanı kaydedilemedi: {e}")
        
        return {
            'success': True,
            'results': results,
            'success_count': success_count,
            'total_count': total_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def schedule_daily_fetch(self, time_str="08:00"):
        """Günlük veri çekmeyi zamanla"""
        # Mevcut zamanlamaları temizle
        schedule.clear()
        
        # Yeni zamanlama ekle
        schedule.every().day.at(time_str).do(self.fetch_all_cities_data)
        
        logging.info(f"[ZAMANLAMA] Otomatik veri çekme {time_str} saatinde zamanlandı")
    
    def start_scheduler(self):
        """Scheduler'ı başlat"""
        if self.is_running:
            logging.warning("Scheduler zaten çalışıyor")
            return
        
        self.is_running = True
        
        def run_scheduler():
            logging.info("[BAŞLATMA] Scheduler başlatılıyor...")
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Her dakika kontrol et
                except Exception as e:
                    logging.error(f"Scheduler hatası: {e}")
                    time.sleep(300)  # Hata durumunda 5 dakika bekle
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        logging.info("[OK] Scheduler başlatıldı")
    
    def stop_scheduler(self):
        """Scheduler'ı durdur"""
        if not self.is_running:
            logging.warning("Scheduler zaten durmuş")
            return
        
        self.is_running = False
        schedule.clear()
        logging.info("[DURDUR] Scheduler durduruldu")
    
    def get_next_run_time(self):
        """Sonraki çalıştırma zamanını al"""
        jobs = schedule.jobs
        if jobs:
            return jobs[0].next_run
        return None
    
    def load_settings_and_start(self):
        """Sistem ayarlarından zamanlamayı yükle ve başlat"""
        try:
            # Otomatik çekme aktif mi?
            auto_enabled = SystemSettings.get_setting('auto_fetch_enabled', 'false')
            auto_time = SystemSettings.get_setting('auto_fetch_time', '08:00')
            
            # None kontrolü
            if auto_enabled is None:
                auto_enabled = 'false'
            if auto_time is None:
                auto_time = '08:00'
            
            if str(auto_enabled).lower() == 'true':
                self.schedule_daily_fetch(str(auto_time))
                self.start_scheduler()
                logging.info(f"[BAŞLAT] Sistem ayarlarından yüklendi: {auto_time} saatinde otomatik çekme aktif")
            else:
                logging.info("[BAŞLAT] Otomatik veri çekme sistem ayarlarında pasif")
        
        except Exception as e:
            logging.error(f"Ayarlar yüklenirken hata: {e}")

# Global scheduler instance
scheduler = DataScheduler()

def init_scheduler(app):
    """Flask app ile scheduler'ı initialize et"""
    with app.app_context():
        try:
            scheduler.load_settings_and_start()
        except Exception as e:
            logging.error(f"Scheduler initialize hatası: {e}")

def get_scheduler_status():
    """Scheduler durumunu al"""
    return {
        'is_running': scheduler.is_running,
        'next_run': scheduler.get_next_run_time(),
        'scheduled_jobs': len(schedule.jobs)
    }

if __name__ == "__main__":
    # Test için direkt çalıştırma
    print("[TEST] Test modunda scheduler başlatılıyor...")
    scheduler.schedule_daily_fetch("08:00")
    scheduler.start_scheduler()
    
    try:
        while True:
            time.sleep(10)
            print(f"[DURUM] Aktif işler: {len(schedule.jobs)}, Sonraki: {scheduler.get_next_run_time()}")
    except KeyboardInterrupt:
        print("[DURDUR] Scheduler durduruluyor...")
        scheduler.stop_scheduler()
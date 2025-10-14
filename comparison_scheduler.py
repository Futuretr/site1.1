#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OTOMATIK GECE KARŞILAŞTIRMA SERVİSİ
Gece saat 00:30'da çalışarak önceki günün sonuçlarını tahminlerle karşılaştırır
"""

import schedule
import time
import logging
from datetime import datetime
from results_scraper import compare_predictions_with_results, save_comparison_results

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comparison_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_midnight_comparison():
    """
    Gece yarısı sonrası karşılaştırma işlemi
    """
    logger.info("🌙 Otomatik gece karşılaştırması başlatılıyor...")
    
    cities = ['bursa', 'istanbul', 'ankara', 'izmir', 'adana', 'kocaeli', 'sanliurfa', 'diyarbakir', 'elazig']
    
    overall_results = {
        'timestamp': datetime.now().isoformat(),
        'total_cities': 0,
        'successful_cities': 0,
        'total_races': 0,
        'total_successful_predictions': 0,
        'city_results': {}
    }
    
    for city in cities:
        try:
            logger.info(f"📊 {city.upper()} sonuçları kontrol ediliyor...")
            
            comparison = compare_predictions_with_results(city, debug=True)
            
            if 'error' not in comparison:
                overall_results['total_cities'] += 1
                overall_results['successful_cities'] += 1
                overall_results['total_races'] += comparison['total_races']
                overall_results['total_successful_predictions'] += comparison['successful_predictions']
                
                success_rate = comparison['success_rate']
                
                overall_results['city_results'][city] = {
                    'success_rate': success_rate,
                    'total_races': comparison['total_races'],
                    'successful_predictions': comparison['successful_predictions'],
                    'status': 'success'
                }
                
                # Sonuçları kaydet
                save_comparison_results(city, comparison)
                
                logger.info(f"✅ {city.upper()}: %{success_rate:.1f} başarı ({comparison['successful_predictions']}/{comparison['total_races']})")
                
            else:
                overall_results['total_cities'] += 1
                overall_results['city_results'][city] = {
                    'error': comparison['error'],
                    'status': 'error'
                }
                logger.warning(f"❌ {city.upper()}: {comparison['error']}")
                
        except Exception as e:
            logger.error(f"💥 {city.upper()} hatası: {str(e)}")
            overall_results['total_cities'] += 1
            overall_results['city_results'][city] = {
                'error': str(e),
                'status': 'exception'
            }
    
    # Genel başarı oranını hesapla
    if overall_results['total_races'] > 0:
        overall_success_rate = (overall_results['total_successful_predictions'] / overall_results['total_races']) * 100
        overall_results['overall_success_rate'] = overall_success_rate
        
        logger.info(f"🎯 GENEL SONUÇ: %{overall_success_rate:.1f} başarı oranı")
        logger.info(f"📈 TOPLAM: {overall_results['total_successful_predictions']}/{overall_results['total_races']} doğru tahmin")
    else:
        overall_results['overall_success_rate'] = 0
        logger.warning("⚠️ Hiçbir şehirden sonuç alınamadı")
    
    # Genel sonuçları kaydet
    try:
        import json
        import os
        
        results_dir = "data/daily_comparisons"
        os.makedirs(results_dir, exist_ok=True)
        
        today_str = datetime.now().strftime('%Y%m%d')
        summary_file = f"{results_dir}/daily_summary_{today_str}.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(overall_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Günlük özet kaydedildi: {summary_file}")
        
    except Exception as e:
        logger.error(f"💾 Özet kayıt hatası: {str(e)}")
    
    logger.info("🏁 Otomatik gece karşılaştırması tamamlandı!")

def start_scheduler():
    """
    Zamanlamacıyı başlat
    """
    logger.info("⏰ Otomatik karşılaştırma zamanlamacısı başlatılıyor...")
    logger.info("🕐 Günlük 00:30'da çalışacak şekilde ayarlandı")
    
    # Her gece 00:30'da çalıştır
    schedule.every().day.at("00:30").do(run_midnight_comparison)
    
    # Test amaçlı - her 5 dakikada bir çalıştır (geliştirme için)
    # schedule.every(5).minutes.do(run_midnight_comparison)
    
    logger.info("✅ Zamanlamacı aktif! Ctrl+C ile durdurun.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
    except KeyboardInterrupt:
        logger.info("⛔ Zamanlamacı durduruldu.")

def run_manual_test():
    """
    Manuel test çalıştırma
    """
    logger.info("🧪 Manuel test başlatılıyor...")
    run_midnight_comparison()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_manual_test()
    else:
        start_scheduler()
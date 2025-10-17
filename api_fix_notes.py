"""
Analiz API düzeltmesi - sadece success field'ları düzeltildi
"""

# Bu dosya sadece hangi değişikliklerin yapılması gerektiğini gösterir

# 1. /api/scrape_city endpoint'inde başarılı yanıt:
success_response = {
    'success': True,  # ← EKLENEN
    'status': 'success',
    'message': 'Şehir verileri başarıyla çekildi!',
    'data': {
        # ... mevcut data
    }
}

# 2. /api/scrape_city endpoint'inde hata yanıtları:
error_response_1 = {
    'success': False,  # ← EKLENEN
    'status': 'error',
    'error': 'Desteklenmeyen şehir',  # ← EKLENEN
    'message': 'Hata mesajı'
}

error_response_2 = {
    'success': False,  # ← EKLENEN
    'status': 'error', 
    'error': 'Veri çekilemedi',  # ← EKLENEN
    'message': 'Hata mesajı'
}

# Bu değişiklikler yapıldıktan sonra frontend'deki:
# if (data.success) kontrolü çalışacak

print("API düzeltme notları hazır!")
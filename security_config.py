import os
import secrets
from datetime import timedelta

class SecurityConfig:
    """Güvenlik konfigürasyonu"""
    
    # Güvenli SECRET_KEY üretimi
    @staticmethod
    def get_secret_key():
        """Environment'dan alır, yoksa güvenli bir tane üretir"""
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            # Güvenli rastgele key üret
            secret_key = secrets.token_urlsafe(32)
            print(f"⚠️  UYARI: SECRET_KEY environment variable'dan alınamadı!")
            print(f"🔐 Geçici key oluşturuldu. Üretim için environment'a ekleyin:")
            print(f"   export SECRET_KEY='{secret_key}'")
        return secret_key
    
    # Session güvenliği
    SESSION_COOKIE_SECURE = True  # HTTPS'de çalışır
    SESSION_COOKIE_HTTPONLY = True  # JavaScript erişimini engelle
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF saldırılarını zorlaştır
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 2 saat session süresi
    
    # CSRF koruması
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 saat CSRF token süresi
    
    # File upload güvenliği
    ALLOWED_EXTENSIONS = {'csv', 'json', 'txt'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB maksimum dosya boyutu
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'  # Production'da Redis kullan
    
    # SQL Injection koruması
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False}
    }

class SecurityHeaders:
    """HTTP güvenlik başlıkları"""
    
    @staticmethod
    def apply_security_headers(response):
        """Response'a güvenlik başlıklarını ekle"""
        
        # XSS koruması
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CSP (Content Security Policy)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HTTPS yönlendirmesi (production'da)
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer koruması
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

def validate_input(input_data, input_type='string', max_length=None, allowed_chars=None):
    """Güvenli input validasyonu"""
    
    if not input_data:
        return None
        
    # String validasyonu
    if input_type == 'string':
        # XSS koruması - tehlikeli karakterleri temizle
        import html
        cleaned = html.escape(str(input_data).strip())
        
        if max_length and len(cleaned) > max_length:
            raise ValueError(f"Input çok uzun (max: {max_length})")
            
        if allowed_chars:
            if not all(c in allowed_chars for c in cleaned):
                raise ValueError("Geçersiz karakterler bulundu")
                
        return cleaned
    
    # Dosya adı validasyonu  
    elif input_type == 'filename':
        import re
        # Güvenli dosya adı pattern'i
        if not re.match(r'^[a-zA-Z0-9._-]+$', input_data):
            raise ValueError("Geçersiz dosya adı")
        return input_data
    
    # Şehir adı validasyonu
    elif input_type == 'city':
        allowed_cities = ['istanbul', 'ankara', 'izmir', 'bursa', 'adana', 
                         'kocaeli', 'sanliurfa', 'diyarbakir', 'elazig']
        if input_data.lower() not in allowed_cities:
            raise ValueError("Geçersiz şehir adı")
        return input_data.lower()
    
    return input_data

def secure_file_upload(file, upload_folder='static/uploads'):
    """Güvenli dosya yükleme"""
    import os
    from werkzeug.utils import secure_filename
    
    if not file or file.filename == '':
        raise ValueError("Geçersiz dosya")
    
    # Dosya uzantısı kontrolü
    filename = secure_filename(file.filename)
    if not filename or '.' not in filename:
        raise ValueError("Geçersiz dosya adı")
    
    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in SecurityConfig.ALLOWED_EXTENSIONS:
        raise ValueError(f"İzin verilmeyen dosya türü: {extension}")
    
    # Güvenli dosya adı oluştur
    safe_filename = f"{secrets.token_hex(8)}_{filename}"
    
    # Dosya boyutu kontrolü (client-side kontrolün yanı sıra)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > SecurityConfig.MAX_CONTENT_LENGTH:
        raise ValueError("Dosya çok büyük")
    
    return safe_filename

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """Güvenlik olaylarını logla"""
    import logging
    from datetime import datetime
    
    # Güvenlik logger'ı oluştur
    security_logger = logging.getLogger('security')
    if not security_logger.handlers:
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        security_logger.addHandler(handler)
        security_logger.setLevel(logging.WARNING)
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event': event_type,
        'user_id': user_id,
        'ip': ip_address,
        'details': details
    }
    
    security_logger.warning(f"SECURITY EVENT: {log_data}")
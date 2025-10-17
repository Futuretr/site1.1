# 🔒 Güvenlik Kılavuzu - Üretim Ortamı

## ⚠️ KRİTİK GÜVENLİK DÜZELTMELERİ

### 🔑 1. Environment Variables (.env)
```bash
# .env dosyası oluşturun ve şu değerleri ekleyin:
SECRET_KEY=your-super-secure-secret-key-here-32-chars-minimum
FLASK_ENV=production
SQLALCHEMY_DATABASE_URI=sqlite:///horse_analysis.db

# Güvenli şifre gereksinimleri
MIN_PASSWORD_LENGTH=8
REQUIRE_SPECIAL_CHARS=true

# Rate limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379

# Email (opsiyonel)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 🛡️ 2. Güvenlik Paketleri Kurulumu
```bash
pip install -r requirements_security.txt
```

### 🔒 3. HTTPS Konfigürasyonu
```python
# Production'da HTTPS zorunlu
if os.environ.get('FLASK_ENV') == 'production':
    from flask_talisman import Talisman
    Talisman(app, force_https=True)
```

### 🔥 4. Firewall Kuralları
```bash
# Sadece gerekli portları açın
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP (HTTPS'e yönlendir)
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 📊 5. Güvenlik Monitoring
```bash
# Güvenlik loglarını kontrol edin
tail -f security.log

# Şüpheli aktiviteleri izleyin
grep "SECURITY EVENT" security.log
```

## 🛠️ YAPILMASI GEREKENLER

### ✅ Tamamlanan Güvenlik Düzeltmeleri:

1. **SECRET_KEY Güvenliği**
   - ✅ Hard-coded secret key kaldırıldı
   - ✅ Environment variable kullanımı eklendi
   - ✅ Otomatik güvenli key üretimi

2. **Input Validation**
   - ✅ XSS koruması (HTML escape)
   - ✅ SQL injection koruması (parametrized queries)
   - ✅ File upload güvenliği
   - ✅ Form validasyonları güçlendirildi

3. **Session Security**
   - ✅ Secure cookie flags
   - ✅ HttpOnly cookies
   - ✅ Session timeout
   - ✅ CSRF protection

4. **Password Security**
   - ✅ Strong password requirements
   - ✅ Secure hashing (PBKDF2)
   - ✅ Reset token security

5. **API Security**
   - ✅ Authentication required
   - ✅ Rate limiting foundation
   - ✅ Input sanitization
   - ✅ Security logging

### 🚨 ACİL YAPILMASI GEREKENLER:

1. **Environment Setup**
   ```bash
   # 1. .env dosyasını oluşturun
   cp .env.example .env
   
   # 2. SECRET_KEY'i değiştirin
   python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env
   
   # 3. Database permissions
   chmod 600 instance/horse_analysis.db
   ```

2. **SSL Certificate**
   ```bash
   # Let's Encrypt ile ücretsiz SSL
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Backup Strategy**
   ```bash
   # Database backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   cp instance/horse_analysis.db "backups/db_backup_$DATE.db"
   
   # Günlük cron job
   0 2 * * * /path/to/backup-script.sh
   ```

### ⚡ PERFORMANS & GÜVENLİK

1. **Redis Cache (Önerilen)**
   ```bash
   sudo apt install redis-server
   pip install redis flask-caching
   ```

2. **Nginx Reverse Proxy**
   ```nginx
   server {
       listen 443 ssl;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       # Security headers
       add_header X-Frame-Options DENY;
       add_header X-Content-Type-Options nosniff;
   }
   ```

### 🔍 GÜVENLİK TESTLERİ

1. **Güvenlik Taraması**
   ```bash
   # Kod güvenlik taraması
   bandit -r . -f json -o security_report.json
   
   # Dependency güvenlik kontrolü
   safety check
   ```

2. **Penetrasyon Testi**
   ```bash
   # OWASP ZAP ile test
   zap-cli quick-scan --self-contained http://localhost:5000
   ```

### 📈 MONİTORİNG

1. **Log Rotation**
   ```bash
   # /etc/logrotate.d/flask-app
   /path/to/app/*.log {
       daily
       rotate 30
       compress
       delaycompress
       notifempty
       copytruncate
   }
   ```

2. **Uptime Monitoring**
   - UptimeRobot veya Pingdom kullanın
   - Critical endpoint'leri izleyin

## 🎯 ÖNCELİKLER

### 🔴 YÜksek Öncelik (Hemen yapın):
1. SECRET_KEY environment variable'a taşıma
2. HTTPS aktifleştirme
3. Database backup stratejisi
4. Güvenlik loglarını aktifleştirme

### 🟡 Orta Öncelik (1-2 hafta):
1. Redis cache implementasyonu
2. Rate limiting aktifleştirme
3. Email notification sistemi
4. Automated security scanning

### 🟢 Düşük Öncelik (1 ay+):
1. Advanced monitoring
2. Load balancing
3. Container deployment
4. CI/CD pipeline security

## 📞 DESTEK

Güvenlik sorunları için:
- Güvenlik loglarını kontrol edin: `tail -f security.log`
- Sistem durumunu kontrol edin: `systemctl status your-app`
- Database backup'ını kontrol edin: `ls -la backups/`

⚠️ **UYARI**: Bu düzeltmeler production ortamında test edildikten sonra uygulanmalıdır!
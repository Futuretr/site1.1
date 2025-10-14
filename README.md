# 🏇 At Yarışı Veri Çekme Web Uygulaması

Türkiye'deki tüm hipodromlardan günlük at yarışı verilerini çeken Flask web uygulaması.

## Özellikler

- 🏇 **9 Şehirden At Verisi**: İstanbul, Ankara, İzmir, Adana, Bursa, Kocaeli, Şanlıurfa, Diyarbakır, Elazığ
- 🌍 **Toplu Veri Çekme**: Tüm şehirlerden tek seferde veri çek
- 📊 **İstatistik Gösterimi**: Başarı oranları ve detaylı raporlar
- 📥 **CSV İndir**: Çekilen verileri CSV formatında indir
- 🧪 **Sistem Testi**: Kod işlevselliğini test et
- 📱 **Responsive Tasarım**: Mobil uyumlu modern arayüz
- 🔍 **Debug Modu**: Detaylı çekme işlemi takibi

### ✨ YENİ! Sonuç Karşılaştırma Sistemi
- 🌙 **Otomatik Gece Kontrolü**: Saat 00:30'da önceki günün sonuçlarını çeker
- ⚖️ **Tahmin Doğrulaması**: Yapılan tahminleri gerçek sonuçlarla karşılaştırır  
- 📈 **Başarı Oranı**: Koşu ve şehir bazında detaylı performans analizi
- 🎯 **Doğruluk Takibi**: Her tahmin için doğru/yanlış durumu ve detayları
- 📋 **Karşılaştırma Raporları**: Excel formatında indirilebilir sonuç analizleri

## Kurulum

1. **Gereksinimları yükleyin:**
```bash
pip install -r requirements.txt
```

2. **Uygulamayı çalıştırın:**
```bash
python app.py
```

3. **Tarayıcıda açın:**
```
http://localhost:5000
```

## Kullanım

### 🏇 Tek Şehir Veri Çekme
1. Dropdown menüden şehir seçin
2. İsteğe bağlı debug modunu açın
3. "At Verilerini Çek" butonuna tıklayın
4. İstatistikleri görün ve CSV dosyasını indirin

### 🌍 Tüm Şehirler Veri Çekme  
1. "Tüm Şehirlerin Verilerini Çek" butonuna tıklayın
2. İşlem tamamlanınca tüm şehirlerin birleşik CSV'ini indirin

### 🧪 Sistem Testi
"Test Et" butonu ile sistemin çalıştığını kontrol edin.

### ⚖️ Sonuç Karşılaştırma (YENİ!)
1. **Dünkü Sonuçları Çek**: Bir önceki günün koşu sonuçlarını görüntüle
2. **Karşılaştır**: Yapılan tahminleri gerçek sonuçlarla karşılaştır
3. **Tümünü Karşılaştır**: Tüm şehirler için toplu karşılaştırma yap

#### Otomatik Gece Kontrolü
Sistem her gece saat 00:30'da otomatik olarak:
- Bir önceki günün sonuçlarını çeker
- Yapılan tahminlerle karşılaştırır  
- Başarı oranlarını hesaplar
- Sonuçları JSON formatında kaydeder

**Manuel Zamanlamacı Başlatma:**
```bash
# Otomatik zamanlamacıyı başlat (gece 00:30'da çalışır)
python comparison_scheduler.py

# Manuel test çalıştır
python comparison_scheduler.py test
```

## 🚀 Hızlı Başlangıç

1. **Projeyi klonlayın ve kurulum yapın**
2. **Flask uygulamasını başlatın**
3. **Bir şehir seçip "Veri Çek" butonuna basın**
4. **"Analiz Yap" ile tahminleri görün**  
5. **Ertesi gün "Dünkü Sonuçları Çek" ile sonuçları kontrol edin**
6. **"Karşılaştır" ile tahmin başarınızı ölçün**

## 📊 Örnek Kullanım Akışı

```
1. Bugün: Bursa için veri çek → Analiz yap → Tahminleri kaydet
2. Yarın: Dünkü sonuçları çek → Tahminlerle karşılaştır → Başarı oranını gör
3. Otomatik: Her gece 00:30'da sistem kendi kendine kontrol eder
```

## Veri Çekilen Şehirler

- **İstanbul** - Veliefendi Hipodromu
- **Ankara** - Ankara Hipodromu  
- **İzmir** - İzmir Hipodromu
- **Adana** - Adana Hipodromu
- **Bursa** - Bursa Hipodromu
- **Kocaeli** - Kocaeli Hipodromu
- **Şanlıurfa** - Şanlıurfa Hipodromu
- **Diyarbakır** - Diyarbakır Hipodromu
- **Elazığ** - Elazığ Hipodromu

## CSV Çıktısı

Her CSV dosyası şu kolonları içerir:
- At İsmi, Koşu No, Profil Linki
- Jokey, Son/Bugünkü Kilo
- Son/Bugünkü Mesafe, Pist
- Son Derece, Son Hipodrom

## Dağıtım

### Yerel Test
```bash
python app.py
```

### Production (Gunicorn ile)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker ile dağıtım
Dockerfile oluşturup containerize edebilirsiniz.

### Cloud dağıtım
- **Heroku**: `Procfile` oluşturun
- **Railway**: GitHub repo'yu bağlayın
- **DigitalOcean App Platform**: GitHub integration
- **AWS/Azure**: Cloud services

## API Endpoints

- `GET /` - Ana sayfa
- `POST /api/scrape_city` - Tek şehir at verisi çek
- `POST /api/scrape_all` - Tüm şehirler at verisi çek  
- `POST /api/test` - Sistem testi yap
- `GET /download/<filename>` - CSV dosyası indir

## Proje Yapısı

```
site/
├── app.py              # Ana Flask uygulaması
├── requirements.txt    # Python bağımlılıkları
├── README.md          # Bu dosya
├── templates/         # HTML şablonları
│   └── index.html
├── static/            # CSS, JS, resim dosyaları
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── .github/
    └── copilot-instructions.md
```

## Özelleştirme

- **Tasarım**: `static/css/style.css` dosyasını düzenleyin
- **Arayüz**: `templates/index.html` dosyasını güncelleyin  
- **JavaScript**: `static/js/main.js` dosyasına özellik ekleyin
- **Backend**: `app.py` dosyasına yeni endpoint'ler ekleyin

## Güvenlik

Production ortamı için:
- `debug=False` yapın
- Environment variables kullanın
- HTTPS kullanın
- Input validation ekleyin
- Rate limiting uygulayın
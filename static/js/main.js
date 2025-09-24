document.addEventListener('DOMContentLoaded', function() {
    console.log('🏇 At Yarışı Analizi başlatılıyor...');

    // DOM elementleri
    const citySelect = document.getElementById('citySelect');
    const checkDataBtn = document.getElementById('checkDataBtn');
    const scrapeAndSaveBtn = document.getElementById('scrapeAndSaveBtn');
    const quickCalculateBtn = document.getElementById('quickCalculateBtn');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const statusMessage = document.getElementById('statusMessage');
    const resultsContainer = document.getElementById('resultsContainer');
    const summaryStats = document.getElementById('summaryStats');
    const results = document.getElementById('results');

    let currentData = null;

    // Şehir seçimi değiştiğinde butonları aktif et
    citySelect.addEventListener('change', function() {
        const hasCity = this.value !== '';
        checkDataBtn.disabled = !hasCity;
        scrapeAndSaveBtn.disabled = !hasCity;
        quickCalculateBtn.disabled = !hasCity;
        scrapeBtn.disabled = !hasCity;
    });

    // Yükleme göstergesi
    function showLoading(show, message = 'İşlem yapılıyor...') {
        if (show) {
            statusMessage.innerHTML = `
                <div class="alert alert-info">
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                        <span>${message}</span>
                    </div>
                </div>
            `;
        } else {
            statusMessage.innerHTML = '';
        }
    }

    // Durum mesajı göster
    function showStatus(message, type = 'info') {
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'danger' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        statusMessage.innerHTML = `
            <div class="alert ${alertClass}" role="alert">
                ${message}
            </div>
        `;
    }

    // Özet istatistikler göster
    function showSummaryStats(data) {
        const totalHorses = data.total_horses;
        const validHorses = data.valid_horses;
        const successRate = data.success_rate;
        
        summaryStats.innerHTML = `
            <div class="col-md-3">
                <div class="stats-card">
                    <span class="stats-number">${totalHorses}</span>
                    <small>Toplam At</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <span class="stats-number">${validHorses}</span>
                    <small>Geçerli Veri</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <span class="stats-number">%${successRate}</span>
                    <small>Başarı Oranı</small>
                </div>
            </div>
        `;
        summaryStats.style.display = 'flex';
    }

    // Pist türü mapping
    function getPistType(pistCode) {
        const pistMap = {
            '1': 'Çim',
            '2': 'Kum', 
            '3': 'Sentetik',
            'Çim': 'Çim',
            'Kum': 'Kum',
            'Sentetik': 'Sentetik',
            'çim': 'Çim',
            'kum': 'Kum',
            'sentetik': 'Sentetik'
        };
        return pistMap[pistCode] || pistCode || '-';
    }

    // Koşu sonuçlarını göster
    function showRaceResults(data) {
        console.log('📊 Sonuçlar gösteriliyor...');
        
        let tabsHtml = '<div class="race-tabs-container"><div class="race-tabs">';
        let contentHtml = '<div class="race-content-container">';

        // Her koşu için sekme ve içerik oluştur
        data.races.forEach((race, index) => {
            const raceNumber = index + 1;
            const validHorses = race.horses.filter(h => h.skor !== null && h.skor !== 'Veri yok');
            
            // Koşu saati hesapla (16:45'ten başlayarak her koşu 30dk sonra)
            const startHour = 16;
            const startMinute = 45;
            const totalMinutes = startMinute + (index * 30);
            const raceHour = startHour + Math.floor(totalMinutes / 60);
            const raceMinute = totalMinutes % 60;
            const raceTime = `${raceHour}:${raceMinute.toString().padStart(2, '0')}`;
            
            // Sekme
            tabsHtml += `
                <button class="race-tab ${index === 0 ? 'active' : ''}" onclick="showRaceTab(${index})" id="tab-${index}">
                    ${raceNumber}. Koşu ${raceTime}
                </button>
            `;

            // İçerik
            contentHtml += `
                <div class="race-content-tab ${index === 0 ? 'active' : ''}" id="race-tab-content-${index}">
                    <!-- Ana Tablo -->
                    <div class="table-responsive">
                        <table class="horse-table">
                            <thead>
                                <tr>
                                    <th width="30">N</th>
                                    <th width="150">At İsmi</th>
                                    <th width="100">Son Hipodrom</th>
                                    <th width="60">100m Çıktı</th>
                                    <th width="80">Son Mesafe</th>
                                    <th width="60">Pist Türü</th>
                                    <th width="60">Son Kilo</th>
                                    <th width="60">Mevcut Kilo</th>
                                    <th width="60">Son Derece</th>
                                    <th width="80">Analiz Skoru</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            // Atları skora göre sırala (en düşük skordan en yükseğe - en iyi 1.)
            const sortedHorses = [...race.horses].sort((a, b) => {
                const scoreA = typeof a.skor === 'number' ? a.skor : 9999;
                const scoreB = typeof b.skor === 'number' ? b.skor : 9999;
                return scoreA - scoreB; // En düşük skor en iyi (1.)
            });

            sortedHorses.forEach((horse, horseIndex) => {
                const rank = horseIndex + 1;
                const scoreText = typeof horse.skor === 'number' ? horse.skor.toFixed(2) : '-';

                contentHtml += `
                    <tr>
                        <td><strong>${rank}</strong></td>
                        <td class="horse-name"><strong>${horse.at_adi || 'Bilinmiyor'}</strong></td>
                        <td style="font-size: 10px;">${horse.son_hipodrom || '-'}</td>
                        <td><strong style="color: ${typeof horse.skor === 'number' ? '#28a745' : '#dc3545'}">${scoreText}</strong></td>
                        <td>${horse.son_mesafe || '-'}m</td>
                        <td>${getPistType(horse.son_pist)}</td>
                        <td>${horse.son_kilo || '-'}kg</td>
                        <td>${horse.agirlik || '-'}kg</td>
                        <td>${horse.son_derece || '-'}</td>
                        <td><strong style="color: ${typeof horse.skor === 'number' ? '#007bff' : '#6c757d'}">${scoreText}</strong></td>
                    </tr>
                `;
            });

            contentHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });

        // "Tüm Koşular" sekmesi ekle
        tabsHtml += `
            <button class="race-tab" onclick="showAllRaces()" id="tab-all">
                Tüm Koşular
            </button>
        `;
        
        // Tüm koşular içeriği
        contentHtml += `
            <div class="race-content-tab" id="race-tab-content-all">
                <div class="row all-races-grid">
        `;
        
        data.races.forEach((race, index) => {
            const raceNumber = index + 1;
            const validHorses = race.horses.filter(h => h.skor !== null && h.skor !== 'Veri yok');
            const topHorse = race.horses.sort((a, b) => {
                const scoreA = typeof a.skor === 'number' ? a.skor : 9999;
                const scoreB = typeof b.skor === 'number' ? b.skor : 9999;
                return scoreA - scoreB; // En düşük skor en iyi
            })[0];
            
            const startHour = 16;
            const startMinute = 45;
            const totalMinutes = startMinute + (index * 30);
            const raceHour = startHour + Math.floor(totalMinutes / 60);
            const raceMinute = totalMinutes % 60;
            const raceTime = `${raceHour}:${raceMinute.toString().padStart(2, '0')}`;
            
            contentHtml += `
                <div class="col-md-4 col-sm-6 mb-3">
                    <div class="race-overview-card">
                        <h6>${raceNumber}. Koşu ${raceTime}</h6>
                        <p class="card-text">
                            <strong>En İyi:</strong> ${topHorse?.at_adi || 'Veri yok'}<br>
                            <strong>Skor:</strong> ${typeof topHorse?.skor === 'number' ? topHorse.skor.toFixed(2) : 'Veri yok'}<br>
                            <strong>Atlar:</strong> ${race.horses.length} / Geçerli: ${validHorses.length}
                        </p>
                        <button class="btn btn-primary btn-sm" onclick="showRaceTab(${index})">
                            Detay Gör
                        </button>
                    </div>
                </div>
            `;
        });
        
        contentHtml += `
                </div>
            </div>
        `;

        tabsHtml += '</div></div>';
        contentHtml += '</div>';

        results.innerHTML = tabsHtml + contentHtml;
    }

    // Koşu sekmesi göster
    window.showRaceTab = function(raceIndex) {
        // Tüm sekmeleri pasif yap
        document.querySelectorAll('.race-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.race-content-tab').forEach(content => {
            content.classList.remove('active');
        });
        
        // Seçili sekmeyi aktif yap
        document.getElementById(`tab-${raceIndex}`).classList.add('active');
        document.getElementById(`race-tab-content-${raceIndex}`).classList.add('active');
    };

    // Tüm koşuları göster
    window.showAllRaces = function() {
        // Tüm sekmeleri pasif yap
        document.querySelectorAll('.race-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.race-content-tab').forEach(content => {
            content.classList.remove('active');
        });
        
        // "Tüm Koşular" sekmesini aktif yap
        document.getElementById('tab-all').classList.add('active');
        document.getElementById('race-tab-content-all').classList.add('active');
    };

    // Veri kontrol butonu
    checkDataBtn.addEventListener('click', async function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Lütfen bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Kaydedilmiş veriler kontrol ediliyor...');

        try {
            const response = await fetch('/api/check_saved_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ city: city })
            });

            const result = await response.json();

            if (response.ok && result.has_data) {
                showStatus(`
                    ✅ ${result.data.city} için bugünkü veri mevcut!<br>
                    📊 Toplam ${result.data.total_horses} at, ${result.data.successful_horses} başarılı veri<br>
                    📈 Başarı oranı: %${result.data.success_rate}
                `, 'success');
                
                quickCalculateBtn.disabled = false;
                downloadBtn.disabled = false;
            } else {
                showStatus(`❌ ${result.message}`, 'warning');
                quickCalculateBtn.disabled = true;
            }
        } catch (error) {
            showStatus('❌ Veri kontrolü sırasında hata oluştu: ' + error.message, 'danger');
        } finally {
            showLoading(false);
        }
    });

    // Veri çekme butonu
    scrapeAndSaveBtn.addEventListener('click', async function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Lütfen bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Veriler çekiliyor ve kaydediliyor...');

        try {
            const response = await fetch('/api/scrape_and_save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ city: city, debug: false })
            });

            const result = await response.json();

            if (response.ok) {
                showStatus(`
                    ✅ ${result.data.city} verileri başarıyla çekildi!<br>
                    📊 Toplam ${result.data.total_horses} at, ${result.data.successful_horses} başarılı veri<br>
                    📈 Başarı oranı: %${result.data.success_rate}<br>
                    💾 Ham veri: <a href="${result.data.raw_download_url}" class="alert-link">${result.data.raw_filename}</a>
                `, 'success');
                
                quickCalculateBtn.disabled = false;
            } else {
                showStatus('❌ Veri çekme hatası: ' + (result.message || 'Bilinmeyen hata'), 'danger');
            }
        } catch (error) {
            showStatus('❌ Veri çekme sırasında hata oluştu: ' + error.message, 'danger');
        } finally {
            showLoading(false);
        }
    });

    // Hızlı hesaplama butonu
    quickCalculateBtn.addEventListener('click', async function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Lütfen bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Kaydedilmiş verilerle analiz yapılıyor...');

        try {
            const response = await fetch('/api/calculate_from_saved', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ city: city })
            });

            const result = await response.json();

            if (response.ok) {
                currentData = result;
                showSummaryStats(result);
                showRaceResults(result);
                resultsContainer.style.display = 'block';
                downloadBtn.disabled = false;
                showStatus('✅ Analiz tamamlandı! Koşulara tıklayarak detayları görüntüleyebilirsiniz.', 'success');
            } else {
                showStatus('❌ Analiz hatası: ' + (result.message || 'Bilinmeyen hata'), 'danger');
            }
        } catch (error) {
            showStatus('❌ Analiz sırasında hata oluştu: ' + error.message, 'danger');
        } finally {
            showLoading(false);
        }
    });

    // Çek ve analiz butonu
    scrapeBtn.addEventListener('click', async function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Lütfen bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Veriler çekiliyor ve analiz yapılıyor...');

        try {
            const response = await fetch('/api/scrape_and_calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ city: city, debug: false })
            });

            const result = await response.json();

            if (response.ok) {
                currentData = result;
                showSummaryStats(result);
                showRaceResults(result);
                resultsContainer.style.display = 'block';
                showStatus('✅ Analiz tamamlandı! Koşulara tıklayarak detayları görüntüleyebilirsiniz.', 'success');
            } else {
                showStatus('❌ Analiz hatası: ' + (result.error || 'Bilinmeyen hata'), 'danger');
            }
        } catch (error) {
            showStatus('❌ Analiz sırasında hata oluştu: ' + error.message, 'danger');
        }
    });

    // CSV indirme butonu
    downloadBtn.addEventListener('click', function() {
        const city = citySelect.value;
        if (!city || !currentData) {
            showStatus('❌ Önce bir analiz yapın!', 'warning');
            return;
        }

        const url = `/download_csv/${city}`;
        const a = document.createElement('a');
        a.href = url;
        a.download = `${city}_analiz_sonuclari.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        showStatus('📥 CSV dosyası indiriliyor...', 'info');
    });
});
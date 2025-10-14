document.addEventListener('DOMContentLoaded', function() {
    console.log('🏇 At Yarışı Analizi başlatılıyor...');

    // DOM elementleri
    const citySelect = document.getElementById('citySelect');
    const checkDataBtn = document.getElementById('checkDataBtn');
    const scrapeAndSaveBtn = document.getElementById('scrapeAndSaveBtn');
    const quickCalculateBtn = document.getElementById('quickCalculateBtn');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const getResultsBtn = document.getElementById('getResultsBtn');
    const compareBtn = document.getElementById('compareBtn');
    const detailedCompareBtn = document.getElementById('detailedCompareBtn');
    const compareAllBtn = document.getElementById('compareAllBtn');
    const statusMessage = document.getElementById('statusMessage');
    const resultsContainer = document.getElementById('resultsContainer');
    const summaryStats = document.getElementById('summaryStats');
    const results = document.getElementById('results');
    const comparisonContainer = document.getElementById('comparisonContainer');
    const comparisonResults = document.getElementById('comparisonResults');
    const yesterdayContainer = document.getElementById('yesterdayContainer');
    const yesterdayResults = document.getElementById('yesterdayResults');

    let currentData = null;

    // Mobil cihaz kontrolü
    function isMobileDevice() {
        return window.innerWidth <= 768 || 
               /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    // Mobil optimizasyonları
    if (isMobileDevice()) {
        // Touch eventi optimizasyonları
        document.body.style.webkitTouchCallout = 'none';
        document.body.style.webkitUserSelect = 'none';
        
        // Mobil scroll optimizasyonu
        document.addEventListener('touchstart', function() {}, {passive: true});
        document.addEventListener('touchmove', function() {}, {passive: true});
    }

    // Ekran yönlendirme değişikliği
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            // Tablo genişliğini yeniden hesapla
            const tables = document.querySelectorAll('.horse-table');
            tables.forEach(table => {
                table.style.width = 'auto';
                setTimeout(() => table.style.width = '100%', 100);
            });
        }, 500);
    });

    // Şehir seçimi değiştiğinde butonları aktif et
    citySelect.addEventListener('change', function() {
        const hasCity = this.value !== '';
        checkDataBtn.disabled = !hasCity;
        scrapeAndSaveBtn.disabled = !hasCity;
        quickCalculateBtn.disabled = !hasCity;
        scrapeBtn.disabled = !hasCity;
        getResultsBtn.disabled = !hasCity;
        compareBtn.disabled = !hasCity;
        detailedCompareBtn.disabled = !hasCity;
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
        console.log('📊 Sonuçlar gösteriliyor...', data);
        console.log('📊 Races array:', data.races);
        console.log('📊 Results element:', results);
        
        if (!data.races || data.races.length === 0) {
            console.log('❌ Koşu verisi bulunamadı!');
            return;
        }
        
        console.log('🔄 Gerçek tablo oluşturuluyor...');
        console.log('📊 Toplam koşu sayısı:', data.races.length);
        
        let tabsHtml = '<div class="race-tabs-container"><div class="race-tabs">';
        let contentHtml = '<div class="race-content-container">';

        // Kazanan çıktı sekmesini kaldırdık

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
                                    <th width="25">N</th>
                                    <th width="120">At İsmi</th>
                                    <th width="80">Hipodrom</th>
                                    <th width="50">Çıktı</th>
                                    <th width="80">1.Derece</th>
                                    <th width="60">Mesafe</th>
                                    <th width="50">Pist</th>
                                    <th width="50">S.Kilo</th>
                                    <th width="50">M.Kilo</th>
                                    <th width="60">Derece</th>
                                    <th width="60">Skor</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            // Atları çıktı değerine göre sırala (en düşük çıktıdan en yükseğe - en iyi 1.)
            const sortedHorses = [...race.horses].sort((a, b) => {
                // Çıktı değerini parse et
                const parseOutput = (value) => {
                    if (!value || value === 'geçersiz' || value === 'Veri yok') return 9999;
                    // String formatı: "1.23.45" -> sayıya çevir
                    const str = value.toString();
                    if (str.includes('.')) {
                        const parts = str.split('.');
                        if (parts.length === 3) {
                            // "1.23.45" formatı -> 83.45 saniye
                            return parseFloat(parts[0]) * 60 + parseFloat(parts[1]) + parseFloat('0.' + parts[2]);
                        }
                    }
                    return parseFloat(str) || 9999;
                };
                
                const outputA = parseOutput(a.cikti_degeri);
                const outputB = parseOutput(b.cikti_degeri);
                return outputA - outputB; // En düşük çıktı en iyi (1.)
            });

            sortedHorses.forEach((horse, horseIndex) => {
                const rank = horseIndex + 1;
                const scoreText = typeof horse.skor === 'number' ? horse.skor.toFixed(2) : '-';
                
                // Çıktı değerini ayrı hesapla (backend'den gelen ham çıktı değeri)
                const ciktiText = horse.cikti_degeri ? (typeof horse.cikti_degeri === 'number' ? horse.cikti_degeri.toFixed(2) : horse.cikti_degeri) : (scoreText === '-' ? '-' : scoreText);

                contentHtml += `
                    <tr>
                        <td><strong>${rank}</strong></td>
                        <td class="horse-name"><strong>${horse.at_adi || 'Bilinmiyor'}</strong></td>
                        <td style="font-size: 10px;">${horse.son_hipodrom || '-'}</td>
                        <td><strong style="color: ${typeof horse.skor === 'number' ? '#28a745' : '#dc3545'}">${ciktiText}</strong></td>
                        <td style="font-size: 10px; color: #28a745;"><strong>${horse.kazanan_ismi || '-'}</strong></td>
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
        
        // Kazanan çıktı sekmesi kaldırıldı

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
        
        // Mobil optimizasyonları uygula
        setTimeout(() => {
            addTouchSupport();
            optimizeTableScroll();
        }, 100);
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

    // Mobil için dokunmatik sekme geçişi
    function addTouchSupport() {
        const raceTabsContainer = document.querySelector('.race-tabs');
        if (raceTabsContainer && isMobileDevice()) {
            let startX = 0;
            let currentX = 0;
            let isDragging = false;

            raceTabsContainer.addEventListener('touchstart', function(e) {
                startX = e.touches[0].clientX;
                isDragging = true;
            }, {passive: true});

            raceTabsContainer.addEventListener('touchmove', function(e) {
                if (!isDragging) return;
                currentX = e.touches[0].clientX;
                const diffX = startX - currentX;
                
                // Yatay scroll
                raceTabsContainer.scrollLeft += diffX * 0.5;
                startX = currentX;
            }, {passive: true});

            raceTabsContainer.addEventListener('touchend', function() {
                isDragging = false;
            }, {passive: true});
        }
    }

    // Mobil için tablo scroll optimizasyonu
    function optimizeTableScroll() {
        const tables = document.querySelectorAll('.table-responsive');
        tables.forEach(table => {
            if (isMobileDevice()) {
                table.style.overflowX = 'auto';
                table.style.webkitOverflowScrolling = 'touch';
                
                // Scroll ipucu göster
                const scrollHint = document.createElement('div');
                scrollHint.style.cssText = `
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 10px;
                    pointer-events: none;
                    z-index: 10;
                `;
                scrollHint.textContent = '← → Kaydır';
                table.style.position = 'relative';
                table.appendChild(scrollHint);
                
                // 3 saniye sonra gizle
                setTimeout(() => {
                    if (scrollHint.parentNode) {
                        scrollHint.style.opacity = '0';
                        scrollHint.style.transition = 'opacity 0.5s';
                        setTimeout(() => scrollHint.remove(), 500);
                    }
                }, 3000);
            }
        });
    }

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
        console.log('🔥 ANALİZ YAP BUTONUNA BASILDI!');
        const city = citySelect.value;
        console.log('🔥 Seçilen şehir:', city);
        if (!city) {
            showStatus('❌ Lütfen bir şehir seçin!', 'warning');
            return;
        }

        console.log('🔥 showLoading çağrılıyor...');
        showLoading(true, 'Kaydedilmiş verilerle analiz yapılıyor...');
        console.log('🔥 fetch başlatılıyor...');

        try {
            console.log('🔥 fetch isteği gönderiliyor...');
            const response = await fetch('/api/calculate_from_saved', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ city: city })
            });

            console.log('🔥 Response alındı:', response.status);
            
            let result;
            try {
                console.log('🔥 JSON parse başlatılıyor...');
                result = await response.json();
                console.log('🔥 JSON parse başarılı!');
            } catch (error) {
                console.error('❌ JSON parse hatası:', error);
                console.log('📝 Response headers:', response.headers);
                const text = await response.text();
                console.log('📝 Response text (ilk 1000 karakter):', text.substring(0, 1000));
                console.log('📝 NaN arıyoruz...');
                const nanMatches = text.match(/:\s*NaN/g);
                if (nanMatches) {
                    console.log('🔍 Bulunan NaN değerleri:', nanMatches);
                }
                return;
            }
            
            console.log('📊 Backend Response:', result);
            console.log('📊 Response keys:', Object.keys(result));
            console.log('📊 Races array:', result.races);
            console.log('📊 Races length:', result.races ? result.races.length : 'races field yok');
            
            // Veri yapısını detaylı analiz edelim
            console.log('🔍 Result type:', typeof result);
            console.log('🔍 Result struktur:', JSON.stringify(result, null, 2));

            if (response.ok) {
                console.log('✅ Response OK, races count:', result.races?.length);
                console.log('✅ resultsContainer element:', resultsContainer);
                
                currentData = result;
                showSummaryStats(result);
                showRaceResults(result);
                
                if (resultsContainer) {
                    resultsContainer.style.display = 'block';
                    resultsContainer.style.visibility = 'visible';
                    console.log('✅ resultsContainer görünür yapıldı');
                    console.log('✅ resultsContainer display:', resultsContainer.style.display);
                    console.log('✅ resultsContainer computed style:', getComputedStyle(resultsContainer).display);
                } else {
                    console.log('❌ resultsContainer bulunamadı!');
                }
                
                downloadBtn.disabled = false;
                showStatus('✅ Analiz tamamlandı! Koşulara tıklayarak detayları görüntüleyebilirsiniz.', 'success');
            } else {
                console.log('❌ Response Error:', result);
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

    // Kazanan çıktı fonksiyonları
    window.createWinnerTable = function(winnerData) {
        if (!winnerData || winnerData.length === 0) {
            return '<div class="alert alert-warning">Henüz kazanan çıktı verisi bulunmuyor.</div>';
        }

        let tableHtml = `
            <div class="table-responsive">
                <table class="table table-striped table-hover winner-table">
                    <thead class="table-dark">
                        <tr>
                            <th>At İsmi</th>
                            <th>Bugünkü Koşu</th>
                            <th>Önceki Koşu Birincisi</th>
                            <th>Derece</th>
                            <th>Ganyan</th>
                            <th>Şehir</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        winnerData.forEach(winner => {
            tableHtml += `
                <tr>
                    <td><strong>${winner.at_ismi || '-'}</strong></td>
                    <td>${winner.bugun_kosu_no || '-'}. Koşu</td>
                    <td><span class="winner-name">${winner.onceki_kosu_birinci_ismi || 'Veri yok'}</span></td>
                    <td>${winner.onceki_kosu_birinci_derece || '-'}</td>
                    <td>${winner.onceki_kosu_birinci_ganyan || '-'}</td>
                    <td>${winner.bugun_sehir || '-'}</td>
                </tr>
            `;
        });

        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;

        return tableHtml;
    };

    window.showWinnerResults = function() {
        // Tüm sekmeleri pasif yap
        document.querySelectorAll('.race-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.race-content-tab').forEach(content => {
            content.classList.remove('active');
        });
        
        // Kazanan çıktı sekmesini aktif yap
        document.getElementById('tab-winners').classList.add('active');
        document.getElementById('race-tab-content-winners').classList.add('active');
    };

    // Dünkü sonuçları getir
    getResultsBtn.addEventListener('click', function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Önce bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Dünkü sonuçlar çekiliyor...');
        
        fetch('/api/get_results', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: city,
                debug: true
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            
            if (data.status === 'success') {
                showYesterdayResults(data.data);
                showStatus(`✅ ${data.data.city} dünkü sonuçları başarıyla çekildi!`, 'success');
            } else {
                showStatus(`❌ Hata: ${data.message}`, 'danger');
            }
        })
        .catch(error => {
            showLoading(false);
            showStatus('❌ Bağlantı hatası!', 'danger');
            console.error('Error:', error);
        });
    });

    // Tahminleri karşılaştır
    compareBtn.addEventListener('click', function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Önce bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Tahminler sonuçlarla karşılaştırılıyor...');
        
        fetch('/api/compare_predictions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: city,
                debug: true
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            
            if (data.status === 'success') {
                showComparisonResults(data.data);
                showStatus(`✅ ${data.data.city} karşılaştırması tamamlandı! Başarı oranı: %${data.data.success_rate.toFixed(1)}`, 'success');
            } else {
                showStatus(`❌ Hata: ${data.message}`, 'danger');
            }
        })
        .catch(error => {
            showLoading(false);
            showStatus('❌ Bağlantı hatası!', 'danger');
            console.error('Error:', error);
        });
    });

    // Detaylı karşılaştırma
    detailedCompareBtn.addEventListener('click', function() {
        const city = citySelect.value;
        if (!city) {
            showStatus('❌ Önce bir şehir seçin!', 'warning');
            return;
        }

        showLoading(true, 'Tüm atlar detaylı analiz ediliyor...');
        
        fetch('/api/detailed_comparison', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: city,
                debug: true
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            
            if (data.status === 'success') {
                showDetailedComparisonResults(data.data);
                showStatus(`✅ ${data.data.city} detaylı karşılaştırması tamamlandı! Başarı oranı: %${data.data.success_rate.toFixed(1)}`, 'success');
            } else {
                showStatus(`❌ Hata: ${data.message}`, 'danger');
            }
        })
        .catch(error => {
            showLoading(false);
            showStatus('❌ Bağlantı hatası!', 'danger');
            console.error('Error:', error);
        });
    });

    // Tüm şehirler için karşılaştır
    compareAllBtn.addEventListener('click', function() {
        showLoading(true, 'Tüm şehirler için karşılaştırma yapılıyor...');
        
        fetch('/api/compare_all_cities', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                debug: true
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            
            if (data.status === 'success') {
                showAllCitiesComparison(data.data);
                showStatus(`✅ Tüm şehirler karşılaştırıldı! Genel başarı oranı: %${data.data.overall_success_rate.toFixed(1)}`, 'success');
            } else {
                showStatus(`❌ Hata: ${data.message}`, 'danger');
            }
        })
        .catch(error => {
            showLoading(false);
            showStatus('❌ Bağlantı hatası!', 'danger');
            console.error('Error:', error);
        });
    });

    // Dünkü sonuçları göster
    function showYesterdayResults(data) {
        yesterdayContainer.style.display = 'block';
        resultsContainer.style.display = 'none';
        comparisonContainer.style.display = 'none';

        let html = `
            <div class="row mb-3">
                <div class="col-md-4">
                    <div class="stats-card bg-info text-white">
                        <span class="stats-number">${data.total_races}</span>
                        <small>Toplam Koşu</small>
                    </div>
                </div>
                <div class="col-md-8">
                    <h5>${data.city} - Dünkü Koşu Sonuçları</h5>
                </div>
            </div>
        `;

        Object.entries(data.results).forEach(([raceNum, results]) => {
            html += `
                <div class="race-card mb-3">
                    <div class="race-header">
                        <h5><i class="fas fa-flag-checkered"></i> ${raceNum}. Koşu</h5>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-sm horse-table">
                            <thead class="table-dark">
                                <tr>
                                    <th>Sıra</th>
                                    <th>At İsmi</th>
                                    <th>Derece</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            results.slice(0, 5).forEach(horse => {
                const rankClass = horse.sira === 1 ? 'text-success fw-bold' : 
                                horse.sira === 2 ? 'text-warning fw-bold' : 
                                horse.sira === 3 ? 'text-danger fw-bold' : '';
                
                html += `
                    <tr>
                        <td><span class="${rankClass}">${horse.sira}</span></td>
                        <td><strong>${horse.at_ismi}</strong></td>
                        <td>${horse.derece}</td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });

        yesterdayResults.innerHTML = html;
    }

    // Karşılaştırma sonuçlarını göster
    function showComparisonResults(data) {
        comparisonContainer.style.display = 'block';
        resultsContainer.style.display = 'none';
        yesterdayContainer.style.display = 'none';

        let html = `
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stats-card bg-success text-white">
                        <span class="stats-number">${data.success_rate.toFixed(1)}%</span>
                        <small>Başarı Oranı</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card bg-info text-white">
                        <span class="stats-number">${data.total_races}</span>
                        <small>Toplam Koşu</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card bg-primary text-white">
                        <span class="stats-number">${data.successful_predictions}</span>
                        <small>Doğru Tahmin</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card bg-warning text-white">
                        <span class="stats-number">${data.total_races - data.successful_predictions}</span>
                        <small>Yanlış Tahmin</small>
                    </div>
                </div>
            </div>
            
            <h5>${data.city} - Detaylı Karşılaştırma</h5>
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead class="table-dark">
                        <tr>
                            <th>Koşu</th>
                            <th>Tahminimiz</th>
                            <th>Tahmini Süre</th>
                            <th>Gerçek Kazanan</th>
                            <th>Gerçek Süre</th>
                            <th>Durum</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.detailed_results.forEach(result => {
            const statusIcon = result.is_successful ? 
                '<i class="fas fa-check text-success"></i>' : 
                '<i class="fas fa-times text-danger"></i>';
            const statusText = result.is_successful ? 'DOĞRU' : 'YANLIŞ';
            const rowClass = result.is_successful ? 'table-success' : 'table-danger';

            // Tahmin detaylarını al
            const predDetails = result.prediction_details || {};
            const cikti = predDetails.cikti || '';
            const mesafe = predDetails.mesafe || '';
            const calcTime = predDetails.calculated_time || 0;
            
            // Tahmini süreyi formatla
            let predictedTimeDisplay = result.predicted_time || '';
            if (calcTime > 0 && cikti && mesafe) {
                predictedTimeDisplay += ` (${cikti} × ${mesafe}m/100)`;
            }

            html += `
                <tr class="${rowClass}">
                    <td><strong>${result.race_number}</strong></td>
                    <td><strong>${result.predicted_winner}</strong></td>
                    <td>${predictedTimeDisplay}</td>
                    <td><strong>${result.actual_winner}</strong></td>
                    <td>${result.actual_time}</td>
                    <td>${statusIcon} ${statusText}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        comparisonResults.innerHTML = html;
    }

    // Tüm şehirler karşılaştırmasını göster
    function showAllCitiesComparison(data) {
        comparisonContainer.style.display = 'block';
        resultsContainer.style.display = 'none';
        yesterdayContainer.style.display = 'none';

        let html = `
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stats-card bg-success text-white">
                        <span class="stats-number">${data.overall_success_rate.toFixed(1)}%</span>
                        <small>Genel Başarı Oranı</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card bg-info text-white">
                        <span class="stats-number">${data.total_races}</span>
                        <small>Toplam Koşu</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-card bg-primary text-white">
                        <span class="stats-number">${data.total_successful_predictions}</span>
                        <small>Doğru Tahmin</small>
                    </div>
                </div>
            </div>
            
            <h5>Tüm Şehirler - Karşılaştırma Özeti</h5>
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead class="table-dark">
                        <tr>
                            <th>Şehir</th>
                            <th>Başarı Oranı</th>
                            <th>Doğru/Toplam</th>
                            <th>Durum</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        Object.entries(data.city_results).forEach(([cityKey, cityData]) => {
            if (cityData.error) {
                html += `
                    <tr class="table-warning">
                        <td><strong>${cityData.city_name}</strong></td>
                        <td colspan="3"><i class="fas fa-exclamation-triangle"></i> ${cityData.error}</td>
                    </tr>
                `;
            } else {
                const successRate = cityData.success_rate || 0;
                const barClass = successRate >= 70 ? 'bg-success' : 
                               successRate >= 50 ? 'bg-warning' : 'bg-danger';
                
                html += `
                    <tr>
                        <td><strong>${cityData.city_name}</strong></td>
                        <td>
                            <div class="progress" style="height: 20px;">
                                <div class="progress-bar ${barClass}" style="width: ${successRate}%">
                                    ${successRate.toFixed(1)}%
                                </div>
                            </div>
                        </td>
                        <td>${cityData.successful_predictions}/${cityData.total_races}</td>
                        <td>
                            ${successRate >= 70 ? '<i class="fas fa-star text-success"></i> Mükemmel' :
                              successRate >= 50 ? '<i class="fas fa-thumbs-up text-warning"></i> İyi' :
                              '<i class="fas fa-thumbs-down text-danger"></i> Geliştirilmeli'}
                        </td>
                    </tr>
                `;
            }
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        comparisonResults.innerHTML = html;
    }

    // Detaylı karşılaştırma sonuçlarını göster
    function showDetailedComparisonResults(data) {
        comparisonContainer.style.display = 'block';
        resultsContainer.style.display = 'none';
        yesterdayContainer.style.display = 'none';

        let html = `
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stats-card bg-success text-white">
                        <span class="stats-number">${data.success_rate.toFixed(1)}%</span>
                        <small>Başarı Oranı</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card bg-info text-white">
                        <span class="stats-number">${data.total_races}</span>
                        <small>Toplam Koşu</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card bg-primary text-white">
                        <span class="stats-number">${data.successful_predictions}</span>
                        <small>Doğru Tahmin</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card bg-warning text-white">
                        <span class="stats-number">${data.total_races - data.successful_predictions}</span>
                        <small>Yanlış Tahmin</small>
                    </div>
                </div>
            </div>
            
            <h5>${data.city} - Tüm Atlar Detaylı Analiz</h5>
        `;

        // Her koşu için detaylı tablo
        data.detailed_races.forEach(race => {
            const raceStatus = race.is_successful ? 'bg-success' : 'bg-danger';
            const statusIcon = race.is_successful ? 
                '<i class="fas fa-check text-success"></i>' : 
                '<i class="fas fa-times text-danger"></i>';

            html += `
                <div class="card mb-4">
                    <div class="card-header ${raceStatus} text-white">
                        <h6 class="mb-0">
                            ${statusIcon} Koşu ${race.race_number}
                        </h6>
                        <small>
                            İlk 3 Tahmin: <strong>${race.top_3_predictions ? race.top_3_predictions.join(', ') : 'Yok'}</strong><br>
                            Kazanan: <strong>${race.actual_winner}</strong>
                            ${race.successful_horse ? ` | ✅ Başarılı: <strong>${race.successful_horse}</strong>` : ''}
                        </small>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-sm mb-0">
                                <thead class="table-dark">
                                    <tr>
                                        <th>At İsmi</th>
                                        <th>Tahmin Sırası</th>
                                        <th>Tahmini Süre</th>
                                        <th>Skor</th>
                                        <th>Koşu Mesafe</th>
                                        <th>Hesap Mesafe</th>
                                        <th>Pist Türü</th>
                                        <th>Gerçek Sıra</th>
                                        <th>Gerçek Süre</th>
                                        <th>Durum</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;

            race.horses.forEach(horse => {
                let rowClass = '';
                let statusBadge = '';
                
                if (horse.is_winner_prediction) {
                    rowClass = 'table-warning'; // Tahmin edilen kazanan
                    statusBadge = '<span class="badge bg-warning">Tahmin</span>';
                }
                
                if (horse.is_actual_winner) {
                    rowClass = 'table-success'; // Gerçek kazanan
                    statusBadge += ' <span class="badge bg-success">Kazanan</span>';
                }

                // Pist türü mapping
                const trackTypeMap = {
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
                const trackType = trackTypeMap[horse.track_type] || horse.track_type || '-';

                // Tahmin sırası badge'i
                let predictionRank = '';
                if (horse.prediction_rank) {
                    // Farklı sıralar için farklı renkler
                    let rankColor = 'bg-secondary';
                    if (horse.prediction_rank === 1) {
                        rankColor = 'bg-primary';      // Mavi - 1. tahmin
                    } else if (horse.prediction_rank === 2) {
                        rankColor = 'bg-info';         // Açık mavi - 2. tahmin
                    } else if (horse.prediction_rank === 3) {
                        rankColor = 'bg-warning';      // Sarı - 3. tahmin
                    } else if (horse.prediction_rank <= 5) {
                        rankColor = 'bg-success';      // Yeşil - 4-5. tahmin
                    } else if (horse.prediction_rank <= 10) {
                        rankColor = 'bg-secondary';    // Gri - 6-10. tahmin
                    } else {
                        rankColor = 'bg-dark';         // Siyah - 10+ tahmin
                    }
                    predictionRank = `<span class="badge ${rankColor}">${horse.prediction_rank}</span>`;
                }

                html += `
                    <tr class="${rowClass}">
                        <td><strong>${horse.name}</strong></td>
                        <td>${predictionRank || '-'}</td>
                        <td>${horse.predicted_time || '-'}</td>
                        <td>${horse.calculated_score > 0 ? horse.calculated_score.toFixed(2) : '-'}</td>
                        <td>${horse.distance || '-'}m</td>
                        <td>${horse.calculation_distance || '-'}m</td>
                        <td><span class="badge bg-secondary">${trackType}</span></td>
                        <td>${horse.actual_position || '-'}</td>
                        <td>${horse.actual_time || '-'}</td>
                        <td>${statusBadge}</td>
                    </tr>
                `;
            });

            html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        });

        comparisonResults.innerHTML = html;
    }
});
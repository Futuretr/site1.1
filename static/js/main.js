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

            // Atları skora göre sırala (en düşük skordan en yükseğe - en iyi 1.)
            const sortedHorses = [...race.horses].sort((a, b) => {
                const scoreA = typeof a.skor === 'number' ? a.skor : 9999;
                const scoreB = typeof b.skor === 'number' ? b.skor : 9999;
                return scoreA - scoreB; // En düşük skor en iyi (1.)
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
});
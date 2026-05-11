




    let mevcutProjeId = null, mevcutProjeKod = null, mevcutProjeAd = '', mevcutProjeTestTuru = 'standart', mevcutProjeCevapSayisi = 0;
    let seciliTakipOturumId = null, seciliTakipIsim = null;
    let chartExplicit, chartImplicit, chartGap, chartRadar, chartScatter;
    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    function escapeHTML(str) {
        if (!str) return "";
        return String(str).replace(/[&<>"']/g, function(m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[m];
        });
    }

    function tabDegistir(tab) {
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        const tabEl = document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1));
        if(tabEl) tabEl.classList.add('active');
        const tabBaslik = tab === 'projeler' ? 'Projelerim' : tab.charAt(0).toUpperCase() + tab.slice(1);
        const testEtiketi = mevcutProjeTestTuru === 'mcrt' || mevcutProjeTestTuru === 'mrt' ? 'MCRT' : 'IRT';
        document.getElementById('currentTabTitle').textContent = tab === 'projeler' || !mevcutProjeAd ? tabBaslik : `${tabBaslik} - ${mevcutProjeAd} (${testEtiketi})`;
        if (tab === 'projeler') { projeleriYukle(); document.getElementById('navGroupProje').style.display = 'none'; } 
        else if(mevcutProjeId) { 
            document.getElementById('navGroupProje').style.display = 'block'; 
            if(tab === 'analiz') analizYukle(); 
            if(tab === 'linkler') linkleriYukle();
            if(tab === 'katilimcilar') katilimciDetaylariniYukle();
        }
        // Scroll to top on tab change
        document.querySelector('.main-content').scrollTop = 0;
    }

    async function projeleriYukle() {
        const showArchived = document.getElementById('checkShowArchived').checked ? 1 : 0;
        const res = await fetch(`/api/projeler?include_archived=${showArchived}`); 
        const data = await res.json();
        
        document.getElementById('projeGrid').innerHTML = data.projeler.map(p => {
            const stat = p.istatistik || {};
            const hedef = stat.hedef_orneklem || 0;
            const tamamlanan = stat.tamamlanan_anket || 0;
            const yarim = stat.yarim_kalan || 0;
            const outlier = stat.outliers || 0;
            const cevapsizBaslayan = stat.baslatilan_cevapsiz || 0;
            const yuzde = hedef > 0 ? Math.min(100, Math.round((tamamlanan / hedef) * 100)) : 0;
            const isMcrt = p.test_turu === 'mcrt' || p.test_turu === 'mrt';
            const testLabel = isMcrt ? 'MCRT' : 'IRT';
            const testColor = isMcrt ? 'var(--warning)' : 'var(--primary)';
            const veriKaynagi = isMcrt ? 'mcrt_cevaplar' : 'cevaplar';
            const toplamCevap = stat.toplam_cevap || 0;
            
            return `
                <div class="card" onclick="projeDetayAc(${p.id})" style="cursor:pointer; position:relative; overflow:hidden;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem;">
                        <div>
                            <h3 style="font-family:'Poppins'; font-weight:700; margin-bottom:0.35rem;">${escapeHTML(p.ad)}</h3>
                            <span class="badge" style="background:${testColor}; color:white; font-size:0.65rem;">${testLabel}</span>
                            <div style="font-size:0.72rem; color:var(--text-dim); margin-top:0.35rem;">${testLabel} | ${veriKaynagi} | ${toplamCevap} cevap</div>
                        </div>
                        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.4rem;">
                            <span class="badge badge-${escapeHTML(p.durum)}">${escapeHTML(p.durum).toUpperCase()}</span>
                            <button class="btn btn-danger btn-sm" style="padding:0.2rem 0.4rem; font-size:0.6rem;" onclick="event.stopPropagation(); projeSilHizli(${p.id}, '${escapeHTML(p.ad).replace(/'/g, "\\'")}')">SİL</button>
                        </div>
                    </div>
                    
                    <div style="margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:0.4rem; color:var(--text-med);">
                            <span>İlerleme (${tamamlanan}/${hedef || '∞'})</span>
                            <span>%${yuzde}</span>
                        </div>
                        <div style="height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden;">
                            <div style="width:${yuzde}%; height:100%; background:linear-gradient(90deg, var(--primary), var(--secondary)); border-radius:3px;"></div>
                        </div>
                    </div>
                    
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:0.5rem; text-align:center;">
                        <div style="background:rgba(16,185,129,0.05); padding:0.5rem; border-radius:8px;">
                            <div style="font-size:0.65rem; color:var(--success); font-weight:700; text-transform:uppercase;">Biten</div>
                            <div style="font-size:1.1rem; font-weight:700;">${tamamlanan}</div>
                        </div>
                        <div style="background:rgba(245,158,11,0.05); padding:0.5rem; border-radius:8px;">
                            <div style="font-size:0.65rem; color:var(--warning); font-weight:700; text-transform:uppercase;">Yarım</div>
                            <div style="font-size:1.1rem; font-weight:700;">${yarim}</div>
                        </div>
                        <div style="background:rgba(239,68,68,0.05); padding:0.5rem; border-radius:8px;">
                            <div style="font-size:0.65rem; color:var(--danger); font-weight:700; text-transform:uppercase;">Outlier</div>
                            <div style="font-size:1.1rem; font-weight:700;">${outlier}</div>
                        </div>
                    </div>
                    ${cevapsizBaslayan > 0 ? `<div style="margin-top:0.6rem; font-size:0.72rem; color:var(--text-dim);">Gercek soruya gecmeden ayrilan: ${cevapsizBaslayan}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    async function projeDetayAc(id) {
        seciliTakipOturumId = null; seciliTakipIsim = null;
        mevcutProjeId = id; const res = await fetch(`/api/proje/${id}`); const data = await res.json();
        const p = data.proje; mevcutProjeKod = p.benzersiz_kod; mevcutProjeAd = p.ad; mevcutProjeTestTuru = p.test_turu || 'standart'; mevcutProjeCevapSayisi = (p.istatistik && p.istatistik.toplam_cevap) || 0;
        document.getElementById('detayProjeAd').textContent = p.ad;
        document.getElementById('editHedefOrneklem').value = p.istatistik.hedef_orneklem || 0;
        document.getElementById('editProjeDurum').value = p.durum;
        document.getElementById('editSoruRandomize').checked = p.soru_randomize === 1;
        document.getElementById('editTestTuru').value = p.test_turu || 'standart';
            document.getElementById('editMcrtKurgu').value = p.mcrt_kurgu || 'cift_blok';
        document.getElementById('editMcrtYerlesim').value = p.mcrt_yerlesim || 'grid_standart';
        document.getElementById('editPanelComplete').value = p.panel_complete_url || '';
        document.getElementById('editPanelScreenout').value = p.panel_screenout_url || '';
        document.getElementById('editPanelQuotaFull').value = p.panel_quotafull_url || '';
        
        // MCRT Kontrolü
        const isMcrt = p.test_turu === 'mcrt' || p.test_turu === 'mrt';
        document.getElementById('cardMcrtSecenekler').style.display = 'none';
        document.getElementById('mcrtKurguAlani').style.display = isMcrt ? 'grid' : 'none';
        
        if(isMcrt) {
            mcrtArayuzGuncelle();
        } else {
            // Standart IRT ise her şeyi normale döndür
            document.querySelectorAll('.card').forEach(c => c.classList.remove('card-disabled'));
        }

        document.getElementById('markaListesi').innerHTML = p.markalar.map(m => {
            let resimIcerik = '<div style="width:32px; height:32px; background:rgba(255,255,255,0.05); border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:0.6rem; color:var(--text-dim);">Yok</div>';
            if (m.resim_dosya) {
                if (m.resim_dosya.match(/\.(mp3|wav|ogg|m4a)$/i)) {
                    resimIcerik = '<div style="width:32px; height:32px; background:rgba(99,102,241,0.1); border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:1rem;">🎵</div>';
                } else {
                    resimIcerik = `<img src="/static/uploads/${escapeHTML(m.resim_dosya)}" style="width:32px; height:32px; border-radius:6px; object-fit:cover; border:1px solid var(--border);">`;
                }
            }
            const noiseBadge = m.is_noise ? '<span style="font-size:0.6rem; background:rgba(239,68,68,0.1); color:var(--danger); padding:2px 4px; border-radius:4px; font-weight:700;">🔇 NOISE</span>' : '';
            const etiketBadge = m.analiz_etiketi ? `<span style="font-size:0.6rem; background:rgba(99,102,241,0.1); color:var(--primary); padding:2px 5px; border-radius:4px; font-weight:600;">📊 ${escapeHTML(m.analiz_etiketi)}</span>` : '';
            return `
            <li class="item-row">
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    ${resimIcerik}
                    <div>
                        <div style="font-weight:600;">${escapeHTML(m.ad)}</div>
                        <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:2px;">${noiseBadge}${etiketBadge}</div>
                    </div>
                </div>
                <button class="btn btn-danger btn-sm" onclick="markaSil(${m.id})">✕</button>
            </li>`;
        }).join('');
        
        document.getElementById('ifadeListesi').innerHTML = p.ifadeler.map(i => {
            let resimIcerik = '<div style="width:32px; height:32px; background:rgba(255,255,255,0.05); border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:0.6rem; color:var(--text-dim);">Yok</div>';
            if (i.resim_dosya) {
                if (i.resim_dosya.match(/\.(mp3|wav|ogg|m4a)$/i)) {
                    resimIcerik = '<div style="width:32px; height:32px; background:rgba(99,102,241,0.1); border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:1rem;">🎵</div>';
                } else {
                    resimIcerik = `<img src="/static/uploads/${escapeHTML(i.resim_dosya)}" style="width:32px; height:32px; border-radius:6px; object-fit:cover; border:1px solid var(--border);">`;
                }
            }
            return `
            <li class="item-row">
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    ${resimIcerik}
                    <div><div>${escapeHTML(i.metin)}</div><div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:2px;">${i.kategori ? `<span style="font-size:0.65rem; background:rgba(16,185,129,0.12); color:var(--success); padding:2px 6px; border-radius:999px; font-weight:700;">${escapeHTML(i.kategori)}</span>` : ""}</div></div>
                </div>
                <button class="btn btn-danger btn-sm" onclick="ifadeSil(${i.id})">✕</button>
            </li>`;
        }).join('');
        tabDegistir('detay');
    }

    async function projeGuncelle() {
        if(!mevcutProjeId) return;
        const hedef = document.getElementById('editHedefOrneklem').value;
        const randomize = document.getElementById('editSoruRandomize').checked;
        const testTuru = document.getElementById('editTestTuru').value;
        const mcrtYerlesim = document.getElementById('editMcrtYerlesim').value;
        const completeUrl = document.getElementById('editPanelComplete').value;
        const screenoutUrl = document.getElementById('editPanelScreenout').value;
        const quotafullUrl = document.getElementById('editPanelQuotaFull').value;

        if(mevcutProjeCevapSayisi > 0 && testTuru !== mevcutProjeTestTuru) {
            const onay = confirm(`Bu projede ${mevcutProjeCevapSayisi} cevap var. Test türünü değiştirmek eski analizleri görünmez hale getirebilir. Devam etmek istiyor musunuz?`);
            if(!onay) {
                document.getElementById('editTestTuru').value = mevcutProjeTestTuru;
                return;
            }
        }

        await fetch(`/api/proje/${mevcutProjeId}/guncelle`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ 
                hedef_orneklem: parseInt(hedef), 
                soru_randomize: randomize,
                test_turu: testTuru,
                mcrt_kurgu: document.getElementById('editMcrtKurgu').value,
                mcrt_yerlesim: mcrtYerlesim,
                panel_complete_url: completeUrl,
                panel_screenout_url: screenoutUrl,
                panel_quotafull_url: quotafullUrl
            })
        });
        mevcutProjeTestTuru = testTuru;
        mcrtArayuzGuncelle();
        if (document.getElementById('tabDetay').classList.contains('active')) tabDegistir('detay');
        toastGoster("Ayarlar kaydedildi.");
    }

    function mcrtArayuzGuncelle() {
        const kurgu = document.getElementById('editMcrtKurgu').value;
        const testTuru = document.getElementById('editTestTuru').value;
        
        // Kartları bul
        const markaCard = document.querySelector('.card:has(#markaListesi)');
        const ifadeCard = document.querySelector('.card:has(#ifadeListesi)');

        if (testTuru === 'mcrt' || testTuru === 'mrt') {
            if(markaCard) markaCard.classList.remove('card-disabled');
            if(ifadeCard) ifadeCard.classList.remove('card-disabled');
            document.getElementById('mcrtKurguAlani').style.display = 'grid';
            document.getElementById('cardMcrtSecenekler').style.display = 'none';
            mcrtGuardrailDurumunuGuncelle();
        } else {
            if(markaCard) markaCard.classList.remove('card-disabled');
            if(ifadeCard) ifadeCard.classList.remove('card-disabled');
            document.getElementById('mcrtKurguAlani').style.display = 'none';
            document.getElementById('cardMcrtSecenekler').style.display = 'none';
        }
    }

    function mcrtGuardrailOzetiHesapla() {
        const kurgu = document.getElementById('editMcrtKurgu').value;
        const markaSayisi = document.querySelectorAll('#markaListesi li').length;
        const ifadeSayisi = document.querySelectorAll('#ifadeListesi li').length;
        const mesajlar = [];
        let uygun = true;

        if (kurgu === 'marka_merkez' || kurgu === 'cift_blok') {
            if (ifadeSayisi === 0 || (ifadeSayisi % 4) !== 0) {
                uygun = false;
                mesajlar.push(`Ifade sayisi 4'un kati olmali. Mevcut: ${ifadeSayisi}`);
            }
        }

        if (kurgu === 'ifade_merkez' || kurgu === 'cift_blok') {
            if (markaSayisi === 0 || (markaSayisi % 4) !== 0) {
                uygun = false;
                mesajlar.push(`Marka sayisi 4'un kati olmali. Mevcut: ${markaSayisi}`);
            }
        }

        return { uygun, markaSayisi, ifadeSayisi, mesajlar };
    }

    function mcrtGuardrailDurumunuGuncelle() {
        const box = document.getElementById('mcrtGuardrailBox');
        if (!box) return;
        const testTuru = document.getElementById('editTestTuru').value;
        if (!(testTuru === 'mcrt' || testTuru === 'mrt')) {
            box.style.display = 'none';
            return;
        }
        const durum = mcrtGuardrailOzetiHesapla();
        box.style.display = 'block';
        if (durum.uygun) {
            box.style.borderColor = 'rgba(16,185,129,0.35)';
            box.style.background = 'rgba(16,185,129,0.08)';
            box.innerHTML = `<strong>4'lu guardrail uyumlu.</strong><br>Marka: ${durum.markaSayisi} | Ifade: ${durum.ifadeSayisi}`;
        } else {
            box.style.borderColor = 'rgba(245,158,11,0.35)';
            box.style.background = 'rgba(245,158,11,0.08)';
            box.innerHTML = `<strong>MCRT 4'lu guardrail uyarisi.</strong><br>${durum.mesajlar.join('<br>')}`;
        }
    }

    async function projeDurumGuncelle() {
        if(!mevcutProjeId) return;
        const durum = document.getElementById('editProjeDurum').value;
        const testTuru = document.getElementById('editTestTuru').value;
        if ((testTuru === 'mcrt' || testTuru === 'mrt') && durum === 'canli') {
            const guard = mcrtGuardrailOzetiHesapla();
            if (!guard.uygun) {
                toastGoster("MCRT 4'lu guardrail saglanmadi. " + guard.mesajlar.join(' | '));
                const res2 = await fetch(`/api/proje/${mevcutProjeId}`);
                const data2 = await res2.json();
                document.getElementById('editProjeDurum').value = data2.proje.durum;
                return;
            }
        }
        const res = await fetch(`/api/proje/${mevcutProjeId}/durum`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ durum })
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster(`Durum güncellendi: ${durum}`);
        } else {
            toastGoster("Hata: " + data.mesaj);
            // Geri al
            const res2 = await fetch(`/api/proje/${mevcutProjeId}`);
            const data2 = await res2.json();
            document.getElementById('editProjeDurum').value = data2.proje.durum;
        }
    }

    function projeYedekle() {
        if(!mevcutProjeId) return;
        window.location.href = `/api/proje/${mevcutProjeId}/yedekle`;
    }

    async function projeSil() {
        if(!mevcutProjeId) return;
        await projeSilHizli(mevcutProjeId, document.getElementById('detayProjeAd').textContent);
    }

    async function projeSilHizli(id, ad) {
        if(!confirm(`'${ad}' projesini ve TÜM VERİLERİNİ silmek istediğinize emin misiniz? Bu işlem geri alınamaz!`)) return;
        
        const res = await fetch(`/api/proje/${id}/sil`, { 
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster("Proje silindi.");
            if(mevcutProjeId === id) tabDegistir('projeler');
            else projeleriYukle();
        } else {
            alert("Hata: " + data.mesaj);
        }
    }

    // --- MARKA / IFADE CRUD ---
    async function markaEkle() {
        if(!mevcutProjeId) return;
        const ad = document.getElementById('yeniMarkaAd').value;
        const etiket = document.getElementById('yeniMarkaEtiket').value.trim();
        const file = document.getElementById('yeniMarkaResim').files[0];
        const isNoise = document.getElementById('yeniMarkaNoise').checked;
        if(!ad) return toastGoster("Marka adı girin.");

        const formData = new FormData();
        formData.append('ad', ad);
        formData.append('analiz_etiketi', etiket);
        formData.append('is_noise', isNoise ? '1' : '0');
        if(file) formData.append('resim', file);

        const res = await fetch(`/api/proje/${mevcutProjeId}/marka`, { 
            method: 'POST', 
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData 
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster(data.mesaj);
            document.getElementById('yeniMarkaAd').value = '';
            document.getElementById('yeniMarkaEtiket').value = '';
            document.getElementById('yeniMarkaResim').value = '';
            document.getElementById('yeniMarkaNoise').checked = false;
            projeDetayAc(mevcutProjeId);
        }
    }

    async function katilimciDetaylariniYukle() {
        if(!mevcutProjeId) return;
        const sifre = prompt("Bu bölüme erişmek için Admin şifrenizi giriniz:");
        if(!sifre) {
            tabDegistir('analiz');
            return;
        }

        const res = await fetch(`/api/proje/${mevcutProjeId}/katilimci_detaylari`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ sifre })
        });
        const data = await res.json();
        
        if(data.durum !== 'basarili') {
            alert(data.mesaj || "Hata oluştu.");
            tabDegistir('analiz');
            return;
        }

        document.getElementById('katilimciDetayBody').innerHTML = data.profiller.map(p => {
            const durumBadge = p.durum === 'tamamlandi'
                ? '<span class="badge" style="background:var(--success); color:white; font-size:0.6rem;">BİTTİ</span>'
                : (String(p.durum || '').startsWith('gecersiz')
                    ? '<span class="badge" style="background:var(--text-dim); color:white; font-size:0.6rem;">GEÇERSİZ</span>'
                    : '<span class="badge" style="background:var(--warning); color:white; font-size:0.6rem;">YARIM</span>');
            
            let analizBadge = '';
            if (p.analiz_durumu === 'GECERLI') {
                analizBadge = '<span class="badge" style="background:var(--primary); color:white; font-size:0.6rem; margin-top:4px; display:inline-block;">GEÇERLİ</span>';
            } else if (p.analiz_durumu === 'ELENDI') {
                analizBadge = `<span class="badge" style="background:var(--danger); color:white; font-size:0.6rem; margin-top:4px; display:inline-block;" title="${escapeHTML(p.analiz_sebep)}">ELENDİ: ${escapeHTML(p.analiz_sebep)}</span>`;
            } else {
                analizBadge = '<span class="badge" style="background:var(--text-dim); color:white; font-size:0.6rem; margin-top:4px; display:inline-block;">BELİRSİZ</span>';
            }
            
            return `
                <tr>
                    <td>
                        <div style="display:flex; flex-direction:column; align-items:center;">
                            ${durumBadge}
                            ${analizBadge}
                        </div>
                    </td>
                    <td>
                        <div style="font-weight:600;">${escapeHTML(p.ad_soyad || 'Anonim')}</div>
                        <div style="font-size:0.7rem; color:var(--primary);">${p.ip_adresi || '-'}</div>
                        <div style="font-size:0.65rem; color:var(--text-dim);">${escapeHTML(p.panel_pid || '-')}</div>
                    </td>
                    <td>
                        <div style="font-size:0.8rem; font-weight:600;">${escapeHTML(p.cihaz_tipi || '-')}</div>
                        <div style="font-size:0.65rem; color:var(--text-dim); max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHTML(p.tarayici_bilgisi || '')}">${escapeHTML(p.tarayici_bilgisi || '-')}</div>
                    </td>
                    <td>
                        <div style="font-weight:600;">${escapeHTML(p.il || '-')}/${escapeHTML(p.ses_grubu || '-')}</div>
                        ${p.enlem ? `
                            <a href="https://www.google.com/maps?q=${p.enlem},${p.boylam}" target="_blank" style="font-size:0.7rem; color:var(--primary); text-decoration:none; display:flex; align-items:center; gap:3px;">
                                📍 Harita (${Math.round(p.konum_hassasiyet)}m)
                            </a>
                        ` : '<span style="font-size:0.7rem; color:var(--text-dim);">Konum Yok</span>'}
                    </td>
                    <td style="font-size:0.75rem;">${p.baslangic_tarihi ? new Date(p.baslangic_tarihi).toLocaleString('tr-TR') : '-'}</td>
                    <td style="font-size:0.75rem;">${p.bitis_tarihi ? new Date(p.bitis_tarihi).toLocaleString('tr-TR') : '-'}</td>
                </tr>
            `;
        }).join('');
    }

    async function markaSil(id) {
        if(!confirm("Bu markayı silmek istediğinize emin misiniz?")) return;
        await fetch(`/api/marka/${id}/sil`, { 
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        projeDetayAc(mevcutProjeId);
    }

    async function ifadeEkle() {
        if(!mevcutProjeId) return;
        const metin = document.getElementById('yeniIfadeMetin').value.trim();
        const kategori = document.getElementById('yeniIfadeKategori').value.trim();
        const file = document.getElementById('yeniIfadeResim').files[0];
        if(!metin) return toastGoster("Ifade metni girin.");

        const formData = new FormData();
        formData.append('metin', metin);
        formData.append('kategori', kategori);
        if(file) formData.append('resim', file);

        const res = await fetch(`/api/proje/${mevcutProjeId}/ifade`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster(data.mesaj);
            document.getElementById('yeniIfadeMetin').value = '';
            document.getElementById('yeniIfadeResim').value = '';
            projeDetayAc(mevcutProjeId);
        } else {
            toastGoster(data.mesaj || 'Ifade eklenemedi.');
        }
    }

    async function ifadeSil(id) {
        if(!confirm("Bu ifadeyi silmek istediginize emin misiniz?")) return;
        await fetch(`/api/ifade/${id}/sil`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        projeDetayAc(mevcutProjeId);
    }

    function aktifIfadeListesiGetir() {
        return Array.from(document.querySelectorAll('#ifadeListesi li')).map(li => {
            const metin = li.querySelector('div > div > div')?.textContent?.trim() || li.textContent.trim();
            return metin;
        }).filter(Boolean);
    }

    function aiMarkaListesiGetir() {
        return Array.from(document.querySelectorAll('#markaListesi li div div:first-child')).map(el => el.textContent.trim()).filter(Boolean);
    }

    let aiKategoriDurumu = {};
    let mevcutAnalizSeviyesi = 'ifade';

    async function aiKategoriOnerisiAl() {
        if(!mevcutProjeId) return;
        const btn = document.getElementById('btnAiKategori');
        const originalText = btn.textContent;
        const projeAd = document.getElementById('detayProjeAd').textContent;
        const hedefKitle = document.getElementById('aiHedeKitle').value.trim();
        const markalar = aiMarkaListesiGetir();
        const mevcutIfadeler = aktifIfadeListesiGetir();
        if(markalar.length === 0) return toastGoster('Once en az bir marka ekleyin.');

        btn.disabled = true;
        btn.textContent = 'Kategoriler kuruluyor...';
        try {
            const res = await fetch('/api/ai_kategori_onerisi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ proje_ad: projeAd, markalar, hedef_kitle: hedefKitle, mevcut_ifadeler: mevcutIfadeler })
            });
            const data = await res.json();
            const kategoriler = (data.kategoriler || []).slice(0, 6);
            if(kategoriler.length === 0) return toastGoster('AI kategori onerisi uretemedi.');

            const liste = document.getElementById('aiOneriListe');
            liste.innerHTML = kategoriler.map(k => `
                <button class="btn btn-outline btn-sm" style="background:white;" onclick='kategoriSec(${JSON.stringify(k)})'>${escapeHTML(k)}</button>
            `).join('');
            document.getElementById('aiOneriKutusu').style.display = 'block';
            document.getElementById('aiKategoriIfadeKutusu').style.display = 'block';
            aiKategoriDurumu = {};
            for (const kategori of kategoriler) {
                aiKategoriDurumu[kategori] = { oneriler: [], redler: [] };
                await aiKategoriIfadeleriAl(kategori, true);
            }
            toastGoster('Kategori seti hazir.');
        } catch (e) {
            toastGoster('AI kategori akisi baslatilamadi.');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    function kategoriSec(kategori) {
        document.getElementById('yeniIfadeKategori').value = kategori;
        if (!aiKategoriDurumu[kategori]) {
            aiKategoriDurumu[kategori] = { oneriler: [], redler: [] };
        }
        renderAiKategoriKartlari();
        toastGoster(`${kategori} kategorisi secildi.`);
    }

    async function aiKategoriIfadeleriAl(kategori, tazele = false) {
        if(!mevcutProjeId || !kategori) return;
        const projeAd = document.getElementById('detayProjeAd').textContent;
        const hedefKitle = document.getElementById('aiHedeKitle').value.trim();
        const markalar = aiMarkaListesiGetir();
        const mevcutIfadeler = aktifIfadeListesiGetir();
        const durum = aiKategoriDurumu[kategori] || { oneriler: [], redler: [] };
        if (tazele) {
            durum.redler = [...durum.redler, ...(durum.oneriler || [])];
        }
        aiKategoriDurumu[kategori] = durum;
        renderAiKategoriKartlari();
        try {
            const res = await fetch('/api/ai_kategori_ifade_onerisi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({
                    proje_ad: projeAd,
                    markalar,
                    hedef_kitle: hedefKitle,
                    kategori,
                    mevcut_ifadeler: mevcutIfadeler,
                    dislanan_ifadeler: durum.redler || []
                })
            });
            const data = await res.json();
            aiKategoriDurumu[kategori] = {
                oneriler: (data.oneriler || []).slice(0, 4),
                redler: durum.redler || []
            };
            renderAiKategoriKartlari();
        } catch (e) {
            toastGoster(`${kategori} icin AI onerisi alinamadi.`);
        }
    }

    function renderAiKategoriKartlari() {
        const kutu = document.getElementById('aiKategoriIfadeKutusu');
        const alan = document.getElementById('aiKategoriKartlari');
        if (!alan) return;
        const entries = Object.entries(aiKategoriDurumu || {});
        if (entries.length === 0) {
            kutu.style.display = 'none';
            return;
        }
        kutu.style.display = 'block';
        alan.innerHTML = entries.map(([kategori, bilgi]) => {
            const oneriler = bilgi.oneriler || [];
            const chips = oneriler.length > 0
                ? oneriler.map(o => `
                    <div style="background:white; border:1px solid #e2e8f0; padding:0.4rem 0.8rem; border-radius:20px; font-size:0.8rem; display:flex; align-items:center; gap:0.5rem;">
                        <span>${escapeHTML(o)}</span>
                        <button onclick='kategoriIcinHizliIfadeEkle(${JSON.stringify(kategori)}, ${JSON.stringify(o)})' style="background:none; border:none; color:var(--success); font-weight:700; cursor:pointer; padding:0 2px;">+</button>
                    </div>
                `).join('')
                : '<div style="font-size:0.8rem; color:var(--text-dim);">Oneri hazirlaniyor...</div>';
            return `
                <div style="border:1px solid var(--border); border-radius:12px; padding:0.85rem; background:rgba(255,255,255,0.02);">
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; margin-bottom:0.65rem; flex-wrap:wrap;">
                        <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                            <strong style="color:var(--text);">${escapeHTML(kategori)}</strong>
                            <button class="btn btn-outline btn-sm" onclick='kategoriSec(${JSON.stringify(kategori)})'>Kullan</button>
                        </div>
                        <button class="btn btn-outline btn-sm" onclick='aiKategoriIfadeleriAl(${JSON.stringify(kategori)}, true)'>Begenmedim, Degistir</button>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:0.5rem;">${chips}</div>
                </div>
            `;
        }).join('');
    }

    async function kategoriIcinHizliIfadeEkle(kategori, metin) {
        document.getElementById('yeniIfadeKategori').value = kategori;
        await hizliIfadeEkle(metin, kategori);
    }

    async function aiIfadeOnerisiAl() {
        await aiKategoriOnerisiAl();
    }

    async function hizliIfadeEkle(metin, kategori = '') {
        if(!mevcutProjeId) return;
        const formData = new FormData();
        formData.append('metin', metin);
        formData.append('kategori', kategori || document.getElementById('yeniIfadeKategori').value.trim());

        const res = await fetch(`/api/proje/${mevcutProjeId}/ifade`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster(`Eklendi: ${metin}`);
            projeDetayAc(mevcutProjeId);
        } else {
            toastGoster(data.mesaj || 'Ifade eklenemedi.');
        }
    }

    let sonAnalizVerisi = []; // Lokal filtreleme için global değişken
    let sonAnalizPaket = null;
    let mevcutTestTuru = 'standart';

    function analizModuGuncelle(data) {
        const isMcrt = mevcutTestTuru === 'mcrt';
        const badge = document.getElementById('analysisEngineBadge');
        const source = document.getElementById('analysisSourceInfo');
        const metrics = document.getElementById('analysisMetricList');
        const aiTitle = document.querySelector('#aiCard .card-title');
        const qFourthLabel = document.getElementById('qFourthLabel');

        if(badge) {
            badge.textContent = isMcrt ? 'Aktif Analiz Motoru: MCRT' : 'Aktif Analiz Motoru: IRT';
            badge.style.color = isMcrt ? 'var(--warning)' : 'var(--primary)';
        }
        if(source) source.textContent = `Veri kaynağı: ${data.veri_kaynagi || (isMcrt ? 'mcrt_cevaplar' : 'cevaplar')}`;
        if(metrics) {
            metrics.textContent = isMcrt
                ? 'Seçilme Payı • Tepki Hızı • Zihinsel Dominans • Hiç seçilmeyen seçenekler • Stimulus bazlı dağılım'
                : 'Explicit Algı • Implicit Güç • GAP • Korelasyon • Katılımcı kalite elemesi';
        }
        if(aiTitle) aiTitle.textContent = isMcrt ? 'Yapay Zeka MCRT Stratejik Analizi' : 'Yapay Zeka IRT Uzmanı Analizi';
        if(qFourthLabel) qFourthLabel.textContent = isMcrt ? 'ORT. TEPKİ HIZI (MS)' : 'ELENEN TRIAL (%)';
    }

    function mcrtAnalizGorunumuKur(data) {
        const wrap = document.getElementById('analysisViewWrap');
        const select = document.getElementById('analysisViewFilter');
        if(!wrap || !select) return;

        const bloklar = data && data.blok_analizleri ? data.blok_analizleri : {};
        const secenekler = [];
        if (data && data.varsayilan_gorunum === 'birlesik') secenekler.push({ value: 'birlesik', label: 'Birlesik Bag Haritasi' });
        if (bloklar.marka_merkez) secenekler.push({ value: 'marka_merkez', label: 'Marka Merkez Blogu' });
        if (bloklar.ifade_merkez) secenekler.push({ value: 'ifade_merkez', label: 'Ifade Merkez Blogu' });

        if (mevcutTestTuru !== 'mcrt' || secenekler.length === 0) {
            wrap.style.display = 'none';
            select.innerHTML = '';
            return;
        }

        const oncekiDeger = select.value || data.varsayilan_gorunum || secenekler[0].value;
        select.innerHTML = secenekler.map(s => `<option value="${s.value}">${s.label}</option>`).join('');
        select.value = secenekler.some(s => s.value === oncekiDeger) ? oncekiDeger : secenekler[0].value;
        wrap.style.display = 'block';
    }

    function kategoriBazliOzetUret(ozet) {
        if (!ozet || ozet.length === 0) return [];
        const grup = new Map();
        ozet.forEach(row => {
            const kategori = (row.kategori || '').trim() || 'Kategorisiz';
            const marka = row.marka || row.cevap_metin || '-';
            const key = `${marka}__${kategori}`;
            if (!grup.has(key)) {
                grup.set(key, {
                    marka,
                    ifade: kategori,
                    kategori,
                    explicit_pct_toplam: 0,
                    implicit_skor_toplam: 0,
                    mcrt_skor_toplam: 0,
                    secilme_orani_toplam: 0,
                    toplam_secilme: 0,
                    n: 0
                });
            }
            const item = grup.get(key);
            item.explicit_pct_toplam += Number(row.explicit_pct || 0);
            item.implicit_skor_toplam += Number(row.implicit_skor || 0);
            item.mcrt_skor_toplam += Number(row.mcrt_skor || row.implicit_skor || 0);
            item.secilme_orani_toplam += Number(row.secilme_orani || row.explicit_pct || 0);
            item.toplam_secilme += Number(row.toplam_secilme || 0);
            item.n += 1;
        });
        return Array.from(grup.values()).map(item => ({
            marka: item.marka,
            ifade: item.kategori,
            kategori: item.kategori,
            explicit_pct: Number((item.explicit_pct_toplam / Math.max(item.n, 1)).toFixed(1)),
            implicit_skor: Number((item.implicit_skor_toplam / Math.max(item.n, 1)).toFixed(1)),
            mcrt_skor: Number((item.mcrt_skor_toplam / Math.max(item.n, 1)).toFixed(1)),
            secilme_orani: Number((item.secilme_orani_toplam / Math.max(item.n, 1)).toFixed(1)),
            toplam_secilme: item.toplam_secilme,
            kategori_satiri: true,
            n: item.n
        }));
    }

    function analizSeviyesiGuncelle(data) {
        const wrap = document.getElementById('analysisAggregationWrap');
        const select = document.getElementById('analysisAggregationFilter');
        if (!wrap || !select) return;
        const kategoriOzet = (data && data.kategori_ozet) ? data.kategori_ozet : [];
        const kategoriVar = kategoriOzet.length > 0;
        wrap.style.display = kategoriVar ? 'block' : 'none';
        select.value = kategoriVar ? mevcutAnalizSeviyesi : 'ifade';
        if (!kategoriVar) mevcutAnalizSeviyesi = 'ifade';
    }

    function aktifAnalizVerisiGetir() {
        if (!sonAnalizPaket) return [];
        const secim = document.getElementById('analysisViewFilter')?.value;
        let baz = [];
        if (mevcutTestTuru === 'mcrt' && secim && sonAnalizPaket.blok_analizleri && sonAnalizPaket.blok_analizleri[secim]) {
            baz = sonAnalizPaket.blok_analizleri[secim];
        } else {
            baz = sonAnalizPaket.ozet || [];
        }
        if (mevcutAnalizSeviyesi === 'kategori') {
            return kategoriBazliOzetUret(baz);
        }
        return baz;
    }

    function analizSeviyesiDegisti() {
        mevcutAnalizSeviyesi = document.getElementById('analysisAggregationFilter')?.value || 'ifade';
        analizGorunumuDegisti();
    }

    function analizGorunumuDegisti() {
        sonAnalizVerisi = aktifAnalizVerisiGetir();
        const qDetails = document.getElementById('qDetails');
        if (qDetails && mevcutTestTuru === 'mcrt') {
            const gorunum = document.getElementById('analysisViewFilter')?.selectedOptions?.[0]?.textContent || 'MCRT';
            const seviye = mevcutAnalizSeviyesi === 'kategori' ? 'Kategori Bazli' : 'Ifade Bazli';
            qDetails.textContent = `${gorunum} / ${seviye} i?in yuklenen analiz satiri: ${sonAnalizVerisi.length}.`;
        }
        renderMainCharts(sonAnalizVerisi);
        renderGapChart(sonAnalizVerisi);
        renderRadarChart(sonAnalizVerisi);
        scatterGuncelleLocal();
    }

    async function analizYukle() {
        const qDetails = document.getElementById('qDetails');
        try {
            if(qDetails) qDetails.textContent = 'Analiz verileri yükleniyor...';
            const f = { cinsiyet: document.getElementById('fCinsiyet').value, ses_grubu: document.getElementById('fSes').value, yas_min: document.getElementById('fYasMin').value, yas_max: document.getElementById('fYasMax').value };
            const query = new URLSearchParams(f).toString();
            const istBody = document.getElementById('istatistikBody');
            if (istBody) {
                istBody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--warning);">Bu tablo için hesaplama yapılıyor...</td></tr>';
            }
            const res = await fetch(`/api/proje/${mevcutProjeId}/analiz?${query}`);
            if(!res.ok) throw new Error(`Analiz API hatası: ${res.status} ${res.statusText}`);
            const data = await res.json();
            
            if(data && data.ozet) { 
                sonAnalizPaket = data;
                mevcutTestTuru = data.test_turu || 'standart';
                analizModuGuncelle(data);
                analizSeviyesiGuncelle(data);
                mcrtAnalizGorunumuKur(data);
                sonAnalizVerisi = aktifAnalizVerisiGetir();

                // Kalite Özeti
                if(data.kalite) {
                    const toplamN = data.kalite.toplam_katilimci ?? 0;
                    const elenenN = data.kalite.elenen_katilimci ?? 0;
                    const finalN = data.kalite.kalan_katilimci ?? data.kalite.gecerli_katilimci ?? toplamN;
                    document.getElementById('qTotalN').textContent = toplamN;
                    document.getElementById('qExcludedN').textContent = elenenN;
                    document.getElementById('qFinalN').textContent = finalN;
                    document.getElementById('qTrialPct').textContent = mevcutTestTuru === 'mcrt' ? Math.round(data.kalite.ortalama_hiz || 0) : '%0';
                    
                    if(qDetails) {
                        if(data.kalite.detaylar && data.kalite.detaylar.length > 0) {
                            const elenenler = data.kalite.detaylar.filter(d => d.durum === 'ELENDI');
                            qDetails.innerHTML = elenenler.length > 0 ? `Yüklenen analiz satırı: ${sonAnalizVerisi.length}. Elenenler: ` + elenenler.map(d => `ID:${d.oturum_id}`).join(', ') : `Yüklenen analiz satırı: ${sonAnalizVerisi.length}. Tüm katılımcılar kriterleri geçti.`;
                        } else {
                            qDetails.textContent = `Yüklenen analiz satırı: ${sonAnalizVerisi.length}.`;
                        }
                    }
                }

                if(sonAnalizVerisi.length === 0) {
                    if(qDetails) qDetails.textContent = 'Bu filtrelerde analiz edilecek veri bulunamadı. Filtreleri temizleyip tekrar deneyin.';
                    renderHamVeri();
                    renderKatilimciAnalizi();
                    return;
                }

                if(mevcutTestTuru === 'mcrt' && qDetails) {
                    const sifirSecimler = sonAnalizVerisi.filter(o => (o.toplam_secilme || 0) === 0).map(o => `${o.marka}: ${o.cevap_metin || o.ifade}`);
                    if(sifirSecimler.length > 0) {
                        qDetails.innerHTML += `<br><strong>Hiç seçilmedi:</strong> ${sifirSecimler.map(escapeHTML).join(', ')}`;
                    }
                }

                if(typeof Chart === 'undefined') {
                    throw new Error('Chart.js yüklenemedi. Sayfayı Ctrl+F5 ile yenileyin veya CDN erişimini kontrol edin.');
                }

                // Grafik Başlıklarını Güncelle
                const isMcrt = mevcutTestTuru === 'mcrt';
                document.querySelector('#chartExplicit')?.parentElement?.querySelector('.card-title') && (document.querySelector('#chartExplicit').parentElement.querySelector('.card-title').textContent = isMcrt ? "📊 Seçilme Payı (%)" : "📉 Explicit Algı (%)");
                document.querySelector('#chartImplicit')?.parentElement?.querySelector('.card-title') && (document.querySelector('#chartImplicit').parentElement.querySelector('.card-title').textContent = isMcrt ? "🧠 Zihinsel Dominans (Skor)" : "🧠 Implicit Güç (Skor)");
                document.querySelector('#chartGap')?.parentElement?.querySelector('.card-title') && (document.querySelector('#chartGap').parentElement.querySelector('.card-title').textContent = isMcrt ? "⚖️ Pay vs Hız Analizi" : "📉 GAP Analizi (Beyan vs Bilinçaltı)");
                document.querySelector('#chartScatter')?.parentElement?.querySelector('.card-title') && (document.querySelector('#chartScatter').parentElement.querySelector('.card-title').textContent = isMcrt ? "🗺️ Zihinsel Harita (MCRT)" : "🗺️ Bilinçaltı Algı Haritası (Scatter)");
                const statBaslik = document.getElementById('istatistikKartBaslik');
                const statAciklama = document.getElementById('istatistikKartAciklama');
                if (statBaslik) statBaslik.textContent = isMcrt ? '🔬 MCRT İstatistiksel Karşılaştırma (Marka Ayrışması)' : '🔬 İstatistiksel Anlamlılık ve Etki Büyüklüğü (Marka Kıyaslama)';
                if (statAciklama) statAciklama.textContent = isMcrt
                    ? 'Markalar arasındaki seçilme payı ve zihinsel dominans farklarının istatistiksel anlamlılığı.'
                    : 'Markalar arasındaki farkların bilimsel olarak anlamlılığı (p-value) ve etkinin büyüklüğü (Cohen\'s d).';
                const statHeadings = [
                    'Karşılaştırma',
                    isMcrt ? 'Seçilme Payı Farkı' : 'Explicit Fark',
                    isMcrt ? 'P-Value (Pay)' : 'P-Value (Exp)',
                    'Güven Aralığı (%95)',
                    isMcrt ? 'P-Value (Skor)' : 'P-Value (Imp)',
                    'Cohen\'s d',
                    'Yorum'
                ];
                statHeadings.forEach((txt, idx) => {
                    const el = document.getElementById(`istatistikTh${idx}`);
                    if (el) el.textContent = txt;
                });

                // İfade Filtresini Doldur (Scatter Plot için)
                const sFilter = document.getElementById('scatterIfadeFiltre');
                const currentVal = sFilter.value;
                sFilter.innerHTML = '<option value="">Tüm İfadeler (Karışık)</option>';
                const ifadeler = [...new Set(sonAnalizVerisi.map(o => o.ifade))];
                ifadeler.forEach(ifd => {
                    const opt = document.createElement('option');
                    opt.value = ifd;
                    opt.textContent = ifd;
                    sFilter.appendChild(opt);
                });
                sFilter.value = currentVal;

                // Grafikleri Çiz
                renderMainCharts(sonAnalizVerisi); 
                renderGapChart(sonAnalizVerisi); 
                renderRadarChart(sonAnalizVerisi); 
                scatterGuncelleLocal(); 
                renderHamVeri(); 
                renderKatilimciAnalizi();
                renderIstatistikTablosu(query);
            }
        } catch (e) {
            console.error("Analiz yükleme hatası:", e);
            if(qDetails) qDetails.textContent = `Analiz yükleme hatası: ${e.message}`;
        }
    }

    async function renderIstatistikTablosu(query = '') {
        const istBody = document.getElementById('istatistikBody');
        if (!istBody || !mevcutProjeId) return;
        istBody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--warning);">Bu tablo için hesaplama yapılıyor...</td></tr>';
        try {
            const q = query ? `?${query}` : '';
            const res = await fetch(`/api/proje/${mevcutProjeId}/analiz_istatistik${q}`);
            if (!res.ok) throw new Error(`İstatistik API hatası: ${res.status} ${res.statusText}`);
            const data = await res.json();
            if(data.istatistik && data.istatistik.length > 0) {
                istBody.innerHTML = data.istatistik.map(s => `<tr><td>${s.marka_a} vs ${s.marka_b}</td><td>%${s.explicit_fark}</td><td>${s.explicit_p} ${s.explicit_anlamlilik || ''}</td><td>${s.guven_araligi || '-'}</td><td>${s.implicit_p} ${s.implicit_anlamlilik || ''}</td><td>${s.cohens_d}</td><td>${s.yorum || s.etki_buyuklugu || '-'}</td></tr>`).join('');
            } else if (data.mesaj) {
                istBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--warning);">${escapeHTML(data.mesaj)}</td></tr>`;
            } else {
                istBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Bu analiz türü veya filtre için istatistiksel fark tablosu yok.</td></tr>';
            }
        } catch (err) {
            console.error('İstatistik tablosu yükleme hatası:', err);
            istBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--danger);">İstatistik tablosu yüklenemedi: ${err.message}</td></tr>`;
        }
    }

    function scatterGuncelleLocal() {
        const seciliIfade = document.getElementById('scatterIfadeFiltre').value;
        let cizilecekVeri = sonAnalizVerisi;
        
        if(seciliIfade) {
            cizilecekVeri = sonAnalizVerisi.filter(o => o.ifade === seciliIfade);
        }
        
        renderScatter(cizilecekVeri);
    }

    async function renderKatilimciAnalizi() {
        const tbody = document.getElementById('listKatilimciAnaliz');
        const id = mevcutProjeId;
        
        if(!id) {
            console.warn("Katilimci Analiz: Proje ID bulunamadi, bekleniyor...");
            return;
        }

        try {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Analiz verileri hazırlanıyor...</td></tr>';
            const res = await fetch(`/api/proje/${id}/katilimci_analiz`);
            
            if (!res.ok) {
                throw new Error(`Sunucu hatası: ${res.status} ${res.statusText}`);
            }
            
            const data = await res.json();
            
            if(data.durum === 'basarili' && data.katilimcilar && data.katilimcilar.length > 0) {
                tbody.innerHTML = '';
                data.katilimcilar.forEach(k => {
                    const tr = document.createElement('tr');
                    const hizColor = k.hiz_ms < 800 ? 'var(--success)' : (k.hiz_ms > 1500 ? 'var(--danger)' : 'var(--warning)');
                    
                    tr.innerHTML = `
                        <td><strong>${escapeHTML(k.ad_soyad)}</strong><br><small style="color:var(--text-dim)">${escapeHTML(k.pid)}</small></td>
                        <td>${escapeHTML(k.yas)} Yaş, ${escapeHTML(k.cinsiyet)}, ${escapeHTML(k.ses)}</td>
                        <td style="color:${hizColor}; font-weight:700;">${escapeHTML(k.hiz_ms)} ms</td>
                        <td><span class="badge badge-primary">${escapeHTML(k.guclu_cevap)} / ${escapeHTML(k.toplam_cevap)}</span></td>
                        <td>
                            <button class="btn ${seciliTakipOturumId === k.oturum_id ? 'btn-success' : 'btn-outline'} btn-sm" onclick="katilimciSec('${escapeHTML(k.oturum_id)}', '${escapeHTML(k.pid)}', '${escapeHTML(k.ad_soyad).replace(/'/g, "\\'")}', this)">${seciliTakipOturumId === k.oturum_id ? '✅ Seçildi' : 'Takip İçin Seç'}</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Bu kırılımda analiz edilecek katılımcı verisi bulunamadı.</td></tr>';
            }
        } catch (err) {
            console.error("Katilimci Analiz Hatasi:", err);
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--danger);">Veriler yüklenirken bir hata oluştu: ${err.message}</td></tr>`;
        }
    }

    function katilimciSec(oturumId, pid, isim, btn) {
        if (seciliTakipOturumId === oturumId) {
            seciliTakipOturumId = null;
            seciliTakipIsim = null;
            toastGoster(`${isim} filtreden çıkarıldı.`);
        } else {
            seciliTakipOturumId = oturumId;
            seciliTakipIsim = `${isim} (${pid})`;
            toastGoster(`${isim} için ham veri filtresi uygulandı.`);
        }
        renderKatilimciAnalizi();
        renderHamVeri();
    }

    function chartBosMesaj(canvasId, mesaj, goster) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const parent = canvas.parentElement;
        let msg = parent.querySelector(`[data-empty-for="${canvasId}"]`);
        if(!msg) {
            msg = document.createElement('div');
            msg.dataset.emptyFor = canvasId;
            msg.style.cssText = 'font-size:0.85rem; color:var(--text-dim); text-align:center; padding:1rem;';
            parent.appendChild(msg);
        }
        msg.textContent = mesaj;
        msg.style.display = goster ? 'block' : 'none';
        canvas.style.display = goster ? 'none' : 'block';
    }

    function renderMainCharts(ozet) {
        const bos = !ozet || ozet.length === 0;
        chartBosMesaj('chartExplicit', 'Bu filtrede veri yok.', bos);
        chartBosMesaj('chartImplicit', 'Bu filtrede veri yok.', bos);
        if(bos) return;
        const labels = [...new Set(ozet.map(o => o.ifade))];
        const markalar = [...new Set(ozet.map(o => o.marka || o.cevap_metin))];
        const isMcrt = mevcutTestTuru === 'mcrt';
        const key1 = isMcrt ? 'secilme_orani' : 'explicit_pct';
        const key2 = isMcrt ? 'mcrt_skor' : 'implicit_skor';

        if(chartExplicit) chartExplicit.destroy();
        chartExplicit = new Chart(document.getElementById('chartExplicit'), { type: 'bar', data: { labels, datasets: markalar.map((m, i) => ({ label: m, data: labels.map(l => (ozet.find(o => (o.marka === m || o.cevap_metin === m) && o.ifade === l) || {})[key1] || 0), backgroundColor: colors[i % colors.length] })) }, options: { responsive: true, scales: { y: { max: 100 } } } });
        if(chartImplicit) chartImplicit.destroy();
        chartImplicit = new Chart(document.getElementById('chartImplicit'), { type: 'bar', data: { labels, datasets: markalar.map((m, i) => ({ label: m, data: labels.map(l => (ozet.find(o => (o.marka === m || o.cevap_metin === m) && o.ifade === l) || {})[key2] || 0), backgroundColor: colors[i % colors.length] })) }, options: { responsive: true, scales: { y: { min: 0, max: 100 } } } });
    }

    function renderGapChart(ozet) {
        const bos = !ozet || ozet.length === 0;
        chartBosMesaj('chartGap', 'Bu filtrede veri yok.', bos);
        if(bos) return;
        const labels = [...new Set(ozet.map(o => o.ifade))];
        const markalar = [...new Set(ozet.map(o => o.marka || o.cevap_metin))];
        const isMcrt = mevcutTestTuru === 'mcrt';
        const key1 = isMcrt ? 'secilme_orani' : 'explicit_pct';
        const key2 = isMcrt ? 'mcrt_skor' : 'implicit_skor';

        if(chartGap) chartGap.destroy();
        chartGap = new Chart(document.getElementById('chartGap'), { type: 'bar', data: { labels, datasets: markalar.map((m, i) => ({ label: m, data: labels.map(l => {
            const d = ozet.find(o => (o.marka === m || o.cevap_metin === m) && o.ifade === l) || { [key1]: 0, [key2]: 0 };
            return d[key1] - d[key2];
        }), backgroundColor: colors[i % colors.length] })) }, options: { responsive: true, scales: { y: { min: -100, max: 100 } } } });
    }

    function renderRadarChart(ozet) {
        const bos = !ozet || ozet.length === 0;
        chartBosMesaj('chartRadar', mevcutTestTuru === 'mcrt' ? 'MCRT için stimulus bazlı dağılım seçilme payı grafiğinde gösterilir.' : 'Bu filtrede veri yok.', bos);
        if(bos) return;
        const labels = [...new Set(ozet.map(o => o.ifade))], markalar = [...new Set(ozet.map(o => o.marka))];
        if(chartRadar) chartRadar.destroy();
        chartRadar = new Chart(document.getElementById('chartRadar'), { type: 'radar', data: { labels, datasets: markalar.map((m, i) => ({ label: m, data: labels.map(l => {
            const d = ozet.find(o => o.marka === m && o.ifade === l) || { implicit_skor: 0 };
            return d.implicit_skor;
        }), borderColor: colors[i % colors.length], backgroundColor: colors[i % colors.length] + '33', fill: true, pointRadius: 4 })) }, options: { responsive: true, scales: { r: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.1)' }, angleLines: { color: 'rgba(255,255,255,0.1)' }, pointLabels: { color: '#94a3b8', font: { size: 10 } } } } } });
    }

    function renderScatter(ozet) {
        const bos = !ozet || ozet.length === 0;
        chartBosMesaj('chartScatter', 'Bu filtrede veri yok.', bos);
        if(bos) return;
        const markalar = [...new Set(ozet.map(o => o.marka || o.cevap_metin))];
        const isMcrt = mevcutTestTuru === 'mcrt';
        const key1 = isMcrt ? 'secilme_orani' : 'explicit_pct';
        const key2 = isMcrt ? 'mcrt_skor' : 'implicit_skor';
        const xTitle = isMcrt ? 'Seçilme Payı %' : 'Explicit Algı %';
        const yTitle = isMcrt ? 'MCRT Skoru (Dominans)' : 'Implicit Güç (0-100)';

        if(chartScatter) chartScatter.destroy();
        chartScatter = new Chart(document.getElementById('chartScatter'), { type: 'scatter', data: { datasets: markalar.map((m, i) => ({ label: m, data: ozet.filter(o => (o.marka === m || o.cevap_metin === m)).map(o => ({ x: o[key1], y: o[key2], ifade: o.ifade })), backgroundColor: colors[i % colors.length], pointRadius: 10, hoverRadius: 15 })) }, options: { maintainAspectRatio: false, scales: { x: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display:true, text: xTitle, color:'#94a3b8' } }, y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display:true, text: yTitle, color:'#94a3b8' } } }, plugins: { tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.raw.ifade} (${c.raw.x}%, ${c.raw.y})` } } } } });
    }

    async function renderHamVeri() {
        const query = seciliTakipOturumId ? `?oturum_id=${encodeURIComponent(seciliTakipOturumId)}` : '';
        const res = await fetch(`/api/proje/${mevcutProjeId}/veriler${query}`);
        const data = await res.json();
        const tbody = document.getElementById('hamVeriBody');
        const filtreBilgi = document.getElementById('hamVeriFiltreBilgi');
        if (filtreBilgi) {
            filtreBilgi.innerHTML = seciliTakipOturumId
                ? `Filtre: <strong>${escapeHTML(seciliTakipIsim)}</strong> <button class="btn btn-outline btn-sm" style="margin-left:.5rem;" onclick="katilimciSecKaldir()">Temizle</button>`
                : 'Son 15 kayıt gösteriliyor';
        }
        if (!data.veriler || data.veriler.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Bu kırılımda ham veri kaydı bulunamadı.</td></tr>';
            return;
        }
        tbody.innerHTML = data.veriler.slice(0, 15).map(v => `<tr><td>${escapeHTML(v.katilimci_id).substring(0,8)}</td><td>${escapeHTML(v.marka) || '-'}</td><td>${escapeHTML(v.ifade) || '-'}</td><td>${escapeHTML(v.cevap) || '-'}</td><td>${escapeHTML(v.sure_ms)}ms</td></tr>`).join('');
    }

    function katilimciSecKaldir() {
        seciliTakipOturumId = null;
        seciliTakipIsim = null;
        renderKatilimciAnalizi();
        renderHamVeri();
    }

    async function projeOlustur() { 
        const ad = document.getElementById('yeniProjeAd').value; 
        if(!ad) return; 
        await fetch('/api/proje/olustur', { 
            method: 'POST', 
            headers: {
                'Content-Type':'application/json',
                'X-CSRFToken': csrfToken
            }, 
            body: JSON.stringify({ad}) 
        }); 
        projeleriYukle(); 
        document.getElementById('yeniProjeAd').value=''; 
    }
    function temaDegistir() { document.body.classList.toggle('light-mode'); }
    function filtreTemizle() { document.getElementById('fCinsiyet').value = ''; document.getElementById('fSes').value = ''; document.getElementById('fYasMin').value = ''; document.getElementById('fYasMax').value = ''; analizYukle(); }
    
    async function toggleCardFullscreen(btn) {
        const card = btn.closest('.analysis-card');
        if (!card) return;
        try {
            if (document.fullscreenElement === card) {
                await document.exitFullscreen();
            } else {
                await card.requestFullscreen();
            }
            setTimeout(() => {
                [chartScatter, chartGap, chartRadar, chartExplicit, chartImplicit].forEach(ch => {
                    if (ch && typeof ch.resize === 'function') ch.resize();
                });
            }, 150);
        } catch (err) {
            console.error('Fullscreen hatası:', err);
        }
    }
    
    function toastGoster(mesaj) {
        const t = document.getElementById('toast');
        t.textContent = mesaj;
        t.style.display = 'block';
        setTimeout(() => t.style.display = 'none', 3000);
    }

    function linkDurumEtiketi(link) {
        const durum = String(link.durum || '').toLowerCase();
        if (durum === 'tamamlandi') return 'Tamamlandi';
        if (durum === 'basladi') return 'Basladi';
        if (durum === 'kullanildi') return 'Kullanildi';
        if (durum === 'aktif') return link.kullanildi ? 'Kullanildi' : 'Hazir';
        return durum || (link.kullanildi ? 'Kullanildi' : 'Hazir');
    }

    async function linkleriYukle() {
        if(!mevcutProjeId) return;
        const res = await fetch(`/api/proje/${mevcutProjeId}/linkler`);
        const data = await res.json();
        const tb = document.getElementById('linkListesiBody');
        const baseUrl = window.location.origin + `/anket/${mevcutProjeKod}/`;
        if(data.durum === 'basarili') {
            tb.innerHTML = data.linkler.map(l => `
                <tr>
                    <td><code>${l.token}</code></td>
                    <td><a href="${baseUrl}${l.token}" target="_blank" style="color:var(--primary-l); text-decoration:none;">${baseUrl}${l.token}</a></td>
                    <td>
                        <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                            <span class="badge ${l.kullanildi ? 'badge-kapali' : 'badge-canli'}">${l.kullanildi ? 'Kapali' : 'Hazir'}</span>
                            <span style="font-size:0.7rem; color:var(--text-dim);">${linkDurumEtiketi(l)}</span>
                            ${(l.yeniden_acma_sayisi || 0) > 0 ? `<span style="font-size:0.7rem; color:var(--text-dim);">yeniden acma:${l.yeniden_acma_sayisi}</span>` : ''}
                            <button class="btn btn-outline btn-sm" style="padding:0.2rem 0.45rem; font-size:0.65rem;" onclick="linkYenidenAc('${l.token}')">Yeniden Ac</button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    }

    async function linkYenidenAc(token) {
        if(!mevcutProjeId) return;
        if(!confirm('Bu link yeniden acilsin mi? Katilimci teste bastan baslar, kaldigi yerden devam etmez.')) return;
        const res = await fetch(`/api/proje/${mevcutProjeId}/link/${token}/yeniden_ac`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster(data.mesaj);
            linkleriYukle();
            renderKatilimciAnalizi();
        } else {
            toastGoster('Hata: ' + data.mesaj);
        }
    }

    async function linkOlustur() {
        if(!mevcutProjeId) return;
        const adet = document.getElementById('inputLinkAdet').value;
        const res = await fetch(`/api/proje/${mevcutProjeId}/link_olustur`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ adet: parseInt(adet) })
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster(data.mesaj);
            linkleriYukle();
        } else {
            toastGoster("Hata: " + data.mesaj);
        }
    }

    async function raporOlustur() {
        if(!mevcutProjeId) return;
        toastGoster("Rapor olu?turuluyor, l?tfen bekleyin...");
        
        const aiContainer = document.getElementById('aiRaporContainer');
        const aiText = (aiContainer && aiContainer.style.display !== 'none') ? aiContainer.innerHTML : null;

        const res = await fetch(`/api/proje/${mevcutProjeId}/analiz_rapor`, { 
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ ai_text: aiText })
        });
        const data = await res.json();
        if(data.durum === 'basarili') {
            toastGoster("Rapor haz?r! Paket indiriliyor...");
            if (data.paket_url) {
                const a = document.createElement('a');
                a.href = data.paket_url;
                a.download = data.paket_isim || '';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } else if (Array.isArray(data.dosyalar)) {
                data.dosyalar.forEach(d => {
                    const a = document.createElement('a');
                    a.href = d.url;
                    a.download = d.isim;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                });
            }
        } else {
            toastGoster("Hata: " + data.mesaj);
        }
    }

    async function aiRaporUret() {
        if(!mevcutProjeId) return;
        const btn = document.getElementById('btnAiRapor');
        const container = document.getElementById('aiRaporContainer');
        
        btn.disabled = true;
        btn.textContent = "Derin Analiz Üretiliyor... Lütfen bekleyin (1-2 Dk)";
        container.style.display = "block";
        container.innerHTML = "<div style='text-align:center; padding:2rem;'>Yapay Zeka IRT Uzmanı verilerinizi okuyor ve stratejik raporu yazıyor... ⏳</div>";

        try {
            const res = await fetch(`/api/proje/${mevcutProjeId}/ai_rapor`, { 
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            // Eğer sunucu JSON dönmezse (örn: 404 HTML sayfası), patlamamak için kontrol et
            const contentType = res.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                throw new Error("Sunucudan geçersiz bir yanıt geldi. Flask sunucusunu yeniden başlattığınızdan emin olun.");
            }

            const data = await res.json();
            
            if(data.durum === 'basarili') {
                container.innerHTML = data.html;
                document.getElementById('btnAiPdf').style.display = 'block';
                toastGoster("AI Raporu başarıyla üretildi!");
            } else {
                container.innerHTML = `<div class='alert alert-danger'>Hata: ${data.mesaj}</div>`;
                toastGoster("Hata: " + data.mesaj);
            }
        } catch (err) {
            container.innerHTML = `<div class='alert alert-danger'>Bağlantı hatası: ${err.message}</div>`;
        } finally {
            btn.disabled = false;
            btn.textContent = "Analiz Üret (DeepSeek)";
        }
    }

    function aiRaporPdfIndir() {
        const element = document.getElementById('aiRaporContainer');
        const opt = {
            margin:       [15, 15],
            filename:     'AI_Stratejik_Analiz_Raporu.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2 },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };
        html2pdf().set(opt).from(element).save();
    }

    projeleriYukle();
    
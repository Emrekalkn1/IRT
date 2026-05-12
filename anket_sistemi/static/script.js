/**
 * Marka Algi Anket Sistemi - JavaScript
 * Proje bazli dinamik - Tek tek soru gosterme
 * Alistirma (Kalibrasyon) ve Normalizasyon destegi
 */

const cevaplar = [];
let mevcutSoruIndex = 0;
let soruBaslangicZaman = null;
let sorular = [];
let baselineMs = 0;
let alistirmaBitti = false;
let profilVerisi = null;
let baslangicZamani = null;
let baglantiHatasi = false;
let alistirmaHataSayisi = 0;
let alistirmaToplam = 0;
let ilceVerisi = [];
let soruRenderToken = 0;


// Çift Tıklama Zoom Engelleme (Mobil)
(function () {
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function (e) {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, { passive: false });

    // Çift tıklama (masaüstü) engelleme
    document.addEventListener('dblclick', function (e) {
        e.preventDefault();
    }, { passive: false });
})();

const oturumId = 'oid_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
const anketConfigEl = document.getElementById('anketConfigData');
let anketConfig = {};

if (anketConfigEl) {
    try {
        anketConfig = JSON.parse(anketConfigEl.textContent || '{}');
    } catch (err) {
        console.error('Anket config okunamadi:', err);
    }
}

const PROJE_ID = anketConfig.PROJE_ID ?? null;
const PROJE_KOD = anketConfig.PROJE_KOD ?? '';
const MARKALAR = Array.isArray(anketConfig.MARKALAR) ? anketConfig.MARKALAR : [];
const IFADELER = Array.isArray(anketConfig.IFADELER) ? anketConfig.IFADELER : [];
const ALISTIRMA_AKTIF = anketConfig.ALISTIRMA_AKTIF ?? 1;
const SORU_RANDOMIZE = anketConfig.SORU_RANDOMIZE ?? 0;
const KATILIMCI_TOKEN = anketConfig.KATILIMCI_TOKEN ?? '';
const TEST_TURU = anketConfig.TEST_TURU ?? 'standart';
const PANEL_COMPLETE = anketConfig.PANEL_COMPLETE ?? '';
const MCRT_SECENEKLER = Array.isArray(anketConfig.MCRT_SECENEKLER) ? anketConfig.MCRT_SECENEKLER : [];
const MCRT_KURGU = anketConfig.MCRT_KURGU ?? 'marka_merkez';
const MCRT_YERLESIM = anketConfig.MCRT_YERLESIM ?? 'grid_standart';

function acceptCookies() {
    localStorage.setItem('cookie_accepted', 'true');
    const banner = document.getElementById('cookieBanner');
    if (banner) {
        banner.style.display = 'none';
    }
}

window.addEventListener('offline', () => {
    baglantiHatasi = true;
    const alertBox = document.createElement('div');
    alertBox.id = 'connectionAlert';
    alertBox.style = 'position:fixed; top:0; left:0; width:100%; background:#ef4444; color:white; text-align:center; padding:10px; z-index:9999; font-weight:bold;';
    alertBox.textContent = '⚠️ İnternet bağlantınız koptu! Lütfen bağlantınızı kontrol edin.';
    document.body.appendChild(alertBox);
});

window.addEventListener('online', () => {
    const alertBox = document.getElementById('connectionAlert');
    if (alertBox) {
        alertBox.style.background = '#10b981';
        alertBox.textContent = '✅ Bağlantı geri geldi. Devam edebilirsiniz.';
        setTimeout(() => alertBox.remove(), 3000);
    }
});

window.addEventListener('beforeunload', (e) => {
    if (baslangicZamani && !document.getElementById('screenTesekkur').classList.contains('active')) {
        e.preventDefault();
        e.returnValue = 'Anketiniz henüz tamamlanmadı. Ayrılmak istediğinize emin misiniz?';
    }
});

// oturumId zaten yukarıda tanımlandı

const ALISTIRMA_SORULARI_GORSEL = [
    { id: 'a1', ad: 'Kuş', ifade: 'Uçar mı?', img: 'kus.png', cevap: 'Evet' },
    { id: 'a2', ad: 'Kaplumbağa', ifade: 'Hızlı mı?', img: 'kaplumbaga.png', cevap: 'Hayır' },
    { id: 'a3', ad: 'Aslan', ifade: 'Vahşi mi?', img: 'aslan.png', cevap: 'Evet' },
    { id: 'a4', ad: 'Salyangoz', ifade: 'Hızlı mı?', img: 'salyangoz.png', cevap: 'Hayır' },
    { id: 'a5', ad: 'Ateş', ifade: 'Sıcak mı?', img: 'ates.png', cevap: 'Evet' },
    { id: 'a6', ad: 'Buz', ifade: 'Sıcak mı?', img: 'buz.png', cevap: 'Hayır' },
    { id: 'a7', ad: 'Güneş', ifade: 'Parlak mı?', img: 'gunes.png', cevap: 'Evet' },
    { id: 'a8', ad: 'Ay', ifade: 'Gece mi çıkar?', img: 'ay.png', cevap: 'Evet' },
    { id: 'a9', ad: 'Fil', ifade: 'Küçük mü?', img: 'fil.png', cevap: 'Hayır' },
    { id: 'a10', ad: 'Fare', ifade: 'Büyük mü?', img: 'fare.png', cevap: 'Hayır' },
    { id: 'a11', ad: 'Taş', ifade: 'Sert mi?', img: 'tas.png', cevap: 'Evet' },
    { id: 'a12', ad: 'Pamuk', ifade: 'Sert mi?', img: 'pamuk.png', cevap: 'Hayır' },
    { id: 'a13', ad: 'Bıçak', ifade: 'Keskin mi?', img: 'bicak.png', cevap: 'Evet' },
    { id: 'a14', ad: 'Limon', ifade: 'Tatlı mı?', img: 'limon.png', cevap: 'Hayır' },
    { id: 'a15', ad: 'Şeker', ifade: 'Ekşi mi?', img: 'seker.png', cevap: 'Hayır' },
    { id: 'a16', ad: 'Su', ifade: 'Islak mı?', img: 'su.png', cevap: 'Evet' },
    { id: 'a17', ad: 'Kar', ifade: 'Siyah mı?', img: 'kar.png', cevap: 'Hayır' },
    { id: 'a18', ad: 'Köpek', ifade: 'Havlar mı?', img: 'kopek.png', cevap: 'Evet' },
    { id: 'a19', ad: 'Balık', ifade: 'Yürür mü?', img: 'balik.png', cevap: 'Hayır' },
    { id: 'a20', ad: 'Zürafa', ifade: 'Uzun mu?', img: 'zurafa.png', cevap: 'Evet' }
];

const ALISTIRMA_SORULARI_SES = [
    { id: 'sa1', ad: 'Alkış', ifade: 'Kalabalık mı?', img: 'Alkis.mp3', cevap: 'Evet' },
    { id: 'sa2', ad: 'Aslan', ifade: 'Sakin mi?', img: 'Aslan.mp3', cevap: 'Hayır' },
    { id: 'sa3', ad: 'Ağlayan Bebek', ifade: 'Gülüyor mu?', img: 'Bebekaglama.mp3', cevap: 'Hayır' },
    { id: 'sa4', ad: 'Böcek', ifade: 'Büyük mü?', img: 'Bocek.mp3', cevap: 'Hayır' },
    { id: 'sa5', ad: 'Kalp Atışı', ifade: 'Kalp mi?', img: 'Kalpatisi.mp3', cevap: 'Evet' },
    { id: 'sa6', ad: 'Klavye', ifade: 'Yazı mı yazılıyor?', img: 'Klavye.mp3', cevap: 'Evet' },
    { id: 'sa7', ad: 'Korna', ifade: 'Bisiklet mi?', img: 'Korna.mp3', cevap: 'Hayır' },
    { id: 'sa8', ad: 'Motor', ifade: 'Sessiz mi?', img: 'Motor.mp3', cevap: 'Hayır' },
    { id: 'sa9', ad: 'Saat', ifade: 'Zamanı mı gösterir?', img: 'Saat.mp3', cevap: 'Evet' },
    { id: 'sa10', ad: 'Sinyal', ifade: 'Uyarı mı?', img: 'Signal.mp3', cevap: 'Evet' },
    { id: 'sa11', ad: 'Su', ifade: 'Ateş mi?', img: 'Su.mp3', cevap: 'Hayır' },
    { id: 'sa12', ad: 'Titreşim', ifade: 'Telefon mu?', img: 'Titresim.mp3', cevap: 'Evet' }
];

// MCRT Evrensel Alistirma Sorulari (Resim Ortada, Kelimeler Butonlarda - 20 Soru)
const ALISTIRMA_SORULARI_MCRT = [
    { id: 'ma1', img: 'aslan.png', dogru: 'Aslan', secenekler: [{ metin: 'Aslan' }, { metin: 'Zebra' }, { metin: 'Fil' }, { metin: 'Maymun' }] },
    { id: 'ma2', img: 'kus.png', dogru: 'Kuş', secenekler: [{ metin: 'Kuş' }, { metin: 'Balık' }, { metin: 'Fare' }, { metin: 'Zürafa' }] },
    { id: 'ma3', img: 'ates.png', dogru: 'Ateş', secenekler: [{ metin: 'Ateş' }, { metin: 'Buz' }, { metin: 'Su' }, { metin: 'Güneş' }] },
    { id: 'ma4', img: 'buz.png', dogru: 'Buz', secenekler: [{ metin: 'Kar' }, { metin: 'Buz' }, { metin: 'Taş' }, { metin: 'Su' }] },
    { id: 'ma5', img: 'balik.png', dogru: 'Balık', secenekler: [{ metin: 'Balık' }, { metin: 'Kuş' }, { metin: 'Aslan' }, { metin: 'Fil' }] },
    { id: 'ma6', img: 'limon.png', dogru: 'Limon', secenekler: [{ metin: 'Şeker' }, { metin: 'Limon' }, { metin: 'Bıçak' }, { metin: 'Pamuk' }] },
    { id: 'ma7', img: 'gunes.png', dogru: 'Güneş', secenekler: [{ metin: 'Ay' }, { metin: 'Güneş' }, { metin: 'Ateş' }, { metin: 'Buz' }] },
    { id: 'ma8', img: 'ay.png', dogru: 'Ay', secenekler: [{ metin: 'Güneş' }, { metin: 'Ay' }, { metin: 'Kar' }, { metin: 'Taş' }] },
    { id: 'ma9', img: 'tas.png', dogru: 'Taş', secenekler: [{ metin: 'Pamuk' }, { metin: 'Taş' }, { metin: 'Bıçak' }, { metin: 'Limon' }] },
    { id: 'ma10', img: 'pamuk.png', dogru: 'Pamuk', secenekler: [{ metin: 'Taş' }, { metin: 'Pamuk' }, { metin: 'Şeker' }, { metin: 'Kar' }] },
    { id: 'ma11', img: 'zurafa.png', dogru: 'Zürafa', secenekler: [{ metin: 'Zürafa' }, { metin: 'Fil' }, { metin: 'Zebra' }, { metin: 'Aslan' }] },
    { id: 'ma12', img: 'fare.png', dogru: 'Fare', secenekler: [{ metin: 'Köpek' }, { metin: 'Fare' }, { metin: 'Zürafa' }, { metin: 'Kuş' }] },
    { id: 'ma13', img: 'kopek.png', dogru: 'Köpek', secenekler: [{ metin: 'Fare' }, { metin: 'Köpek' }, { metin: 'Aslan' }, { metin: 'Zebra' }] },
    { id: 'ma14', img: 'su.png', dogru: 'Su', secenekler: [{ metin: 'Ateş' }, { metin: 'Su' }, { metin: 'Limon' }, { metin: 'Buz' }] },
    { id: 'ma15', img: 'bicak.png', dogru: 'Bıçak', secenekler: [{ metin: 'Taş' }, { metin: 'Bıçak' }, { metin: 'Pamuk' }, { metin: 'Limon' }] },
    { id: 'ma16', img: 'seker.png', dogru: 'Şeker', secenekler: [{ metin: 'Limon' }, { metin: 'Şeker' }, { metin: 'Pamuk' }, { metin: 'Buz' }] },
    { id: 'ma17', img: 'kar.png', dogru: 'Kar', secenekler: [{ metin: 'Su' }, { metin: 'Kar' }, { metin: 'Güneş' }, { metin: 'Ay' }] },
    { id: 'ma18', img: 'zebra.png', dogru: 'Zebra', secenekler: [{ metin: 'Aslan' }, { metin: 'Zebra' }, { metin: 'Maymun' }, { metin: 'Fil' }] },
    { id: 'ma19', img: 'maymun.png', dogru: 'Maymun', secenekler: [{ metin: 'Kuş' }, { metin: 'Maymun' }, { metin: 'Fare' }, { metin: 'Aslan' }] },
    { id: 'ma20', img: 'fil.png', dogru: 'Fil', secenekler: [{ metin: 'Fare' }, { metin: 'Fil' }, { metin: 'Zürafa' }, { metin: 'Zebra' }] }
];

const ALISTIRMA_SORULARI_GORSEL_V2 = [
    { id: 'na1', ad: 'Bebek', ifade: 'Olumlu?', img: 'bebek.png', cevap: 'Evet' },
    { id: 'na2', ad: 'Gülümseme', ifade: 'Neşeli?', img: 'gulumseme.png', cevap: 'Evet' },
    { id: 'na3', ad: 'Yardım', ifade: 'Kötü mü?', img: 'yardim.png', cevap: 'Hayır' },
    { id: 'na4', ad: 'Hediye', ifade: 'Sevindirir?', img: 'hediye.png', cevap: 'Evet' },
    { id: 'na5', ad: 'Kalp', ifade: 'Tehlikeli?', img: 'kalp.png', cevap: 'Hayır' },
    { id: 'na6', ad: 'Çiçek', ifade: 'Olumlu?', img: 'cicek.png', cevap: 'Evet' },
    { id: 'na7', ad: 'Güneş', ifade: 'Soğuk mu?', img: 'gunes.png', cevap: 'Hayır' },
    { id: 'na8', ad: 'Su', ifade: 'Sağlıklı', img: 'su.png', cevap: 'Evet' },
    { id: 'na9', ad: 'Köpek', ifade: 'Uçar mı?', img: 'kopek.png', cevap: 'Hayır' },
    { id: 'na10', ad: 'Kuş', ifade: 'Uçar?', img: 'kus.png', cevap: 'Evet' },
    { id: 'na11', ad: 'Cenaze', ifade: 'Eğlenceli?', img: 'cenaze.png', cevap: 'Hayır' },
    { id: 'na12', ad: 'Kaza', ifade: 'Tehlikeli?', img: 'kaza.png', cevap: 'Evet' },
    { id: 'na13', ad: 'İhanet', ifade: 'İyi mi?', img: 'ihanet.png', cevap: 'Hayır' },
    { id: 'na14', ad: 'Çöp', ifade: 'Kirli mi?', img: 'cop.png', cevap: 'Evet' },
    { id: 'na15', ad: 'Mikrop', ifade: 'Yararlı?', img: 'mikrop.png', cevap: 'Hayır' },
    { id: 'na16', ad: 'Yangin', ifade: 'Korkutucu?', img: 'yangin.png', cevap: 'Evet' },
    { id: 'na17', ad: 'Yara', ifade: 'Güzel mi?', img: 'yara.png', cevap: 'Hayır' },
    { id: 'na18', ad: 'Yılan', ifade: 'Tehlikeli?', img: 'yilan.png', cevap: 'Evet' },
    { id: 'na19', ad: 'Akrep', ifade: 'Evcil mi?', img: 'akrep.png', cevap: 'Hayır' },
    { id: 'na20', ad: 'Kurukafa', ifade: 'Ürkütücü?', img: 'kurukafa.png', cevap: 'Evet' }
];

const ALISTIRMA_SORULARI_MCRT_V2 = [
    { id: 'nm1', img: 'bebek.png', dogru: 'bebek', secenekler: [{ metin: 'bebek' }, { metin: 'cenaze' }, { metin: 'yara' }, { metin: 'çöp' }] },
    { id: 'nm2', img: 'gulumseme.png', dogru: 'gülümseme', secenekler: [{ metin: 'gülümseme' }, { metin: 'ihanet' }, { metin: 'kaza' }, { metin: 'mikrop' }] },
    { id: 'nm3', img: 'yardim.png', dogru: 'yardım', secenekler: [{ metin: 'yardım' }, { metin: 'ihanet' }, { metin: 'çöp' }, { metin: 'yılan' }] },
    { id: 'nm4', img: 'hediye.png', dogru: 'hediye', secenekler: [{ metin: 'hediye' }, { metin: 'cenaze' }, { metin: 'akrep' }, { metin: 'çöp' }] },
    { id: 'nm5', img: 'kalp.png', dogru: 'kalp', secenekler: [{ metin: 'kalp' }, { metin: 'kaza' }, { metin: 'akrep' }, { metin: 'yara' }] },
    { id: 'nm6', img: 'cicek.png', dogru: 'çiçek', secenekler: [{ metin: 'çiçek' }, { metin: 'çöp' }, { metin: 'mikrop' }, { metin: 'yara' }] },
    { id: 'nm7', img: 'gunes.png', dogru: 'güneş', secenekler: [{ metin: 'güneş' }, { metin: 'yangın' }, { metin: 'cenaze' }, { metin: 'çöp' }] },
    { id: 'nm8', img: 'su.png', dogru: 'su', secenekler: [{ metin: 'su' }, { metin: 'çöp' }, { metin: 'yara' }, { metin: 'mikrop' }] },
    { id: 'nm9', img: 'kopek.png', dogru: 'köpek', secenekler: [{ metin: 'köpek' }, { metin: 'yılan' }, { metin: 'akrep' }, { metin: 'cenaze' }] },
    { id: 'nm10', img: 'kus.png', dogru: 'kuş', secenekler: [{ metin: 'kuş' }, { metin: 'akrep' }, { metin: 'yılan' }, { metin: 'çöp' }] },
    { id: 'nm11', img: 'cenaze.png', dogru: 'cenaze', secenekler: [{ metin: 'bebek' }, { metin: 'cenaze' }, { metin: 'hediye' }, { metin: 'gülümseme' }] },
    { id: 'nm12', img: 'kaza.png', dogru: 'kaza', secenekler: [{ metin: 'kaza' }, { metin: 'kalp' }, { metin: 'çiçek' }, { metin: 'su' }] },
    { id: 'nm13', img: 'ihanet.png', dogru: 'ihanet', secenekler: [{ metin: 'ihanet' }, { metin: 'yardım' }, { metin: 'hediye' }, { metin: 'kalp' }] },
    { id: 'nm14', img: 'cop.png', dogru: 'çöp', secenekler: [{ metin: 'çöp' }, { metin: 'su' }, { metin: 'çiçek' }, { metin: 'bebek' }] },
    { id: 'nm15', img: 'mikrop.png', dogru: 'mikrop', secenekler: [{ metin: 'mikrop' }, { metin: 'su' }, { metin: 'hediye' }, { metin: 'kalp' }] },
    { id: 'nm16', img: 'yangin.png', dogru: 'yangın', secenekler: [{ metin: 'yangın' }, { metin: 'su' }, { metin: 'çiçek' }, { metin: 'gülümseme' }] },
    { id: 'nm17', img: 'yara.png', dogru: 'yara', secenekler: [{ metin: 'yara' }, { metin: 'hediye' }, { metin: 'kalp' }, { metin: 'çiçek' }] },
    { id: 'nm18', img: 'yilan.png', dogru: 'yılan', secenekler: [{ metin: 'yılan' }, { metin: 'köpek' }, { metin: 'kuş' }, { metin: 'bebek' }] },
    { id: 'nm19', img: 'akrep.png', dogru: 'akrep', secenekler: [{ metin: 'akrep' }, { metin: 'kalp' }, { metin: 'hediye' }, { metin: 'çiçek' }] },
    { id: 'nm20', img: 'kurukafa.png', dogru: 'kurukafa', secenekler: [{ metin: 'kurukafa' }, { metin: 'bebek' }, { metin: 'gülümseme' }, { metin: 'kalp' }] }
];

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

function mcrtKurguNormalizeEt(kurgu) {
    return (kurgu || 'marka_merkez').trim().toLowerCase().replace(/-/g, '_');
}

function aktifMcrtBlokGetir(soru) {
    return mcrtKurguNormalizeEt((soru && soru.mcrtBlok) || (typeof MCRT_KURGU !== 'undefined' ? MCRT_KURGU : 'marka_merkez'));
}

function aktifMcrtYerlesimGetir() {
    return (typeof MCRT_YERLESIM !== 'undefined' ? MCRT_YERLESIM : 'grid_standart').trim().toLowerCase();
}

function mcrtSecenekGruplariOlustur(liste, maxSecenek = 4) {
    const kaynak = Array.isArray(liste) ? [...liste] : [];
    if (kaynak.length <= maxSecenek) return [kaynak];

    const gruplar = [];
    for (let i = 0; i < kaynak.length; i += maxSecenek) {
        gruplar.push(kaynak.slice(i, i + maxSecenek));
    }

    return gruplar.filter(g => g.length > 0);
}

function turkceKucukMetin(metin) {
    return String(metin || '').toLocaleLowerCase('tr-TR');
}

function alistirmaDosyaAdiOlustur(metin) {
    return turkceKucukMetin(metin)
        .replace(/ş/g, 's')
        .replace(/ç/g, 'c')
        .replace(/ü/g, 'u')
        .replace(/ö/g, 'o')
        .replace(/ı/g, 'i')
        .replace(/ğ/g, 'g') + '.png';
}

function mcrtGercekSorulariOlustur(kurgu) {
    const gercekSorular = [];

    if (kurgu === 'ifade_merkez') {
        IFADELER.forEach(ifade => {
            const secenekler = MARKALAR.map(m => ({
                id: m.id,
                metin: m.ad,
                resim_dosya: m.resim_dosya
            }));
            const secenekGruplari = mcrtSecenekGruplariOlustur(secenekler, 4);

            secenekGruplari.forEach((grup, grupIndex) => {
                gercekSorular.push({
                    isAlistirma: false,
                    isMcrtAlistirma: false,
                    mcrtBlok: 'ifade_merkez',
                    markaId: null,
                    markaAd: "",
                    resimDosya: null,
                    ifadeId: ifade.id,
                    ifadeMetin: ifade.metin,
                    ifadeResim: ifade.resim_dosya,
                    mcrtTrialGrup: grupIndex + 1,
                    mcrtTrialToplam: secenekGruplari.length,
                    mcrtSecenekler: grup
                });
            });
        });
        return gercekSorular;
    }

    MARKALAR.forEach(marka => {
        const secenekler = IFADELER.map(i => ({
            id: i.id,
            metin: i.metin,
            resim_dosya: i.resim_dosya
        }));
        const secenekGruplari = mcrtSecenekGruplariOlustur(secenekler, 4);

        secenekGruplari.forEach((grup, grupIndex) => {
            gercekSorular.push({
                isAlistirma: false,
                isMcrtAlistirma: false,
                mcrtBlok: 'marka_merkez',
                markaId: marka.id,
                markaAd: marka.ad,
                resimDosya: marka.resim_dosya,
                ifadeId: null,
                ifadeMetin: "",
                ifadeResim: null,
                mcrtTrialGrup: grupIndex + 1,
                mcrtTrialToplam: secenekGruplari.length,
                mcrtSecenekler: grup
            });
        });
    });
    return gercekSorular;
}

function butonlariPrimingIcinGizle(container) {
    if (!container) return;
    container.style.transition = 'none';
    container.style.opacity = '0';
    container.style.pointerEvents = 'none';
    const eskiButonlar = container.querySelectorAll('button');
    eskiButonlar.forEach(btn => {
        btn.blur();
        btn.disabled = false;
        btn.classList.remove('btn-yanitlaniyor');
    });
    if (document.activeElement && typeof document.activeElement.blur === 'function') {
        document.activeElement.blur();
    }
    void container.offsetHeight;
}

function butonlariGoster(container) {
    if (!container) return;
    container.style.transition = 'opacity 0.16s ease-in';
    container.style.opacity = '1';
    container.style.pointerEvents = 'auto';
}

// Zeki Siralama (Akilli Dagitim / Interleaving)
function smartShuffle(soruListesi) {
    // 1. Marka gruplarini olustur
    const markaGruplari = {};
    soruListesi.forEach(s => {
        if (!markaGruplari[s.markaId]) markaGruplari[s.markaId] = [];
        markaGruplari[s.markaId].push(s);
    });

    // 2. Her markanin kendi icindeki ifadelerini rastgele karistir
    const markaIdleri = Object.keys(markaGruplari);
    markaIdleri.forEach(id => {
        shuffleArray(markaGruplari[id]);
    });

    // 3. Marka sirasini katilimciya ozel karistir (Latin Square hissiyati)
    shuffleArray(markaIdleri);

    // 4. Sirayla her markadan bir soru cekerek listeyi or
    const yeniSiralama = [];
    let soruKaldi = true;
    while (soruKaldi) {
        soruKaldi = false;
        markaIdleri.forEach(id => {
            if (markaGruplari[id].length > 0) {
                yeniSiralama.push(markaGruplari[id].shift());
                soruKaldi = true;
            }
        });
    }

    // Orijinal listeyi temizle ve yeni siralamayi ekle
    soruListesi.length = 0;
    yeniSiralama.forEach(s => soruListesi.push(s));
}

// Soru listesini olustur
function sorulariOlustur() {
    sorular = [];
    const tTuru = (typeof TEST_TURU !== 'undefined') ? TEST_TURU.toLowerCase() : 'standart';
    const isMcrt = (tTuru === 'mcrt' || tTuru === 'mrt');

    // 1. Alistirma sorulari
    if (typeof ALISTIRMA_AKTIF !== 'undefined' && ALISTIRMA_AKTIF) {
        if (isMcrt) {
            // Akilli MCRT Baseline: Kurguya gore otomatik yer degistirir
            let kurgu = mcrtKurguNormalizeEt(typeof MCRT_KURGU !== 'undefined' ? MCRT_KURGU : 'marka_merkez');
            if (kurgu === 'cift_blok') kurgu = 'marka_merkez';

            ALISTIRMA_SORULARI_MCRT_V2.forEach(a => {
                // Eger kurgu "marka_merkez" ise RESIM ortada olmali
                if (kurgu === 'marka_merkez') {
                    // Resim Ortada, Kelime Butonlarda (Default)
                    sorular.push({
                        isAlistirma: true, isMcrtAlistirma: true,
                        resimDosya: `alistirma/${a.img}`, ifadeMetin: "", dogruCevap: a.dogru,
                        mcrtSecenekler: a.secenekler.map(s => ({ metin: s.metin }))
                    });
                } else {
                    // Kelime Ortada, Resim Butonlarda
                    sorular.push({
                        isAlistirma: true, isMcrtAlistirma: true,
                        resimDosya: null, ifadeMetin: turkceKucukMetin(a.dogru), dogruCevap: a.dogru,
                        mcrtSecenekler: a.secenekler.map(s => ({ metin: s.metin, resim: alistirmaDosyaAdiOlustur(s.metin) }))
                    });
                }
            });
        } else {
            const isAudioTest = (typeof TEST_TURU !== 'undefined' && TEST_TURU === 'ses');
            const aktifListe = isAudioTest ? ALISTIRMA_SORULARI_SES : ALISTIRMA_SORULARI_GORSEL_V2;
            for (const a of aktifListe) {
                const path = isAudioTest ? `../sound_baseline/${a.img}` : `alistirma/${a.img}`;
                sorular.push({
                    isAlistirma: true,
                    markaId: 0,
                    markaAd: a.ad,
                    resimDosya: path,
                    ifadeId: 0,
                    ifadeMetin: a.ifade,
                    dogruCevap: a.cevap
                });
            }
        }
    }

    // 2. Gercek anket sorulari
    const gercekSorular = [];
    if (isMcrt && typeof MARKALAR !== 'undefined' && typeof IFADELER !== 'undefined') {
        const kurgu = mcrtKurguNormalizeEt(typeof MCRT_KURGU !== 'undefined' ? MCRT_KURGU : 'marka_merkez');

        if (kurgu === 'cift_blok') {
            const markaMerkezSorular = mcrtGercekSorulariOlustur('marka_merkez');
            const ifadeMerkezSorular = mcrtGercekSorulariOlustur('ifade_merkez');
            gercekSorular.push(...markaMerkezSorular, ...ifadeMerkezSorular);
        } else {
            gercekSorular.push(...mcrtGercekSorulariOlustur(kurgu));
        }
    } else if (isMcrt && MARKALAR.length === 0 && IFADELER.length > 0) {
        // Sadece ifadeler üzerinden MCRT
        IFADELER.forEach(i => {
            gercekSorular.push({
                markaId: null, markaAd: "", markaResim: null,
                ifadeId: i.id, ifadeMetin: i.metin, ifadeResim: i.resim_dosya,
                isAlistirma: false
            });
        });
    } else if (typeof MARKALAR !== 'undefined' && typeof IFADELER !== 'undefined') {
        let seciliMarkalar = MARKALAR;
        if (typeof TEST_TURU !== 'undefined' && TEST_TURU === 'monadik' && MARKALAR.length > 0) {
            const rMarka = MARKALAR[Math.floor(Math.random() * MARKALAR.length)];
            seciliMarkalar = [rMarka];
        }

        let aktifIfadeler = IFADELER;
        // MCRT'de eger ifadeler bossa, secenekleri ifade olarak kullan (Cunku admin panelinde ifadeler kapali olabilir)
        if (isMcrt && IFADELER.length === 0 && (typeof MCRT_SECENEKLER !== 'undefined' && MCRT_SECENEKLER.length > 0)) {
            aktifIfadeler = MCRT_SECENEKLER.map(s => ({ id: s.id, metin: s.metin, resim_dosya: s.resim_dosya }));
        }

        for (const marka of seciliMarkalar) {
            for (const ifade of aktifIfadeler) {
                gercekSorular.push({
                    isAlistirma: false,
                    isMcrtAlistirma: false,
                    markaId: marka.id,
                    markaAd: marka.ad,
                    resimDosya: marka.resim_dosya,
                    ifadeId: ifade.id,
                    ifadeMetin: ifade.metin,
                    ifadeResim: ifade.resim_dosya,
                    mcrtSecenekler: (typeof MCRT_SECENEKLER !== 'undefined') ? MCRT_SECENEKLER : []
                });
            }
        }
    }

    // Rastgele Karistir (Eger aciksa)
    if (typeof SORU_RANDOMIZE !== 'undefined' && SORU_RANDOMIZE) {
        try {
            const kurgu = mcrtKurguNormalizeEt(typeof MCRT_KURGU !== 'undefined' ? MCRT_KURGU : 'marka_merkez');
            if (isMcrt && kurgu === 'cift_blok') {
                const markaBlok = gercekSorular.filter(s => s.mcrtBlok === 'marka_merkez');
                const ifadeBlok = gercekSorular.filter(s => s.mcrtBlok === 'ifade_merkez');
                smartShuffle(markaBlok);
                smartShuffle(ifadeBlok);
                gercekSorular.length = 0;
                gercekSorular.push(...markaBlok, ...ifadeBlok);
            } else {
                smartShuffle(gercekSorular);
            }
        } catch (e) {
            console.error("Zeki sıralama hatası, basit karıştırmaya geçiliyor:", e);
            shuffleArray(gercekSorular);
        }
    }

    if (gercekSorular.length > 0) {
        sorular = sorular.concat(gercekSorular);
        // Resimleri onceden yukle (Prefetch)
        gorselleriOnYukle(sorular);
    } else {
        console.warn("DİKKAT: Hiç gerçek anket sorusu oluşturulamadı! MARKALAR ve IFADELER listelerini kontrol edin.");
    }
}

// Resim On-Yukleme (Prefetching)
function gorselleriOnYukle(liste = []) {
    if (!liste || !Array.isArray(liste)) return;
    const yuklenecekler = new Set();
    liste.forEach(s => {
        if (s.resimDosya) yuklenecekler.add(s.isAlistirma ? `/static/img/${s.resimDosya}` : `/static/uploads/${s.resimDosya}`);
        if (s.ifadeResim) yuklenecekler.add(`/static/uploads/${s.ifadeResim}`);
        if (s.mcrtSecenekler) {
            s.mcrtSecenekler.forEach(sec => {
                if (sec.resim) yuklenecekler.add(`/static/img/alistirma/${sec.resim}`);
                if (sec.resim_dosya) yuklenecekler.add(`/static/uploads/${sec.resim_dosya}`);
            });
        }
    });

    yuklenecekler.forEach(url => {
        const img = new Image();
        img.src = url;
    });
}

// Ekran gecisi
function ekranGoster(hedefId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const hedef = document.getElementById(hedefId);
    if (hedef) hedef.classList.add('active');
}

function sayfayiYenile() {
    window.location.reload();
}

function standartCevapButonlariniBagla() {
    const btnEvet = document.getElementById('btnEvet');
    const btnHayir = document.getElementById('btnHayir');

    if (btnEvet) {
        btnEvet.onclick = () => cevapVer('Evet');
    }
    if (btnHayir) {
        btnHayir.onclick = () => cevapVer('Hayir');
    }
}

function statikButonlariBagla() {
    const bagla = (id, handler) => {
        const el = document.getElementById(id);
        if (el) {
            el.onclick = handler;
        }
    };

    bagla('btnBasla', () => ekranGoster('screenProfil'));
    bagla('btnProfilKaydet', () => profilKaydetVeBasla());
    bagla('btnProjeyiBasla', (e) => testeGercektenBasla(e.currentTarget));
    bagla('btnAnaArastirmaBasla', () => anaAnketeBasla());
    bagla('btnKonumTekrarDene', () => sayfayiYenile());
    bagla('btnZayifDevamEt', () => ekranGoster('screenKarsilama'));
    bagla('btnZayifYenile', () => sayfayiYenile());
    bagla('btnCookieAccept', () => acceptCookies());

    standartCevapButonlariniBagla();
}

// Profil kaydet ve teste basla
function profilKaydetVeBasla() {
    const adSoyad = document.getElementById('profAdSoyad').value.trim();
    const yas = document.getElementById('profYas').value.trim();
    const cinsiyet = document.getElementById('profCinsiyet').value;
    const egitimVal = parseInt(document.getElementById('profEgitim').value);
    const meslekVal = parseInt(document.getElementById('profMeslek').value);

    // TUAD 2025 Yeni Parametreler
    const evVal = parseInt(document.getElementById('profEv').value) || 0;
    const arabaVal = parseInt(document.getElementById('profAraba').value) || 0;
    const saglikVal = parseInt(document.getElementById('profSaglik').value) || 0;

    const il = document.getElementById('profIl').value;
    const ilce = document.getElementById('profIlce').value;

    if (!adSoyad || !yas || !cinsiyet || !egitimVal || !meslekVal || !evVal || document.getElementById('profAraba').value === "" || !saglikVal || !il || !ilce) {
        alert("Lütfen tüm profil alanlarını doldurun.");
        return;
    }

    // TUAD 2025 Kompozit Skor Hesaplama
    // Temel Puan: Eğitim (1-6) + Meslek (1-6)
    let toplamSkor = egitimVal + meslekVal;

    // Varlık Bonusları
    if (evVal === 2) toplamSkor += 1; // Ev sahibi
    if (arabaVal === 3) toplamSkor += 2; // Yeni araba
    else if (arabaVal === 2) toplamSkor += 1; // Orta yaş araba
    else if (arabaVal === 0) toplamSkor -= 1; // Araba yok (negatif etki)

    if (saglikVal === 2) toplamSkor += 1; // Özel sağlık

    // SES Grubu Belirleme (TUAD 2025 Eşikleri)
    let sesGrubu = "E";
    if (toplamSkor >= 14) sesGrubu = "A";
    else if (toplamSkor >= 11) sesGrubu = "B";
    else if (toplamSkor >= 8) sesGrubu = "C1";
    else if (toplamSkor >= 6) sesGrubu = "C2";
    else if (toplamSkor >= 4) sesGrubu = "D";

    // Text degerlerini de alalim
    const egitimText = document.getElementById('profEgitim').options[document.getElementById('profEgitim').selectedIndex].text;
    const meslekText = document.getElementById('profMeslek').options[document.getElementById('profMeslek').selectedIndex].text;
    const evText = document.getElementById('profEv').options[document.getElementById('profEv').selectedIndex].text;
    const arabaText = document.getElementById('profAraba').options[document.getElementById('profAraba').selectedIndex].text;
    const saglikText = document.getElementById('profSaglik').options[document.getElementById('profSaglik').selectedIndex].text;

    // Cihaz ve PID
    const cihazTipi = /Mobi|Android/i.test(navigator.userAgent) ? 'Mobil' : 'Masaüstü';
    const panelPid = new URLSearchParams(window.location.search).get('pid') || '';

    profilVerisi = {
        ad_soyad: adSoyad,
        yas: parseInt(yas),
        cinsiyet: cinsiyet,
        meslek: meslekText,
        egitim: egitimText,
        ev_durumu: evText,
        araba_durumu: arabaText,
        saglik_durumu: saglikText,
        il: il,
        ilce: ilce,
        ses_grubu: sesGrubu,
        cihaz_tipi: cihazTipi,
        panel_pid: panelPid,
        tarayici_bilgisi: navigator.userAgent,
        baslangic_tarihi: new Date().toISOString(),
        bitis_tarihi: null,
        baglanti_hatasi: false
    };

    baslangicZamani = new Date();
    ekranGoster('screenHazirlik');
}

function testeGercektenBasla(btnRef) {
    anketBasla(btnRef);
}

async function anketBasla(clickedBtn) {
    const btn = clickedBtn || document.getElementById('btnBasla');
    const originalText = btn ? btn.innerHTML : '<span>Teste Başla</span>';
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span>Hazırlanıyor...</span>';
    }

    // 1. Görseller zaten sayfa açılışında arka planda yükleniyor
    // Yine de garantiye almak için bekle (zaten cachelenmişse anlık biter)
    if (typeof sorular !== 'undefined' && sorular.length > 0) {
        await gorselleriOnYukle(sorular);
    }

    // 2. Konum Bilgisi Al (Yüksek Hassasiyet)
    let gpsData = { enlem: null, boylam: null, hassasiyet: null };
    if ("geolocation" in navigator) {
        try {
            const pos = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                });
            });
            gpsData.enlem = pos.coords.latitude;
            gpsData.boylam = pos.coords.longitude;
            gpsData.hassasiyet = pos.coords.accuracy;
            console.log(`Konum Alındı: ${gpsData.enlem}, ${gpsData.boylam} (+/- ${gpsData.hassasiyet}m)`);
        } catch (e) {
            console.warn("Konum alınamadı veya izin verilmedi:", e.message);
        }
    }

    // 3. Oturumu Veritabanında Başlat (Linki burada "yakıyoruz")
    try {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfVal = csrfMeta ? csrfMeta.getAttribute('content') : '';
        await fetch('/api/oturum_baslat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfVal
            },
            body: JSON.stringify({
                proje_id: typeof PROJE_ID !== 'undefined' ? PROJE_ID : null,
                oturum_id: oturumId,
                profil_verisi: profilVerisi,
                token: typeof KATILIMCI_TOKEN !== 'undefined' ? KATILIMCI_TOKEN : '',
                enlem: gpsData.enlem,
                boylam: gpsData.boylam,
                konum_hassasiyet: gpsData.hassasiyet
            })
        });
    } catch (e) {
        console.error("Oturum başlatılamadı:", e);
    }

    if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }

    ekranGoster('screenSoru');
    setTimeout(() => soruGoster(0), 300);
}

// Soru goster
function soruGoster(index) {
    const renderToken = ++soruRenderToken;

    if (index >= sorular.length) {
        // Otomatik gönderim baslat
        tumCevaplariGonder();
        return;
    }

    const soru = sorular[index];

    // Alistirma bittiyse ve gercek teste geciliyorsa araya gecis ekrani koy
    if (!alistirmaBitti && !soru.isAlistirma && index > 0) {
        alistirmaBitti = true;
        mevcutSoruIndex = index;
        baselineHesapla();
        ekranGoster('screenGecis');
        return;
    }

    mevcutSoruIndex = index;
    const kart = document.getElementById('soruKart');
    const screenSoru = document.getElementById('screenSoru');

    if (soru.isAlistirma) {
        screenSoru.classList.add('is-alistirma');
    } else {
        screenSoru.classList.remove('is-alistirma');
    }

    if (kart) {
        kart.style.opacity = '';
        kart.style.transition = '';
        kart.classList.remove('gorunur');
        kart.classList.add('gizleniyor');
    }

    // Butonları ve konteynırı hazırla
    const butonlarContainer = document.querySelector('.soru-butonlar');
    if (butonlarContainer) {
        butonlarContainer.id = 'soruButonlar';
        butonlariPrimingIcinGizle(butonlarContainer);

        // MCRT Mantığı: Eğer MCRT alıştırması veya MCRT gerçek sorusuysa
        const isMcrt = (typeof TEST_TURU !== 'undefined' && (TEST_TURU.toLowerCase() === 'mcrt' || TEST_TURU.toLowerCase() === 'mrt'));
        if (soru.isMcrtAlistirma || (!soru.isAlistirma && isMcrt)) {
            butonlarContainer.innerHTML = '';
            butonlarContainer.classList.add('mcrt-grid');
            butonlarContainer.classList.remove('mcrt-freeform');

            const yerlesim = aktifMcrtYerlesimGetir();
            if (!soru.isAlistirma && yerlesim === 'serbest_denemsel') {
                butonlarContainer.classList.remove('mcrt-grid');
                butonlarContainer.classList.add('mcrt-freeform');
            }

            const hamSecenekler = Array.isArray(soru.mcrtSecenekler) && soru.mcrtSecenekler.length > 0
                ? soru.mcrtSecenekler
                : MCRT_SECENEKLER;
            const karisikSecenekler = shuffleArray([...hamSecenekler]);
            const kurgu = aktifMcrtBlokGetir(soru);

            karisikSecenekler.forEach(secenek => {
                const btn = document.createElement('button');
                btn.className = 'btn-cevap btn-mcrt';
                btn.type = 'button';
                btn.autocomplete = 'off';

                let btnIcerik = '';
                const rPath = soru.isMcrtAlistirma ? `/static/img/alistirma/${secenek.resim}` : `/static/uploads/${secenek.resim_dosya}`;
                const hasImage = Boolean(secenek.resim || secenek.resim_dosya);
                const gorunenMetin = kurgu === 'marka_merkez' ? turkceKucukMetin(secenek.metin) : secenek.metin;
                if (hasImage) {
                    btnIcerik += `<img src="${rPath}" style="object-fit:contain; pointer-events:none;">`;
                }
                if (hasImage && kurgu !== 'marka_merkez') {
                    btn.classList.add('mcrt-image-only');
                    btn.setAttribute('aria-label', gorunenMetin);
                    btn.setAttribute('title', gorunenMetin);
                }
                btnIcerik += `<span>${gorunenMetin}</span>`;

                btn.innerHTML = btnIcerik;
                btn.onmouseenter = () => {};
                btn.onmouseup = () => btn.blur();
                btn.ontouchend = () => setTimeout(() => btn.blur(), 0);
                btn.onclick = () => cevapVer(secenek.metin, secenek.id || 0, btn);
                butonlarContainer.appendChild(btn);
            });
        } else {
            // Standart Evet/Hayır (Standart Alıştırma veya Standart IRT Testi)
            butonlarContainer.classList.remove('mcrt-grid');
            butonlarContainer.innerHTML = `
                <button class="btn-cevap btn-cevap-evet" id="btnEvet"><span>EVET</span></button>
                <button class="btn-cevap btn-cevap-hayir" id="btnHayir"><span>HAYIR</span></button>
            `;
            standartCevapButonlariniBagla();
        }
        butonlariPrimingIcinGizle(butonlarContainer);
    }

    setTimeout(() => {
        if (renderToken !== soruRenderToken) return;

        const logo = document.getElementById('soruLogo');
        const markaEl = document.getElementById('soruMarkaAd');
        const audioEl = document.getElementById('soruAudio');
        const ifadeGorselContainer = document.getElementById('soruIfadeGorselContainer');
        const ifadeGorsel = document.getElementById('soruIfadeGorsel');
        const isAudio = soru.resimDosya && soru.resimDosya.match(/\.(mp3|wav|ogg|m4a)$/i);

        // Yeni soru yuklenmeden once eski gorsel izlerini tamamen temizle
        if (logo) {
            logo.style.visibility = 'hidden';
            logo.removeAttribute('src');
        }
        if (audioEl) {
            try { audioEl.pause(); } catch (_) {}
            audioEl.removeAttribute('src');
            audioEl.load?.();
        }
        if (ifadeGorsel) {
            ifadeGorsel.style.visibility = 'hidden';
            ifadeGorsel.removeAttribute('src');
        }
        if (ifadeGorselContainer) {
            ifadeGorselContainer.style.display = 'none';
        }

        // Görsellerin (varsa) yüklendiğinden emin ol ve göster
        const showQuestion = () => {
            if (renderToken !== soruRenderToken) return;

            if (kart) {
                kart.style.opacity = '';
                kart.style.transition = '';
                kart.classList.remove('gizleniyor');
                kart.classList.add('gorunur');
            }

            if (isAudio) {
                // Ses bittiğinde kronometreyi başlat ve butonları göster
                audioEl.onended = () => {
                    if (renderToken !== soruRenderToken) return;

                    const btns = document.getElementById('soruButonlar');
                    butonlariGoster(btns);
                    soruBaslangicZaman = performance.now();
                };
                audioEl.play().catch(e => console.log('Audio Autoplay Engellendi: ', e));
            } else {
                // Normal görsel priming (600ms sonra butonlar)
                setTimeout(() => {
                    if (renderToken !== soruRenderToken) return;

                    const btns = document.getElementById('soruButonlar');
                    butonlariGoster(btns);
                    soruBaslangicZaman = performance.now();
                }, 600);
            }
        };

        if (soru.resimDosya) {
            const path = soru.isAlistirma ? `/static/img/${soru.resimDosya}` : `/static/uploads/${soru.resimDosya}`;
            if (isAudio) {
                audioEl.src = path;
                logo.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><rect width="120" height="120" rx="8" fill="%23f8fafc"/><text x="60" y="75" text-anchor="middle" fill="%23cbd5e1" font-size="40">🔊</text></svg>`;
                logo.style.visibility = 'visible';
            } else {
                logo.onload = () => { logo.style.visibility = 'visible'; };
                logo.src = path;
            }
            logo.style.display = 'block';
            if (markaEl) markaEl.style.display = 'block';
        } else if (soru.markaAd) {
            const ch = soru.markaAd.charAt(0);
            logo.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><rect width="120" height="120" rx="8" fill="%23e2e8f0"/><text x="60" y="75" text-anchor="middle" fill="%23475569" font-size="50" font-family="Poppins" font-weight="700">${ch}</text></svg>`;
    logo.style.visibility = 'visible';
    logo.style.display = 'block';
    if (markaEl) markaEl.style.display = 'block';
} else {
    // MCRT Alistirma gibi logo ve marka adi gerekmeyen durumlar
    logo.src = '';
    logo.style.display = 'none';
    if (markaEl) {
        markaEl.textContent = '';
        markaEl.style.display = 'none';
    }
}

// İfade Görseli Kontrolü
if (soru.ifadeResim) {
    ifadeGorsel.onload = () => { ifadeGorsel.style.visibility = 'visible'; };
    ifadeGorsel.src = `/static/uploads/${soru.ifadeResim}`;
    ifadeGorselContainer.style.display = 'inline-flex';
} else {
    ifadeGorselContainer.style.display = 'none';
}

if (markaEl && markaEl.style.display !== 'none') markaEl.textContent = soru.markaAd || "";
const ifadeEl = document.getElementById('soruIfade');
const isMcrt = (typeof TEST_TURU !== 'undefined' && (TEST_TURU.toLowerCase() === 'mcrt' || TEST_TURU.toLowerCase() === 'mrt'));
// MCRT Marka-Merkezli kurguda ortada kelime gozukmemeli (Sadece logo olmali)
const kurgu = aktifMcrtBlokGetir(soru);
if (isMcrt && kurgu === 'marka_merkez' && !soru.isMcrtAlistirma) {
    ifadeEl.textContent = "";
} else {
    ifadeEl.textContent = (isMcrt && kurgu === 'ifade_merkez') ? turkceKucukMetin(soru.ifadeMetin || "") : (soru.ifadeMetin || "");
}

        // Görsellerin (varsa) yüklendiğinden emin ol ve göster
        // Not: gorselleriOnYukle sayesinde bunlar muhtemelen cache'tedir
        showQuestion();

        if (!soru.isAlistirma) {
            const gercekSorular = sorular.filter(s => !s.isAlistirma);
            const gercekIndex = index - sorular.filter(s => s.isAlistirma).length;
            const toplam = gercekSorular.length;
            const yuzde = Math.round((gercekIndex / toplam) * 100);
            const fillEl = document.getElementById('soruProgressFill');
            const textEl = document.getElementById('soruProgressText');
            if (fillEl) fillEl.style.width = `${yuzde}%`;
            if (textEl) textEl.textContent = `${gercekIndex + 1} / ${toplam}`;
        }
    }, 250);

// Sonraki görseli şimdiden arka planda yükle (prefetch)
const sonrakiIndex = index + 1;
if (sonrakiIndex < sorular.length) {
    const sonraki = sorular[sonrakiIndex];
    if (sonraki.resimDosya) {
        const path = sonraki.isAlistirma
            ? `/static/img/${sonraki.resimDosya}`
            : `/static/uploads/${sonraki.resimDosya}`;
        const prefetch = new Image();
        prefetch.src = path;
    }
}
}

// Cevap ver
function cevapVer(cevap, secenekId = null, tiklananBtn = null) {
    const bitisZaman = performance.now();
    soruRenderToken++;

    // Butonun odagini kaldir ve temizle
    if (tiklananBtn) {
        tiklananBtn.blur();
        tiklananBtn.classList.add('btn-yanitlaniyor');
    }
    if (document.activeElement) document.activeElement.blur();
    const btnCont = document.getElementById('soruButonlar');
    if (btnCont) {
        btnCont.style.pointerEvents = 'none'; // Cift tiklamayi engelle
        btnCont.style.transition = 'opacity 0.12s ease-out';
        btnCont.style.opacity = '0';
        btnCont.querySelectorAll('button').forEach(b => {
            if (b !== tiklananBtn) b.classList.remove('btn-yanitlaniyor');
            b.blur();
        });
    }

    // Alistirma kontrolu
    const sure_ms = Math.round(bitisZaman - soruBaslangicZaman);
    const soru = sorular[mevcutSoruIndex];
    const isMcrt = (typeof TEST_TURU !== 'undefined' && (TEST_TURU.toLowerCase() === 'mcrt' || TEST_TURU.toLowerCase() === 'mrt'));
    const kurgu = aktifMcrtBlokGetir(soru);
    const secilenMarkaId = isMcrt && !soru.isAlistirma && kurgu === 'ifade_merkez' ? secenekId : soru.markaId;
    const secilenSecenekId = isMcrt && !soru.isAlistirma && kurgu === 'ifade_merkez' ? null : secenekId;

    // Alistirma sorusuysa hata takibi yap
    let dogruCevapMi = null;
    if (soru.isAlistirma && soru.dogruCevap) {
        alistirmaToplam++;
        dogruCevapMi = (cevap === soru.dogruCevap);
        if (!dogruCevapMi) {
            alistirmaHataSayisi++;
        }
    }

    cevaplar.push({
        marka_id: soru.isAlistirma ? null : secilenMarkaId,
        ifade_id: soru.isAlistirma ? null : soru.ifadeId,
        secilen_secenek_id: secilenSecenekId,
        mcrt_blok: soru.isAlistirma ? 'alistirma' : kurgu,
        cevap: cevap,
        cevap_metin: cevap,
        sure_ms: sure_ms,
        is_alistirma: soru.isAlistirma || false,
        baseline_ms: baselineMs,
        oturum_id: oturumId,
        dogru_cevap_mi: dogruCevapMi
    });

    // Tum butonlari devre disi birak
    const btnContainer = document.querySelector('.soru-butonlar');
    if (btnContainer) {
        const btns = btnContainer.querySelectorAll('button');
        btns.forEach(b => b.disabled = true);
    }

    setTimeout(() => soruGoster(mevcutSoruIndex + 1), 280);
}

function medyanHesapla(degerler) {
    const sirali = [...degerler].sort((a, b) => a - b);
    const orta = Math.floor(sirali.length / 2);
    return sirali.length % 2 === 1
        ? Math.round(sirali[orta])
        : Math.round((sirali[orta - 1] + sirali[orta]) / 2);
}

// Baz hiz hesapla (Alistirma sorularinin ortalamasi)
function baselineHesapla() {
    const alistirmaCevaplari = cevaplar.filter(c => c.is_alistirma);
    const tumSureler = alistirmaCevaplari
        .map(c => Number(c.sure_ms))
        .filter(ms => Number.isFinite(ms) && ms > 0);

    if (tumSureler.length === 0) return;

    const tTuru = (typeof TEST_TURU !== 'undefined') ? TEST_TURU.toLowerCase() : 'standart';
    const isMcrt = (tTuru === 'mcrt' || tTuru === 'mrt');
    let hesapSureleri;

    if (isMcrt) {
        hesapSureleri = tumSureler.filter(ms => ms >= 250 && ms <= 8000);
        if (hesapSureleri.length === 0) hesapSureleri = tumSureler;
        baselineMs = medyanHesapla(hesapSureleri);
    } else {
        hesapSureleri = tumSureler.filter(ms => ms >= 300 && ms <= 3000);
        if (hesapSureleri.length === 0) hesapSureleri = tumSureler;
        const toplamSure = hesapSureleri.reduce((acc, curr) => acc + curr, 0);
        baselineMs = Math.round(toplamSure / hesapSureleri.length);
        console.log("Hesaplanan Baz Hız:", baselineMs, "ms");
    }

    console.log("Hesaplanan Baz Hiz:", baselineMs, "ms");
}

// Gecis ekranindan sonra ana anketi baslat
function anaAnketeBasla() {
    ekranGoster('screenSoru');
    // Tum gelecek cevaplara baz hizi ekle
    cevaplar.forEach(c => { if (!c.is_alistirma) c.baseline_ms = baselineMs; });
    setTimeout(() => soruGoster(mevcutSoruIndex), 300);
}

// Bağlantı kalitesini kontrol et (2G veya yavaş 3G ise uyar)
function baglantiKalitesiniKontrolEt() {
    if (navigator.connection) {
        const type = navigator.connection.effectiveType; // '4g', '3g', '2g', 'slow-2g'
        const downlink = navigator.connection.downlink; // Mb/s cinsinden hız

        // Çok zayıf bağlantı kriterleri
        if (type === '2g' || type === 'slow-2g' || (type === '3g' && downlink < 1.5)) {
            return false; // Zayıf bağlantı
        }
    }
    return true; // İyi veya bilinmeyen (riske girme, devam et)
}

// Konum Onayi ve Isleme
function konumOnayi(onay) {
    if (!onay) {
        ekranGoster('screenKonumReddedildi');
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                profilVerisi = {
                    enlem: pos.coords.latitude,
                    boylam: pos.coords.longitude
                };

                // Konumdan sonra bağlantı kalitesini de kontrol et
                if (!baglantiKalitesiniKontrolEt()) {
                    ekranGoster('screenZayifBaglanti');
                } else {
                    ekranGoster('screenKarsilama');
                }
            },
            (err) => {
                console.warn("Konum izni verildi ama alinmadi:", err);
                if (!baglantiKalitesiniKontrolEt()) {
                    ekranGoster('screenZayifBaglanti');
                } else {
                    ekranGoster('screenKarsilama');
                }
            },
            { timeout: 10000 }
        );
    } else {
        if (!baglantiKalitesiniKontrolEt()) {
            ekranGoster('screenZayifBaglanti');
        } else {
            ekranGoster('screenKarsilama');
        }
    }
}

// Cevaplari gonder
async function tumCevaplariGonder() {
    ekranGoster('screenGonder');
    const altBilgi = document.getElementById('gonderAltBilgi');

    // Zaman asimi kontrolu (AbortController)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 saniye siniri

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const response = await fetch('/api/cevap_kaydet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            signal: controller.signal, // Zaman asimi sinyali
            body: JSON.stringify({
                proje_id: typeof PROJE_ID !== 'undefined' ? PROJE_ID : null,
                proje_kod: typeof PROJE_KOD !== 'undefined' ? PROJE_KOD : '',
                token: typeof KATILIMCI_TOKEN !== 'undefined' ? KATILIMCI_TOKEN : '',
                cevaplar: cevaplar,
                oturum_id: oturumId,
                kalite_metrikleri: {
                    alistirma_hata_sayisi: alistirmaHataSayisi,
                    alistirma_toplam: alistirmaToplam,
                    alistirma_hata_orani: alistirmaToplam > 0 ? Math.round((alistirmaHataSayisi / alistirmaToplam) * 100) : 0,
                    baseline_ms: baselineMs,
                    baglanti: {
                        tip: navigator.connection ? navigator.connection.effectiveType : 'unknown',
                        hiz: navigator.connection ? navigator.connection.downlink : 0,
                        rtt: navigator.connection ? navigator.connection.rtt : 0
                    }
                }
            })
        });

        clearTimeout(timeoutId); // Basariliysa zaman asimini temizle

        const data = await response.json();

        if (response.ok && data.durum === 'basarili') {
            // Tamamlandi mühürünü vur (Geri dönüs engeli icin)
            if (typeof PROJE_ID !== 'undefined') {
                localStorage.setItem(`anket_bitti_${PROJE_ID}`, 'true');
            }

            if (typeof PANEL_COMPLETE !== 'undefined' && PANEL_COMPLETE.trim() !== '') {
                const pid = new URLSearchParams(window.location.search).get('pid') || '';
                const redirectUrl = PANEL_COMPLETE.replace('[PID]', pid);
                try {
                    const validatedUrl = new URL(redirectUrl);
                    if (validatedUrl.protocol === 'https:' || validatedUrl.protocol === 'http:') {
                        window.location.href = validatedUrl.href; // nosemgrep: js-open-redirect
                    }
                } catch (e) {
                    console.error('Geçersiz yönlendirme URL:', e);
                    ekranGoster('screenTesekkur');
                    konfetiOlustur();
                }
            } else {
                ekranGoster('screenTesekkur');
                konfetiOlustur();
            }
        } else {
            if (altBilgi) {
                altBilgi.innerHTML = `Bir hata oluştu: ${data.mesaj || 'Kaydedilemedi.'} <br><button onclick="tumCevaplariGonder()" style="margin-top:10px; padding:8px 20px; background:var(--primary); color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">Tekrar Dene</button>`;
                altBilgi.style.color = '#ef4444';
            }
        }
    } catch (error) {
        clearTimeout(timeoutId);
        if (altBilgi) {
            const errorMsg = error.name === 'AbortError' ? 'Bağlantı zaman aşımına uğradı (İnternet yavaş olabilir).' : 'Bağlantı hatası! Verileriniz kaydedilemedi.';
            altBilgi.innerHTML = `${errorMsg} <br><button onclick="tumCevaplariGonder()" style="margin-top:10px; padding:8px 20px; background:var(--primary); color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">Tekrar Dene</button>`;
            altBilgi.style.color = '#ef4444';
        }
    }
}

function konfetiOlustur() {
    const konfeti = document.getElementById('konfeti');
    if (!konfeti) return;
    const renkler = ['#6366f1', '#8b5cf6', '#10b981', '#ef4444', '#f59e0b', '#ec4899', '#06b6d4'];
    for (let i = 0; i < 60; i++) {
        const p = document.createElement('div');
        p.className = 'konfeti-parca';
        p.style.left = `${Math.random() * 100}%`;
        p.style.top = `${Math.random() * -20}%`;
        p.style.backgroundColor = renkler[Math.floor(Math.random() * renkler.length)];
        p.style.animationDelay = `${Math.random() * 2}s`;
        p.style.animationDuration = `${2 + Math.random() * 2}s`;
        p.style.width = `${6 + Math.random() * 8}px`;
        p.style.height = `${6 + Math.random() * 8}px`;
        p.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        konfeti.appendChild(p);
    }
}

async function ilceleriYukle() {
    try {
        const response = await fetch('/static/ilceler.json');
        ilceVerisi = await response.json();

        const ilSelect = document.getElementById('profIl');
        const ilceSelect = document.getElementById('profIlce');

        // Benzersiz illeri al ve sırala
        const iller = [...new Set(ilceVerisi.map(item => item.sehir_adi))].sort((a, b) => a.localeCompare(b, 'tr'));

        iller.forEach(il => {
            const option = document.createElement('option');
            option.value = il;
            option.textContent = il;
            ilSelect.appendChild(option);
        });

        ilSelect.addEventListener('change', function () {
            const seciliIl = this.value;
            ilceSelect.innerHTML = '<option value="">İlçe Seçiniz</option>';

            if (seciliIl) {
                const ilceler = ilceVerisi
                    .filter(item => item.sehir_adi === seciliIl)
                    .map(item => item.ilce_adi)
                    .sort((a, b) => a.localeCompare(b, 'tr'));

                ilceler.forEach(ilce => {
                    const option = document.createElement('option');
                    option.value = ilce;
                    option.textContent = ilce;
                    ilceSelect.appendChild(option);
                });
            }
        });
    } catch (error) {
        console.error("İl/İlçe verisi yüklenemedi:", error);
    }
}

function yasListesiYukle() {
    const yasSelect = document.getElementById('profYas');
    if (yasSelect) {
        for (let i = 12; i <= 70; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = i;
            yasSelect.appendChild(option);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    statikButonlariBagla();
    // Önce bitirme kontrolü yap
    if (typeof PROJE_ID !== 'undefined') {
        const tokenliGiris = (typeof KATILIMCI_TOKEN !== 'undefined' && KATILIMCI_TOKEN);
        if (!tokenliGiris && localStorage.getItem(`anket_bitti_${PROJE_ID}`)) {
            ekranGoster('screenZatenTamamlandi');
            return; // Testi baslatma
        }
    }

    sorulariOlustur();
    // Sayfa yuklenince gorselleri hemen arka planda yukle (Soru listesi olustuktan sonra)
    if (typeof sorular !== 'undefined' && sorular.length > 0) {
        gorselleriOnYukle(sorular);
    }
    ilceleriYukle();
    yasListesiYukle();
});

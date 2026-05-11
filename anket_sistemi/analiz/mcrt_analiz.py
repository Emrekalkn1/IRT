# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from itertools import combinations
from scipy.stats import wilcoxon

def mcrt_katilimci_kalite_analizi(df):
    """MCRT icin katilimci kalitesini secim paterni ve karar suresine gore degerlendirir."""
    if df.empty:
        return pd.DataFrame(), {
            "toplam_katilimci": 0,
            "elenen_katilimci": 0,
            "kalan_katilimci": 0,
            "detaylar": [],
            "kriterler": {
                "min_ms": 250,
                "max_ms": 8000,
                "hizli_oran_limiti": 0.30,
                "yavas_oran_limiti": 0.50,
                "tek_secenek_oran_limiti": 0.95
            }
        }

    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    gercek_df = df[df['is_alistirma'] == 0].copy() if 'is_alistirma' in df.columns else df.copy()

    kalite_raporu = {
        "toplam_katilimci": int(gercek_df['oturum_id'].nunique()) if 'oturum_id' in gercek_df.columns else 0,
        "elenen_katilimci": 0,
        "kalan_katilimci": 0,
        "detaylar": [],
        "kriterler": {
            "min_ms": 250,
            "max_ms": 8000,
            "hizli_oran_limiti": 0.30,
            "yavas_oran_limiti": 0.50,
            "tek_secenek_oran_limiti": 0.95
        }
    }

    if gercek_df.empty or 'oturum_id' not in gercek_df.columns:
        return gercek_df, kalite_raporu

    elenen_oturumlar = []
    for oturum_id in gercek_df['oturum_id'].dropna().unique():
        oturum_df = gercek_df[gercek_df['oturum_id'] == oturum_id]
        toplam = len(oturum_df)
        if toplam == 0:
            continue

        sorunlar = []
        hizli = len(oturum_df[oturum_df['sure_ms'] < 250]) if 'sure_ms' in oturum_df.columns else 0
        yavas = len(oturum_df[oturum_df['sure_ms'] > 8000]) if 'sure_ms' in oturum_df.columns else 0

        if hizli / toplam > 0.30:
            sorunlar.append(f"Cok hizli MCRT secimi: %{int(hizli / toplam * 100)}")
        if yavas / toplam > 0.50:
            sorunlar.append(f"Cok yavas MCRT secimi: %{int(yavas / toplam * 100)}")

        if 'cevap_metin' in oturum_df.columns:
            secim_dagilimi = oturum_df['cevap_metin'].value_counts(dropna=True)
            if len(secim_dagilimi) > 0 and secim_dagilimi.iloc[0] / toplam > 0.95 and toplam >= 4:
                sorunlar.append("Tek secenege kilitlenme")

        if sorunlar:
            elenen_oturumlar.append(oturum_id)
            kalite_raporu["detaylar"].append({"oturum_id": oturum_id, "durum": "ELENDI", "sorunlar": sorunlar})
        else:
            kalite_raporu["detaylar"].append({"oturum_id": oturum_id, "durum": "OK"})

    kalite_raporu["elenen_katilimci"] = len(elenen_oturumlar)
    kalite_raporu["kalan_katilimci"] = kalite_raporu["toplam_katilimci"] - kalite_raporu["elenen_katilimci"]

    temiz_df = gercek_df[~gercek_df['oturum_id'].isin(elenen_oturumlar)].copy()
    return temiz_df, kalite_raporu

def mcrt_temel_analiz(df, tum_secenekler=None, kurgu="marka_merkez"):
    """
    MCRT verilerini (market share, response time) analiz eder.
    """
    if df.empty:
        return pd.DataFrame(), {}

    df, kalite = mcrt_katilimci_kalite_analizi(df)
    
    if df.empty:
        return pd.DataFrame(), kalite

    kurgu = str(kurgu or "marka_merkez").strip().lower()

    # Marka-merkez: stimulus marka, secenek ifade
    # Ifade-merkez: stimulus ifade, secenek marka
    if kurgu == "ifade_merkez":
        df['stimulus'] = df['ifade']
    else:
        df['stimulus'] = df.apply(lambda x: x['marka'] if (x['marka'] and x['marka'] != 'None') else x['ifade'], axis=1)
    
    ozet = df.groupby(['stimulus', 'cevap_metin']).agg(
        toplam_secilme=('id', 'count'),
        ortalama_hiz=('sure_ms', 'mean'),
        medyan_hiz=('sure_ms', 'median')
    ).reset_index()

    # Her stimulus'un toplam secilme sayisini bul (Yuzde hesaplamak icin)
    stimulus_toplamlari = df.groupby('stimulus')['id'].count().to_dict()
    
    def yuzde_hesapla(row):
        toplam = stimulus_toplamlari.get(row['stimulus'], 1)
        return round((row['toplam_secilme'] / toplam) * 100, 1)

    ozet['secilme_orani'] = ozet.apply(yuzde_hesapla, axis=1)

    if tum_secenekler:
        stimuluslar = sorted(df['stimulus'].dropna().unique())
        tum_kombinasyonlar = pd.MultiIndex.from_product(
            [stimuluslar, tum_secenekler],
            names=['stimulus', 'cevap_metin']
        ).to_frame(index=False)
        ozet = tum_kombinasyonlar.merge(ozet, on=['stimulus', 'cevap_metin'], how='left')
        ozet['toplam_secilme'] = ozet['toplam_secilme'].fillna(0).astype(int)
        ozet['ortalama_hiz'] = ozet['ortalama_hiz'].fillna(0)
        ozet['medyan_hiz'] = ozet['medyan_hiz'].fillna(0)
        ozet['secilme_orani'] = ozet['secilme_orani'].fillna(0)

    if kurgu == "ifade_merkez":
        ozet['marka'] = ozet['cevap_metin']
        ozet['ifade'] = ozet['stimulus']
    else:
        ozet['marka'] = ozet['stimulus']
        ozet['ifade'] = ozet['cevap_metin']

    # Implicit Skor (MCRT Versiyonu): Hiz ve Orani birlestiren skor
    def mcrt_skor_hesapla(row):
        if row['toplam_secilme'] == 0:
            return 0
        # Hizli ve cok secilen daha yuksek puan alir.
        hiz_faktoru = 1000 / max(row['ortalama_hiz'], 300) 
        skor = row['secilme_orani'] * hiz_faktoru
        return round(min(skor, 100), 1)

    ozet['mcrt_skor'] = ozet.apply(mcrt_skor_hesapla, axis=1)
    ozet['implicit_skor'] = ozet['mcrt_skor'] # Grafik uyumu
    ozet['explicit_pct'] = ozet['secilme_orani'] # Grafik uyumu
    
    kalite["gecerli_katilimci"] = kalite.get("kalan_katilimci", 0)
    kalite["toplam_cevap"] = int(len(df))
    kalite["ortalama_hiz"] = float(round(df['sure_ms'].mean(), 1)) if not df.empty else 0

    return ozet, kalite


def mcrt_marka_karsilastirma_testi(ozet_df):
    """MCRT için marka bazlı ikili karşılaştırmalar üretir."""
    if ozet_df is None or ozet_df.empty or 'marka' not in ozet_df.columns or 'ifade' not in ozet_df.columns:
        return []

    df = ozet_df.copy()
    df['marka'] = df['marka'].astype(str)
    df['ifade'] = df['ifade'].astype(str)
    df['secilme_orani'] = pd.to_numeric(df.get('secilme_orani'), errors='coerce').fillna(0.0)
    df['mcrt_skor'] = pd.to_numeric(df.get('mcrt_skor'), errors='coerce').fillna(0.0)

    markalar = [m for m in sorted(df['marka'].dropna().unique()) if m and m != 'None']
    sonuclar = []

    def p_text(p):
        if p is None or (isinstance(p, float) and np.isnan(p)):
            return "1.000"
        return f"{float(p):.3f}"

    def anlamlilik(p):
        try:
            return "anlamlı" if float(p) < 0.05 else "ns"
        except Exception:
            return "ns"

    def etki_buyuklugu_label(d):
        ad = abs(float(d))
        if ad < 0.2:
            return "çok küçük"
        if ad < 0.5:
            return "küçük"
        if ad < 0.8:
            return "orta"
        return "büyük"

    def cohens_d_paired(diff_series):
        vals = np.asarray(diff_series, dtype=float)
        if len(vals) < 2:
            return 0.0
        std = np.std(vals, ddof=1)
        if std == 0 or np.isnan(std):
            return 0.0
        return float(np.mean(vals) / std)

    def guven_araligi(diff_series):
        vals = np.asarray(diff_series, dtype=float)
        if len(vals) < 2:
            ort = float(np.mean(vals)) if len(vals) else 0.0
            return f"{ort:.1f} .. {ort:.1f}"
        std = np.std(vals, ddof=1)
        se = std / np.sqrt(len(vals)) if len(vals) else 0
        ort = float(np.mean(vals))
        alt = ort - 1.96 * se
        ust = ort + 1.96 * se
        return f"{alt:.1f} .. {ust:.1f}"

    for marka_a, marka_b in combinations(markalar, 2):
        a_df = df[df['marka'] == marka_a][['ifade', 'secilme_orani', 'mcrt_skor']].copy()
        b_df = df[df['marka'] == marka_b][['ifade', 'secilme_orani', 'mcrt_skor']].copy()

        eslesen = a_df.merge(
            b_df,
            on='ifade',
            how='inner',
            suffixes=('_a', '_b')
        )
        if eslesen.empty:
            continue

        pay_diff = eslesen['secilme_orani_a'] - eslesen['secilme_orani_b']
        skor_diff = eslesen['mcrt_skor_a'] - eslesen['mcrt_skor_b']

        if len(eslesen) >= 2 and not np.allclose(pay_diff.to_numpy(dtype=float), 0):
            try:
                p_pay = float(
                    wilcoxon(
                        eslesen['secilme_orani_a'],
                        eslesen['secilme_orani_b'],
                        method='approx'
                    ).pvalue
                )
            except Exception:
                p_pay = 1.0
        else:
            p_pay = 1.0

        if len(eslesen) >= 2 and not np.allclose(skor_diff.to_numpy(dtype=float), 0):
            try:
                p_skor = float(
                    wilcoxon(
                        eslesen['mcrt_skor_a'],
                        eslesen['mcrt_skor_b'],
                        method='approx'
                    ).pvalue
                )
            except Exception:
                p_skor = 1.0
        else:
            p_skor = 1.0

        d_val = cohens_d_paired(skor_diff)
        pay_ort = float(pay_diff.mean()) if len(pay_diff) else 0.0
        skor_ort = float(skor_diff.mean()) if len(skor_diff) else 0.0

        if p_skor < 0.05 or p_pay < 0.05:
            lider = marka_a if skor_ort >= 0 else marka_b
            yorum = f"{lider} bu ifade setlerinde daha güçlü ayrışıyor."
        else:
            yorum = "İki marka arasında istatistiksel olarak net bir ayrışma yok."

        sonuclar.append({
            "marka_a": marka_a,
            "marka_b": marka_b,
            "explicit_fark": round(pay_ort, 1),
            "explicit_p": p_text(p_pay),
            "explicit_anlamlilik": anlamlilik(p_pay),
            "guven_araligi": guven_araligi(pay_diff),
            "implicit_p": p_text(p_skor),
            "implicit_anlamlilik": anlamlilik(p_skor),
            "cohens_d": round(d_val, 2),
            "etki_buyuklugu": etki_buyuklugu_label(d_val),
            "yorum": yorum
        })

    return sonuclar

# -*- coding: utf-8 -*-
"""
Analiz Modülü - Bilimsel Standartlar (MySQL Uyumlu)
"""
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime

def _json_scalar(value, default=0):
    if pd.isna(value):
        return default
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value

def katilimci_kalite_analizi(df):
    """Her katılımcının veri kalitesini değerlendirir."""
    if df.empty:
        return pd.DataFrame(), {"toplam_katilimci": 0, "elenen_katilimci": 0, "detaylar": []}

    # Sütun isimlerini küçük harfe sabitle
    df.columns = [c.lower() for c in df.columns]

    if 'oturum_id' not in df.columns:
        return df, {"error": "oturum_id eksik"}

    gercek_df = df[df['is_alistirma'] == 0].copy() if 'is_alistirma' in df.columns else df.copy()
    
    kalite_raporu = {
        'toplam_katilimci': int(df['oturum_id'].nunique()),
        'elenen_katilimci': 0,
        'kalan_katilimci': 0,
        'detaylar': []
    }
    
    elenen_oturumlar = []
    for oturum_id in gercek_df['oturum_id'].unique():
        oturum_df = gercek_df[gercek_df['oturum_id'] == oturum_id]
        toplam = len(oturum_df)
        if toplam == 0: continue
        
        sorunlar = []
        # Kriter 1: Çok hızlı cevap (>%30 trial <300ms) - Esnek
        if 'sure_ms' in oturum_df.columns:
            hizli = len(oturum_df[oturum_df['sure_ms'] < 300])
            if (hizli / toplam) > 0.3: sorunlar.append(f"Hızlı cevap: %{int(hizli/toplam*100)}")
        
        # Kriter 2: Yanıt yanlılığı (>%98 aynı cevap)
        if 'cevap' in oturum_df.columns:
            en_cok = oturum_df['cevap'].value_counts()
            if len(en_cok) > 0 and (en_cok.iloc[0] / toplam) > 0.98:
                sorunlar.append("Aynı yanıt yanlılığı")

        if sorunlar:
            elenen_oturumlar.append(oturum_id)
            kalite_raporu['detaylar'].append({'oturum_id': oturum_id, 'durum': 'ELENDI', 'sorunlar': sorunlar})
        else:
            kalite_raporu['detaylar'].append({'oturum_id': oturum_id, 'durum': 'OK'})

    kalite_raporu['elenen_katilimci'] = len(elenen_oturumlar)
    kalite_raporu['kalan_katilimci'] = kalite_raporu['toplam_katilimci'] - kalite_raporu['elenen_katilimci']
    
    temiz_df = df[~df['oturum_id'].isin(elenen_oturumlar)].copy()
    return temiz_df, kalite_raporu

def explicit_implicit_analiz(df, kalite_filtresi=True):
    """Ana analiz fonksiyonu."""
    if df.empty:
        return pd.DataFrame(), {"toplam_katilimci": 0}

    # Sütunları küçük harfe çek
    df.columns = [c.lower() for c in df.columns]

    kalite_raporu = {"toplam_katilimci": df['oturum_id'].nunique()}
    if kalite_filtresi:
        df, kalite_raporu = katilimci_kalite_analizi(df)

    if df.empty:
        return pd.DataFrame(), kalite_raporu

    # Noise markaları ele (is_noise=1 olanlar analiz dışı bırakılır)
    if 'is_noise' in df.columns:
        df = df[df['is_noise'] != 1].copy()

    # Gerçek veriler ve Outlier temizliği (300-3000ms)
    df = df[df['is_alistirma'] == 0].copy() if 'is_alistirma' in df.columns else df.copy()
    df = df[(df['sure_ms'] >= 300) & (df['sure_ms'] <= 3000)].copy()

    # Implicit Güç (D-score benzeri)
    if 'sure_ms' in df.columns:
        oturum_sd = df.groupby('oturum_id')['sure_ms'].transform('std').fillna(100).clip(lower=1)
        # Baseline yoksa 1000ms varsay
        df['guc_skor'] = df.apply(lambda x: (x.get('baseline_ms', 1000) or 1000) - x['sure_ms'], axis=1)
        df['guc_skor'] = df['guc_skor'] / oturum_sd
    else:
        df['guc_skor'] = 0

    sonuclar = []
    for (marka, ifade), grp in df.groupby(['marka', 'ifade']):
        evet_sayisi = len(grp[grp['cevap'] == 'Evet'])
        toplam = len(grp)
        
        explicit_pct = (evet_sayisi / toplam * 100) if toplam > 0 else 0
        implicit_guc = round(grp['guc_skor'].mean(), 3)
        implicit_skor = round(max(0, min(100, (implicit_guc * 25) + 50)), 1)
        
        evet_df = grp[grp['cevap'] == 'Evet']
        hayir_df = grp[grp['cevap'] == 'Hayır']
        evet_ms = evet_df['sure_ms'].mean() if not evet_df.empty else 0
        hayir_ms = hayir_df['sure_ms'].mean() if not hayir_df.empty else 0

        sonuclar.append({
            'marka': str(marka), 'ifade': str(ifade),
            'explicit_pct': round(explicit_pct, 1),
            'implicit_skor': implicit_skor,
            'implicit_guc': implicit_guc,
            'implicit_evet_ms': round(evet_ms, 1),
            'fark_ms': round(hayir_ms - evet_ms, 1),
            'n': toplam
        })

    sonuc_df = pd.DataFrame(sonuclar)
    if not sonuc_df.empty:
        sonuc_df = sonuc_df.sort_values(['marka', 'ifade']).reset_index(drop=True)

    return sonuc_df, kalite_raporu

def marka_karsilastirma_testi(df):
    """Markalar arası istatistiksel testler."""
    if df.empty: return []
    df.columns = [c.lower() for c in df.columns]
    df = df[df['is_alistirma'] == 0].copy() if 'is_alistirma' in df.columns else df.copy()
    
    markalar = df['marka'].unique()
    if len(markalar) < 2: return []
    
    sonuclar = []
    for i in range(len(markalar)):
        for j in range(i + 1, len(markalar)):
            m_a, m_b = markalar[i], markalar[j]
            df_a, df_b = df[df['marka'] == m_a], df[df['marka'] == m_b]
            
            if len(df_a) < 3 or len(df_b) < 3: continue

            # Explicit (Chi-square)
            evet_a, n_a = len(df_a[df_a['cevap'] == 'Evet']), len(df_a)
            evet_b, n_b = len(df_b[df_b['cevap'] == 'Evet']), len(df_b)
            try:
                _, p_exp, _, _ = stats.chi2_contingency([[evet_a, n_a-evet_a], [evet_b, n_b-evet_b]])
            except Exception: p_exp = 1.0

            # Implicit (T-test)
            try:
                _, p_imp = stats.ttest_ind(df_a['sure_ms'], df_b['sure_ms'], equal_var=False)
            except Exception: p_imp = 1.0

            def anlam(p): return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))

            sonuclar.append({
                "marka_a": m_a, "marka_b": m_b,
                "explicit_fark": round((evet_a/n_a - evet_b/n_b)*100, 1),
                "explicit_p": round(p_exp, 4), "explicit_anlamlilik": anlam(p_exp),
                "implicit_p": round(p_imp, 4), "implicit_anlamlilik": anlam(p_imp),
                "cohens_d": round((df_a['sure_ms'].mean() - df_b['sure_ms'].mean()) / np.std(df['sure_ms']), 2),
                "etki_buyuklugu": "orta", "explicit_ci_95": "N/A"
            })
    return sonuclar

def korelasyon_hesapla(sonuc_df):
    if sonuc_df is None or len(sonuc_df) < 3:
        return {"pearson": 0, "spearman": 0, "p_pearson": 1.0, "p_spearman": 1.0}
    try:
        r_p, p_p = stats.pearsonr(sonuc_df['explicit_pct'], sonuc_df['implicit_guc'])
        r_s, p_s = stats.spearmanr(sonuc_df['explicit_pct'], sonuc_df['implicit_guc'])
        return {"pearson": round(r_p, 3), "p_pearson": round(p_p, 4), "spearman": round(r_s, 3), "p_spearman": round(p_s, 4)}
    except Exception:
        return {"pearson": 0, "spearman": 0, "p_pearson": 1.0, "p_spearman": 1.0}

def marka_modern_geleneksel(sonuc_df):
    """Marka bazlı özet verileri oluşturur (Analiz raporu için)."""
    if sonuc_df.empty:
        return pd.DataFrame()
    
    # Marka bazında grupla ve ortalamaları al
    marka_ozet = sonuc_df.groupby('marka').agg({
        'explicit_pct': 'mean',
        'implicit_guc': 'mean',
        'implicit_skor': 'mean',
        'n': 'sum'
    }).reset_index()
    
    # Yuvarlamalar
    marka_ozet['explicit_pct'] = marka_ozet['explicit_pct'].round(1)
    marka_ozet['implicit_guc'] = marka_ozet['implicit_guc'].round(3)
    marka_ozet['implicit_skor'] = marka_ozet['implicit_skor'].round(1)
    
    return marka_ozet

def veri_kalite_ozeti(df, kalite_raporu):
    """Veri kalitesi hakkında yönetici özeti oluşturur."""
    toplam = int(_json_scalar(kalite_raporu.get('toplam_katilimci', 0)))
    elenen = int(_json_scalar(kalite_raporu.get('elenen_katilimci', 0)))
    kalan = int(_json_scalar(kalite_raporu.get('kalan_katilimci', toplam - elenen)))
    
    ozet = {
        "toplam_katilimci": toplam,
        "elenen_katilimci": elenen,
        "gecerli_katilimci": kalan,
        "gecerlilik_orani": float(round((kalan / toplam * 100), 1)) if toplam > 0 else 0,
        "ortalama_cevap_suresi": float(round(df['sure_ms'].mean(), 0)) if not df.empty and 'sure_ms' in df.columns else 0,
        "en_hizli_cevap": _json_scalar(df['sure_ms'].min()) if not df.empty and 'sure_ms' in df.columns else 0,
        "detaylar": kalite_raporu.get('detaylar', [])
    }
    return ozet

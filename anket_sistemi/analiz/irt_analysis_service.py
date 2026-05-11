# -*- coding: utf-8 -*-
import pandas as pd

from analiz.analiz import explicit_implicit_analiz, marka_karsilastirma_testi, korelasyon_hesapla


def kategori_ozeti_uret(ozet_df, ifade_df=None):
    if ozet_df is None or ozet_df.empty:
        return []

    if ifade_df is None or getattr(ifade_df, "empty", True):
        ifade_df = pd.DataFrame()
    ifade_kategori = {}
    if not ifade_df.empty and "metin" in ifade_df.columns:
        ifade_kategori = {
            str(row.get("metin") or ""): str(row.get("kategori") or "").strip()
            for _, row in ifade_df.iterrows()
        }

    df = ozet_df.copy()
    if "marka" not in df.columns or "ifade" not in df.columns:
        return []
    if "kategori" not in df.columns:
        df["kategori"] = df["ifade"].astype(str).map(ifade_kategori).fillna("")
    df["kategori"] = df["kategori"].astype(str).replace("", "Kategorisiz")

    explicit_kaynak = "explicit_pct" if "explicit_pct" in df.columns else ("secilme_orani" if "secilme_orani" in df.columns else None)
    implicit_kaynak = (
        "implicit_guc" if "implicit_guc" in df.columns
        else "implicit_skor" if "implicit_skor" in df.columns
        else "mcrt_skor" if "mcrt_skor" in df.columns
        else None
    )
    adet_kaynak = "n" if "n" in df.columns else ("toplam_secilme" if "toplam_secilme" in df.columns else None)

    agg_map = {}
    if explicit_kaynak:
        agg_map["explicit_pct"] = (explicit_kaynak, "mean")
    if implicit_kaynak:
        agg_map["implicit_skor"] = (implicit_kaynak, "mean")
    if adet_kaynak:
        agg_map["n"] = (adet_kaynak, "sum")
    else:
        agg_map["n"] = ("ifade", "count")

    grup = (
        df.groupby(["marka", "kategori"], dropna=False)
        .agg(**agg_map)
        .reset_index()
    )
    for col in ["explicit_pct", "implicit_skor"]:
        if col in grup.columns:
            grup[col] = grup[col].round(1)
    return grup.to_dict(orient="records")


def irt_proje_analizi(db, proje_id):
    df = db.proje_verileri_df(proje_id)
    if df is None or df.empty:
        return {
            "ozet": [],
            "kalite": {},
            "istatistik": [],
            "korelasyon": {},
            "kategori_ozet": [],
            "test_turu": "standart",
            "analiz_motoru": "IRT",
            "veri_kaynagi": "cevaplar"
        }

    ozet_df, kalite_raporu = explicit_implicit_analiz(df)
    ifade_df = pd.DataFrame(db.proje_ifadeleri(proje_id) or [])
    if not ozet_df.empty and not ifade_df.empty and "metin" in ifade_df.columns:
        kategori_map = {
            str(row.get("metin") or ""): str(row.get("kategori") or "").strip()
            for _, row in ifade_df.iterrows()
        }
        ozet_df["kategori"] = ozet_df["ifade"].astype(str).map(kategori_map).fillna("")
    testler = marka_karsilastirma_testi(df)

    return {
        "ozet": ozet_df.to_dict(orient="records") if not ozet_df.empty else [],
        "kalite": kalite_raporu,
        "istatistik": testler,
        "korelasyon": korelasyon_hesapla(ozet_df) if not ozet_df.empty else {},
        "kategori_ozet": kategori_ozeti_uret(ozet_df, ifade_df),
        "test_turu": "standart",
        "analiz_motoru": "IRT",
        "veri_kaynagi": "cevaplar"
    }

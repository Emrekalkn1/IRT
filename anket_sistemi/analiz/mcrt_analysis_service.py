# -*- coding: utf-8 -*-
import pandas as pd
import time

from analiz.mcrt_analiz import mcrt_temel_analiz, mcrt_marka_karsilastirma_testi
from analiz.irt_analysis_service import kategori_ozeti_uret


_MCRT_ISTATISTIK_CACHE = {}
_MCRT_ISTATISTIK_TTL_SN = 120


def mcrt_secenek_evreni(db, proje_id, proje=None, kurgu=None):
    proje = proje or db.proje_getir(proje_id) or {}
    kurgu = str(kurgu or proje.get("mcrt_kurgu") or "marka_merkez").strip().lower()

    if kurgu == "ifade_merkez":
        return [m["ad"] for m in db.proje_markalari(proje_id)]

    ifadeler = db.proje_ifadeleri(proje_id)
    if ifadeler:
        return [i["metin"] for i in ifadeler]

    return [s["metin"] for s in db.proje_mcrt_secenekleri(proje_id)]


def mcrt_blok_dfleri(df):
    marka_df = df[df["ifade_id"].isna()].copy() if "ifade_id" in df.columns else pd.DataFrame()
    ifade_df = df[df["ifade_id"].notna()].copy() if "ifade_id" in df.columns else pd.DataFrame()
    return marka_df, ifade_df


def mcrt_birlesik_ozet(marka_ozet, ifade_ozet):
    if marka_ozet.empty and ifade_ozet.empty:
        return pd.DataFrame()

    if marka_ozet.empty:
        marka_ozet = ifade_ozet[["marka", "ifade"]].copy()
        marka_ozet["toplam_secilme"] = 0
        marka_ozet["ortalama_hiz"] = 0
        marka_ozet["medyan_hiz"] = 0
        marka_ozet["secilme_orani"] = 0
        marka_ozet["mcrt_skor"] = 0

    if ifade_ozet.empty:
        ifade_ozet = marka_ozet[["marka", "ifade"]].copy()
        ifade_ozet["toplam_secilme"] = 0
        ifade_ozet["ortalama_hiz"] = 0
        ifade_ozet["medyan_hiz"] = 0
        ifade_ozet["secilme_orani"] = 0
        ifade_ozet["mcrt_skor"] = 0

    birlesik = pd.merge(
        marka_ozet,
        ifade_ozet,
        on=["marka", "ifade"],
        how="outer",
        suffixes=("_marka", "_ifade")
    ).fillna(0)

    if birlesik.empty:
        return birlesik

    birlesik["stimulus"] = birlesik["marka"] + " <-> " + birlesik["ifade"]
    birlesik["toplam_secilme"] = birlesik["toplam_secilme_marka"] + birlesik["toplam_secilme_ifade"]
    birlesik["secilme_orani"] = ((birlesik["secilme_orani_marka"] + birlesik["secilme_orani_ifade"]) / 2).round(1)
    birlesik["mcrt_skor"] = ((birlesik["mcrt_skor_marka"] + birlesik["mcrt_skor_ifade"]) / 2).round(1)
    birlesik["implicit_skor"] = birlesik["mcrt_skor"]
    birlesik["explicit_pct"] = birlesik["secilme_orani"]
    birlesik["ortalama_hiz"] = (
        (birlesik["ortalama_hiz_marka"] + birlesik["ortalama_hiz_ifade"]) / 2
    ).round(1)
    birlesik["medyan_hiz"] = (
        (birlesik["medyan_hiz_marka"] + birlesik["medyan_hiz_ifade"]) / 2
    ).round(1)
    birlesik["blok"] = "birlesik"
    return birlesik


def _mcrt_cache_key(proje_id, proje, df):
    son_tarih = ""
    if "tarih" in df.columns and not df.empty:
        try:
            son_tarih = str(df["tarih"].iloc[-1])
        except Exception:
            son_tarih = ""
    return (
        int(proje_id),
        str(proje.get("mcrt_kurgu") or "marka_merkez"),
        int(len(df)),
        son_tarih,
    )


def mcrt_proje_analizi(db, proje_id, include_stats=True):
    proje = db.proje_getir(proje_id) or {}
    df = db.proje_mcrt_verileri_df(proje_id)
    if df is None or df.empty:
        return {
            "ozet": [],
            "kalite": {},
            "istatistik": [],
            "korelasyon": {},
            "kategori_ozet": [],
            "test_turu": "mcrt",
            "analiz_motoru": "MCRT",
            "veri_kaynagi": "mcrt_cevaplar"
        }

    kalite_raporu = {}
    blok_analizleri = {}
    blok_kaliteleri = {}
    varsayilan_gorunum = "tek_blok"
    kurgu = str(proje.get("mcrt_kurgu") or "marka_merkez").strip().lower()

    if kurgu == "cift_blok":
        marka_df, ifade_df = mcrt_blok_dfleri(df)
        marka_ozet, kalite_raporu = mcrt_temel_analiz(
            marka_df,
            tum_secenekler=mcrt_secenek_evreni(db, proje_id, proje=proje, kurgu="marka_merkez"),
            kurgu="marka_merkez"
        )
        ifade_ozet, ifade_kalite = mcrt_temel_analiz(
            ifade_df,
            tum_secenekler=mcrt_secenek_evreni(db, proje_id, proje=proje, kurgu="ifade_merkez"),
            kurgu="ifade_merkez"
        )
        if not marka_ozet.empty:
            marka_ozet = marka_ozet.copy()
            marka_ozet["blok"] = "marka_merkez"
            blok_analizleri["marka_merkez"] = marka_ozet.to_dict(orient="records")
            blok_kaliteleri["marka_merkez"] = kalite_raporu or {}
        if not ifade_ozet.empty:
            ifade_ozet = ifade_ozet.copy()
            ifade_ozet["blok"] = "ifade_merkez"
            blok_analizleri["ifade_merkez"] = ifade_ozet.to_dict(orient="records")
            blok_kaliteleri["ifade_merkez"] = ifade_kalite or {}
        ozet_df = mcrt_birlesik_ozet(marka_ozet, ifade_ozet)
        varsayilan_gorunum = "birlesik"
    else:
        tum_secenekler = mcrt_secenek_evreni(db, proje_id, proje=proje, kurgu=kurgu)
        ozet_df, kalite_raporu = mcrt_temel_analiz(
            df,
            tum_secenekler=tum_secenekler,
            kurgu=kurgu
        )

    istatistik = []
    if include_stats and not ozet_df.empty:
        cache_key = _mcrt_cache_key(proje_id, proje, df)
        cached = _MCRT_ISTATISTIK_CACHE.get(cache_key)
        now = time.time()
        if cached and (now - cached.get("ts", 0) < _MCRT_ISTATISTIK_TTL_SN):
            istatistik = cached.get("data") or []
        else:
            istatistik = mcrt_marka_karsilastirma_testi(ozet_df)
            _MCRT_ISTATISTIK_CACHE[cache_key] = {"ts": now, "data": istatistik}

    ifade_df = pd.DataFrame(db.proje_ifadeleri(proje_id) or [])
    if not ozet_df.empty and not ifade_df.empty and "metin" in ifade_df.columns:
        kategori_map = {
            str(row.get("metin") or ""): str(row.get("kategori") or "").strip()
            for _, row in ifade_df.iterrows()
        }
        ozet_df["kategori"] = ozet_df["ifade"].astype(str).map(kategori_map).fillna("")

    return {
        "ozet": ozet_df.to_dict(orient="records") if not ozet_df.empty else [],
        "kalite": kalite_raporu,
        "istatistik": istatistik,
        "korelasyon": {},
        "kategori_ozet": kategori_ozeti_uret(ozet_df, ifade_df),
        "blok_analizleri": blok_analizleri,
        "blok_kaliteleri": blok_kaliteleri,
        "varsayilan_gorunum": varsayilan_gorunum,
        "test_turu": "mcrt",
        "analiz_motoru": "MCRT",
        "veri_kaynagi": "mcrt_cevaplar"
    }

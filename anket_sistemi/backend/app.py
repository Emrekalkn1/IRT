# -*- coding: utf-8 -*-
"""
Marka Algi Anket Sistemi - Flask Uygulamasi
Proje bazli mimari
"""

import os
import sys
import uuid
import math
import io
import json
import zipfile
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import (
    Flask, render_template, request, jsonify,
    session, make_response, redirect, url_for, send_from_directory, send_file
)
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

PROJE_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJE_KOK, ".env"))
sys.path.insert(0, PROJE_KOK)

import pandas as pd
import numpy as np
from backend.database import Veritabani

app = Flask(
    __name__,
    template_folder=os.path.join(PROJE_KOK, "backend", "templates"),
    static_folder=os.path.join(PROJE_KOK, "static")
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY environment variable is not set!")

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=1800,
    WTF_CSRF_SSL_STRICT=False
)

# Guvenlik Eklentileri
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "75 per hour"],
    storage_uri="memory://",
)

import logging
import logging.handlers

log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')
logging.basicConfig(
    handlers=[logging.handlers.RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)],
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
db = Veritabani()


def no_store_response(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def mcrt_dortlu_guardrail_ozeti(proje_id, kurgu=None):
    proje = db.proje_getir(proje_id) or {}
    kurgu = (kurgu or proje.get("mcrt_kurgu") or "cift_blok").strip().lower().replace("-", "_")
    markalar = db.proje_markalari(proje_id)
    ifadeler = db.proje_ifadeleri(proje_id)
    marka_sayisi = len(markalar or [])
    ifade_sayisi = len(ifadeler or [])
    mesajlar = []
    uygun = True

    if kurgu in ("marka_merkez", "cift_blok"):
        if ifade_sayisi == 0 or ifade_sayisi % 4 != 0:
            uygun = False
            mesajlar.append(f"Ifade sayisi 4'un kati olmali. Mevcut: {ifade_sayisi}")

    if kurgu in ("ifade_merkez", "cift_blok"):
        if marka_sayisi == 0 or marka_sayisi % 4 != 0:
            uygun = False
            mesajlar.append(f"Marka sayisi 4'un kati olmali. Mevcut: {marka_sayisi}")

    return {
        "uygun": uygun,
        "marka_sayisi": marka_sayisi,
        "ifade_sayisi": ifade_sayisi,
        "mesajlar": mesajlar
    }

# Varsayilan admin olustur (Eger yoksa)
def varsayilan_admin_olustur():
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    
    if not admin_user or not admin_pass:
        return # .env henuz yuklenmemis olabilir veya eksik
    
    admin = db.kullanici_dogrula(admin_user)
    if not admin:
        db.kullanici_olustur(admin_user, generate_password_hash(admin_pass), "Sistem YÃ¶neticisi")

varsayilan_admin_olustur()

# Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_sayfasi'))
        return f(*args, **kwargs)
    return decorated_function

UPLOAD_FOLDER = os.path.join(PROJE_KOK, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'mp3', 'wav', 'ogg', 'm4a'}

@app.route('/output/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(PROJE_KOK, "output"), filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def yedek_zip_olustur(proje_id):
    yedek_verisi = db.proje_yedek_verisi(proje_id)
    proje = yedek_verisi.get("proje") or {}
    proje_adi = secure_filename(proje.get("ad") or f"proje_{proje_id}") or f"proje_{proje_id}"
    zaman = datetime.now().strftime("%Y%m%d_%H%M%S")

    referans_dosyalar = set()
    for item in (yedek_verisi.get("markalar") or []):
        if item.get("resim_dosya"):
            referans_dosyalar.add(item["resim_dosya"])
    for item in (yedek_verisi.get("ifadeler") or []):
        if item.get("resim_dosya"):
            referans_dosyalar.add(item["resim_dosya"])
    for item in (yedek_verisi.get("mcrt_secenekler") or []):
        if item.get("resim_dosya"):
            referans_dosyalar.add(item["resim_dosya"])

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(yedek_verisi, ensure_ascii=False, indent=2))
        for dosya_adi in sorted(referans_dosyalar):
            safe_name = os.path.basename(dosya_adi)
            kaynak = os.path.join(UPLOAD_FOLDER, safe_name)
            if os.path.isfile(kaynak):
                zf.write(kaynak, arcname=f"uploads/{safe_name}")

    buffer.seek(0)
    dosya_adi = f"yedek_{proje_adi}_{zaman}.zip"
    return buffer, dosya_adi


def yedek_dosyasini_oku(yuklu_dosya):
    dosya_adi = (yuklu_dosya.filename or "").lower()
    ham = yuklu_dosya.read()
    if not ham:
        raise ValueError("Yuklenen yedek dosyasi bos.")

    dosya_haritasi = {}
    if dosya_adi.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(ham), "r") as zf:
            if "manifest.json" not in zf.namelist():
                raise ValueError("ZIP yedeÄŸinde manifest.json bulunamadi.")
            yedek_verisi = json.loads(zf.read("manifest.json").decode("utf-8"))

            for uye in zf.namelist():
                if not uye.startswith("uploads/") or uye.endswith("/"):
                    continue
                eski_ad = os.path.basename(uye)
                if not eski_ad:
                    continue
                hedef_ad = secure_filename(eski_ad) or f"yedek_{uuid.uuid4().hex[:8]}"
                if not allowed_file(hedef_ad):
                    continue
                kok, ext = os.path.splitext(hedef_ad)
                sayac = 1
                hedef_yol = os.path.join(UPLOAD_FOLDER, hedef_ad)
                while os.path.exists(hedef_yol):
                    hedef_ad = f"{kok}_{sayac}{ext}"
                    hedef_yol = os.path.join(UPLOAD_FOLDER, hedef_ad)
                    sayac += 1
                with zf.open(uye) as src, open(hedef_yol, "wb") as dst:
                    dst.write(src.read())
                dosya_haritasi[eski_ad] = hedef_ad
        return yedek_verisi, dosya_haritasi

    if dosya_adi.endswith(".json"):
        return json.loads(ham.decode("utf-8")), dosya_haritasi

    raise ValueError("Sadece .zip veya .json yedek dosyasi yuklenebilir.")


# ========================
# ANA SAYFALAR
# ========================

@app.route("/")
def anasayfa():
    return redirect("/secure-mrt-admin")


@app.route("/secure-mrt-admin")
@login_required
def admin_panel():
    return render_template("admin.html")


@app.route("/secure-mrt-auth", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour")
def login_sayfasi():
    if request.method == "POST":
        data = request.form
        username = data.get("username")
        password = data.get("password")
        ip = get_remote_address()

        lock = db.check_login_lockout(username, ip)
        if lock:
            return no_store_response(
                make_response(render_template("login.html", hata="Cok fazla basarisiz deneme. Lutfen 15 dakika sonra tekrar deneyin."))
            )

        logging.info(f"[AUTH] Attempt: detected_ip={'masked' if ip else 'none'}")

        user = db.kullanici_dogrula(username)
        success = user and check_password_hash(user["password_hash"], password)
        logging.info(f"[AUTH] Login attempt: user={username}, ip={ip}, found={bool(user)}, success={success}")

        db.track_login_attempt(username, ip, success)

        if success:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["ad_soyad"] = user["ad_soyad"]
            logging.info("[AUTH] Success! Redirecting to admin panel.")
            return redirect(url_for("admin_panel"))

        return no_store_response(
            make_response(render_template("login.html", hata="Hatali kullanici adi veya sifre"))
        )

    if "user_id" in session:
        return redirect(url_for("admin_panel"))
    return no_store_response(make_response(render_template("login.html")))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_sayfasi"))


@app.route("/anket/<kod>")
@app.route("/anket/<kod>/<token>")
def anket_sayfasi(kod, token=None):
    proje = db.proje_kod_ile_getir(kod)
    if not proje:
        return render_template("anket.html", hata="Bu anket bulunamadi."), 404
    
    # Token kontrolÃ¼
    if token:
        tk = db.katilimci_linki_dogrula(token)
        if not tk or tk['proje_id'] != proje['id']:
            return render_template("anket.html", hata="Bu link gecersiz veya daha once kullanilmis."), 403
    
    if proje['durum'] == 'kapali':
        return render_template("anket.html", hata="Bu anket henuz yayinlanmadi.")

    markalar = db.proje_markalari(proje['id'])
    ifadeler = db.proje_ifadeleri(proje['id'])
    
    # MCRT Seceneklerini Yukle
    mcrt_secenekler = []
    if proje.get('test_turu') in ['mcrt', 'mrt']:
        mcrt_secenekler = db.proje_mcrt_secenekleri(proje['id'])

    # Ã‡erez kontrolÃ¼ (Sadece token yoksa veya token geÃ§ersizse ana engelleyici olsun)
    tamamlandi_cerezi = request.cookies.get(f"anket_{kod}", "0") == "1"
    
    # EÄŸer geÃ§erli bir token varsa, Ã§erezi gÃ¶rmezden gel (aynÄ± cihazdan farklÄ± katÄ±lÄ±mcÄ±lar iÃ§in)
    is_tamamlandi = tamamlandi_cerezi
    if token and not (not tk or tk['proje_id'] != proje['id']):
        is_tamamlandi = False

    return render_template(
        "anket.html",
        proje=proje,
        markalar=markalar,
        ifadeler=ifadeler,
        tamamlandi=is_tamamlandi,
        hata=None,
        token=token,
        mcrt_secenekler=mcrt_secenekler
    )


# ========================
# PROJE API
# ========================

@app.route("/api/projeler", methods=["GET"])
@login_required
def projeler_listele():
    try:
        include_archived = request.args.get("include_archived", "0") == "1"
        projeler = db.tum_projeler(include_archived=include_archived)
        for p in projeler:
            stat = db.proje_istatistik(p['id'])
            p['katilimci_sayisi'] = stat['katilimci_sayisi']
            p['toplam_cevap'] = stat['toplam_cevap']
            p['istatistik'] = stat # Detayli istatistikleri de gonder
        return jsonify({"durum": "basarili", "projeler": projeler})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/olustur", methods=["POST"])
@login_required
def proje_olustur():
    try:
        veri = request.get_json()
        ad = veri.get("ad", "").strip()
        aciklama = veri.get("aciklama", "").strip()
        bilgilendirme = veri.get("bilgilendirme", "").strip()

        if not ad:
            return jsonify({"durum": "hata", "mesaj": "Proje adı boş olamaz."}), 400

        proje_id, kod = db.proje_olustur(ad, aciklama, bilgilendirme)
        return jsonify({
            "durum": "basarili",
            "proje_id": proje_id,
            "kod": kod,
            "mesaj": f"Proje '{ad}' oluÅŸturuldu!"
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>", methods=["GET"])
@login_required
def proje_detay(proje_id):
    try:
        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadi."}), 404
        proje['markalar'] = db.proje_markalari(proje_id)
        proje['ifadeler'] = db.proje_ifadeleri(proje_id)
        proje['istatistik'] = db.proje_istatistik(proje_id)
        return jsonify({"durum": "basarili", "proje": proje})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/guncelle", methods=["POST"])
@login_required
def proje_guncelle_api(proje_id):
    try:
        veri = request.get_json()
        db.proje_guncelle(
            proje_id,
            ad=veri.get("ad"),
            aciklama=veri.get("aciklama"),
            bilgilendirme=veri.get("bilgilendirme"),
            alistirma_aktif=veri.get("alistirma_aktif"),
            soru_randomize=veri.get("soru_randomize"),
            hedef_orneklem=veri.get("hedef_orneklem"),
            test_turu=veri.get("test_turu"),
            mcrt_kurgu=veri.get("mcrt_kurgu"),
            mcrt_yerlesim=veri.get("mcrt_yerlesim"),
            panel_complete_url=veri.get("panel_complete_url"),
            panel_screenout_url=veri.get("panel_screenout_url"),
            panel_quotafull_url=veri.get("panel_quotafull_url")
        )
        return jsonify({"durum": "basarili", "mesaj": "Proje gÃ¼ncellendi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/durum", methods=["POST"])
@login_required
def proje_durum(proje_id):
    try:
        veri = request.get_json()
        yeni_durum = veri.get("durum", "")
        if yeni_durum not in ("taslak", "canli", "kapali", "arsiv"):
            return jsonify({"durum": "hata", "mesaj": "GeÃ§ersiz durum."}), 400

        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadi."}), 404

        if yeni_durum == "canli":
            markalar = db.proje_markalari(proje_id)
            ifadeler = db.proje_ifadeleri(proje_id)
            if len(markalar) == 0:
                return jsonify({"durum": "hata", "mesaj": "En az 1 marka ekleyin."}), 400
            if len(ifadeler) == 0:
                return jsonify({"durum": "hata", "mesaj": "En az 1 ifade ekleyin."}), 400
            if (proje.get("test_turu") or "").lower() in ("mcrt", "mrt"):
                guard = mcrt_dortlu_guardrail_ozeti(proje_id, proje.get("mcrt_kurgu"))
                if not guard["uygun"]:
                    return jsonify({
                        "durum": "hata",
                        "mesaj": "MCRT 4'lu guardrail saglanmadi. " + " | ".join(guard["mesajlar"])
                    }), 400

        db.proje_durum_degistir(proje_id, yeni_durum)
        return jsonify({"durum": "basarili", "mesaj": f"Proje durumu: {yeni_durum}"})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500



@app.route("/api/proje/<int:proje_id>/kilit", methods=["POST"])
@login_required
def proje_kilit_api(proje_id):
    try:
        yeni_durum = db.proje_kilit_degistir(proje_id)
        if yeni_durum is None:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadı."}), 404
        return jsonify({"durum": "basarili", "kilitli": yeni_durum, "mesaj": "Kilit durumu güncellendi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/proje/<int:proje_id>/sil", methods=["DELETE"])
@login_required
def proje_sil_api(proje_id):
    try:
        db.proje_sil(proje_id)
        return jsonify({"durum": "basarili", "mesaj": "Proje silindi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500



@app.route("/api/katilimci/<oturum_id>/sil", methods=["DELETE"])
@login_required
def katilimci_sil_api(oturum_id):
    try:
        db.katilimci_sil(oturum_id)
        return jsonify({"durum": "basarili", "mesaj": "Katılımcı ve verileri silindi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/proje/<int:proje_id>/yedekle", methods=["GET"])
@login_required
def proje_yedekle_api(proje_id):
    try:
        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadi."}), 404
        buffer, dosya_adi = yedek_zip_olustur(proje_id)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=dosya_adi,
            mimetype="application/zip"
        )
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/klonla", methods=["POST"])
@login_required
def proje_klonla_api(proje_id):
    try:
        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadi."}), 404
            
        yedek_verisi = db.proje_yedek_verisi(proje_id)
        yedek_verisi["proje"]["ad"] = proje["ad"] + " (Klon)"
        # Klonlama isleminde veritabani baglantilari kopyalanacak. 
        # Uploads icindeki dosya isimleri ayni kalacak (dosya_haritasi bossa kendi adini kullanir)
        sonuc = db.proje_yedekten_yukle(yedek_verisi, {})
        return jsonify({
            "durum": "basarili",
            "mesaj": f"Proje klonlandi: '{sonuc['ad']}'.",
            "proje_id": sonuc["proje_id"],
            "kod": sonuc["kod"]
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/yedek_yukle", methods=["POST"])
@login_required
def proje_yedek_yukle_api():
    try:
        if "yedek" not in request.files:
            return jsonify({"durum": "hata", "mesaj": "Lutfen bir yedek dosyasi secin."}), 400

        yuklu_dosya = request.files["yedek"]
        yedek_verisi, dosya_haritasi = yedek_dosyasini_oku(yuklu_dosya)
        sonuc = db.proje_yedekten_yukle(yedek_verisi, dosya_haritasi)
        return jsonify({
            "durum": "basarili",
            "mesaj": f"Yedek yuklendi. '{sonuc['ad']}' projesi geri getirildi.",
            "proje_id": sonuc["proje_id"],
            "kod": sonuc["kod"]
        })
    except ValueError as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 400
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


# ========================
# KATILIMCI LINKI API
# ========================

@app.route("/api/proje/<int:proje_id>/link_olustur", methods=["POST"])
@login_required
def link_olustur_api(proje_id):
    try:
        veri = request.get_json()
        adet = int(veri.get("adet", 1))
        if adet < 1 or adet > 500:
            return jsonify({"durum": "hata", "mesaj": "GeÃ§ersiz adet (1-500)."}), 400
        
        tokens = db.katilimci_linki_olustur(proje_id, adet)
        return jsonify({
            "durum": "basarili",
            "mesaj": f"{adet} adet link oluÅŸturuldu.",
            "tokens": tokens
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/linkler", methods=["GET"])
@login_required
def linkleri_getir_api(proje_id):
    try:
        linkler = db.katilimci_linkleri_getir(proje_id)
        return jsonify({"durum": "basarili", "linkler": linkler})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/link/<token>/yeniden_ac", methods=["POST"])
@login_required
def link_yeniden_ac_api(proje_id, token):
    try:
        db.katilimci_linki_yeniden_ac(proje_id, token)
        return jsonify({"durum": "basarili", "mesaj": "Link yeniden acildi. Katilimci teste bastan girebilir."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


# ========================
# MARKA API
# ========================

@app.route("/api/proje/<int:proje_id>/marka", methods=["POST"])
@login_required
def marka_ekle_api(proje_id):
    try:

        proje = db.proje_getir(proje_id)
        if proje and proje.get("kilitli") == 1:
            return jsonify({"durum": "hata", "mesaj": "Proje kilitli. İfade, marka veya seçenek eklenip silinemez."}), 403
        ad = request.form.get("ad", "").strip()
        if not ad:
            return jsonify({"durum": "hata", "mesaj": "Marka adı boş olamaz."}), 400

        resim_dosya = ""
        if 'resim' in request.files:
            dosya = request.files['resim']
            if dosya and dosya.filename and allowed_file(dosya.filename):
                filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{dosya.filename}")
                dosya.save(os.path.join(UPLOAD_FOLDER, filename))
                resim_dosya = filename

        is_noise = request.form.get("is_noise", "0") == "1"
        analiz_etiketi = request.form.get("analiz_etiketi", "").strip()
        marka_id = db.marka_ekle(proje_id, ad, resim_dosya, is_noise, analiz_etiketi)
        return jsonify({
            "durum": "basarili",
            "marka_id": marka_id,
            "mesaj": f"Marka '{ad}' eklendi."
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/marka/<int:marka_id>/sil", methods=["DELETE"])
@login_required
def marka_sil_api(marka_id):
    try:

        conn = db._baglanti_al()
        c = db._get_cursor(conn)
        c.execute("SELECT proje_id FROM markalar WHERE id=?", (marka_id,))
        row = c.fetchone()
        conn.close()
        if row:
            proje = db.proje_getir(row['proje_id'] if db.db_type == "mysql" else row[0])
            if proje and proje.get("kilitli") == 1:
                return jsonify({"durum": "hata", "mesaj": "Proje kilitli."}), 403
        db.marka_sil(marka_id)
        return jsonify({"durum": "basarili", "mesaj": "Marka silindi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


# ========================
# IFADE API
# ========================

@app.route("/api/proje/<int:proje_id>/ifade", methods=["POST"])
@login_required
def ifade_ekle_api(proje_id):
    try:

        proje = db.proje_getir(proje_id)
        if proje and proje.get("kilitli") == 1:
            return jsonify({"durum": "hata", "mesaj": "Proje kilitli. İfade, marka veya seçenek eklenip silinemez."}), 403
        metin = request.form.get("metin", "").strip()
        kategori = request.form.get("kategori", "").strip()
        if not metin:
            return jsonify({"durum": "hata", "mesaj": "İfade metni boş olamaz."}), 400

        resim_dosya = ""
        if 'resim' in request.files:
            dosya = request.files['resim']
            if dosya and dosya.filename and allowed_file(dosya.filename):
                filename = secure_filename(f"ifade_{uuid.uuid4().hex[:8]}_{dosya.filename}")
                dosya.save(os.path.join(UPLOAD_FOLDER, filename))
                resim_dosya = filename

        ifade_id = db.ifade_ekle(proje_id, metin, kategori, resim_dosya)
        return jsonify({
            "durum": "basarili",
            "ifade_id": ifade_id,
            "mesaj": f"İfade '{metin}' eklendi."
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/ifade/<int:ifade_id>/sil", methods=["DELETE"])
@login_required
def ifade_sil_api(ifade_id):
    try:

        conn = db._baglanti_al()
        c = db._get_cursor(conn)
        c.execute("SELECT proje_id FROM ifadeler WHERE id=?", (ifade_id,))
        row = c.fetchone()
        conn.close()
        if row:
            proje = db.proje_getir(row['proje_id'] if db.db_type == "mysql" else row[0])
            if proje and proje.get("kilitli") == 1:
                return jsonify({"durum": "hata", "mesaj": "Proje kilitli."}), 403
        db.ifade_sil(ifade_id)
        return jsonify({"durum": "basarili", "mesaj": "İfade silindi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


# ========================
# MCRT SECENEK API
# ========================

@app.route("/api/proje/<int:proje_id>/mcrt_secenekler", methods=["GET"])
@login_required
def mcrt_secenekler_api(proje_id):
    try:
        secenekler = db.proje_mcrt_secenekleri(proje_id)
        return jsonify({"durum": "basarili", "secenekler": secenekler})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/proje/<int:proje_id>/mcrt_secenek", methods=["POST"])
@login_required
def mcrt_secenek_ekle_api(proje_id):
    try:

        proje = db.proje_getir(proje_id)
        if proje and proje.get("kilitli") == 1:
            return jsonify({"durum": "hata", "mesaj": "Proje kilitli. İfade, marka veya seçenek eklenip silinemez."}), 403
        metin = request.form.get("metin", "").strip()
        if not metin:
            return jsonify({"durum": "hata", "mesaj": "SeÃ§enek metni boÅŸ olamaz."}), 400

        resim_dosya = ""
        if 'resim' in request.files:
            dosya = request.files['resim']
            if dosya and dosya.filename and allowed_file(dosya.filename):
                filename = secure_filename(f"mcrt_{uuid.uuid4().hex[:8]}_{dosya.filename}")
                dosya.save(os.path.join(UPLOAD_FOLDER, filename))
                resim_dosya = filename

        secenek_id = db.mcrt_secenek_ekle(proje_id, metin, resim_dosya)
        return jsonify({
            "durum": "basarili",
            "secenek_id": secenek_id,
            "mesaj": f"SeÃ§enek '{metin}' eklendi."
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/mcrt_secenek/<int:secenek_id>/sil", methods=["DELETE"])
@login_required
def mcrt_secenek_sil_api(secenek_id):
    try:

        conn = db._baglanti_al()
        c = db._get_cursor(conn)
        c.execute("SELECT proje_id FROM mcrt_secenekler WHERE id=?", (secenek_id,))
        row = c.fetchone()
        conn.close()
        if row:
            proje = db.proje_getir(row['proje_id'] if db.db_type == "mysql" else row[0])
            if proje and proje.get("kilitli") == 1:
                return jsonify({"durum": "hata", "mesaj": "Proje kilitli."}), 403
        db.mcrt_secenek_sil(secenek_id)
        return jsonify({"durum": "basarili", "mesaj": "SeÃ§enek silindi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


# ========================
# CEVAP API (katilimci)
# ========================

@app.route("/api/oturum_baslat", methods=["POST"])
@limiter.limit("20 per minute")
def oturum_baslat_api():
    try:
        veri = request.get_json()
        proje_id = veri.get("proje_id")
        oturum_id = veri.get("oturum_id")
        profil = veri.get("profil_verisi", {})
        token = veri.get("token")
        
        # Tarayici ve IP bilgisi
        ua = request.headers.get('User-Agent', '')
        profil["tarayici_bilgisi"] = ua
        profil["ip_adresi"] = request.remote_addr or "bilinmiyor"
        profil["cihaz_tipi"] = "Mobil" if any(x in ua for x in ["Mobile", "Android", "iPhone"]) else "MasaÃ¼stÃ¼"
        
        # GPS verilerini profil nesnesine aktar
        profil["enlem"] = veri.get("enlem")
        profil["boylam"] = veri.get("boylam")
        profil["konum_hassasiyet"] = veri.get("konum_hassasiyet")
        
        db.oturum_baslat(proje_id, oturum_id, profil, token)
        return jsonify({"durum": "basarili"})
    except ValueError as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 403
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/cevap_kaydet", methods=["POST"])
@limiter.limit("500 per minute")
def cevap_kaydet():
    try:
        veri = request.get_json()
        if not veri:
            return jsonify({"durum": "hata", "mesaj": "Veri bulunamadı."}), 400

        proje_id = veri.get("proje_id")
        cevaplar = veri.get("cevaplar", [])
        oturum_id = veri.get("oturum_id")
        proje_kod = veri.get("proje_kod", "")

        if not cevaplar or not proje_id or not oturum_id:
            return jsonify({"durum": "hata", "mesaj": "Eksik veri."}), 400

        katilimci_id = request.remote_addr or "bilinmiyor"
        kalite_metrikleri = veri.get("kalite_metrikleri", {})
        
        # Test tÃ¼rÃ¼ne gÃ¶re yÃ¶nlendirme
        proje = db.proje_getir(proje_id)
        is_mcrt = proje and (proje.get('test_turu') == 'mcrt' or proje.get('test_turu') == 'mrt')
        
        if is_mcrt:
            kayit = db.mcrt_toplu_cevap_kaydet(proje_id, cevaplar, katilimci_id, oturum_id, kalite_metrikleri)
        else:
            kayit = db.toplu_cevap_kaydet(proje_id, cevaplar, katilimci_id, oturum_id, kalite_metrikleri)

        response = make_response(jsonify({
            "durum": "basarili",
            "mesaj": f"{kayit} cevap kaydedildi!",
            "kayit_sayisi": kayit
        }))

        if proje_kod:
            response.set_cookie(f"anket_{proje_kod}", "1", max_age=30*24*60*60, httponly=True, secure=True, samesite='Lax')

        return response
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


# ========================
# ANALIZ API
# ========================

@app.route("/api/proje/<int:proje_id>/veriler", methods=["GET"])
@login_required
def proje_veriler(proje_id):
    try:
        marka_id = request.args.get("marka_id")
        oturum_id = request.args.get("oturum_id")
        page_raw = request.args.get("page", "1")
        per_page_raw = request.args.get("per_page")
        limit_raw = request.args.get("limit")
        try:
            page = max(1, int(page_raw))
        except Exception:
            page = 1
        try:
            per_page = max(1, min(int(per_page_raw or limit_raw or "10"), 200))
        except Exception:
            per_page = 10
        proje = db.proje_getir(proje_id)
        is_mcrt = proje and (proje.get('test_turu') in ['mcrt', 'mrt'])
        if is_mcrt:
            df = db.proje_mcrt_verileri_df(proje_id)
            if marka_id and df is not None and not df.empty:
                df = df[df["marka_id"] == int(marka_id)] if "marka_id" in df.columns else df
            if oturum_id and df is not None and not df.empty:
                df = df[df["oturum_id"].astype(str).str.lower() == str(oturum_id).lower()] if "oturum_id" in df.columns else df
            if df is None or df.empty:
                veriler = []
                toplam_kayit = 0
            else:
                df = df.copy()
                df["cevap"] = df.get("cevap_metin")
                df = df.sort_values("tarih", ascending=False)
                toplam_kayit = len(df)
                toplam_sayfa = max(1, math.ceil(toplam_kayit / per_page)) if toplam_kayit else 1
                page = min(page, toplam_sayfa)
                baslangic = (page - 1) * per_page
                bitis = baslangic + per_page
                df = df.iloc[baslangic:bitis]
                df = df.astype(object).where(pd.notna(df), None)
                veriler = df.to_dict(orient="records")
        else:
            veriler = db.proje_verileri(proje_id, marka_id=marka_id)
            if oturum_id:
                veriler = [v for v in veriler if str(v.get("oturum_id", "")).lower() == str(oturum_id).lower()]
            toplam_kayit = len(veriler)
            toplam_sayfa = max(1, math.ceil(toplam_kayit / per_page)) if toplam_kayit else 1
            page = min(page, toplam_sayfa)
            baslangic = (page - 1) * per_page
            bitis = baslangic + per_page
            veriler = veriler[baslangic:bitis]
        toplam_sayfa = max(1, math.ceil(toplam_kayit / per_page)) if toplam_kayit else 1
        return jsonify({
            "durum": "basarili",
            "veriler": veriler,
            "sayfalama": {
                "sayfa": page,
                "sayfa_boyutu": per_page,
                "toplam_kayit": toplam_kayit,
                "toplam_sayfa": toplam_sayfa
            }
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/istatistik", methods=["GET"])
@login_required
def proje_istatistik_api(proje_id):
    try:
        stat = db.proje_istatistik(proje_id)
        return jsonify({"durum": "basarili", "istatistik": stat})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/explicit_ozet", methods=["GET"])
@login_required
def explicit_ozet(proje_id):
    try:
        filtre = {
            "cinsiyet": request.args.get("cinsiyet"),
            "yas_min": request.args.get("yas_min"),
            "yas_max": request.args.get("yas_max"),
            "ses_grubu": request.args.get("ses_grubu"),
            "il": request.args.get("il")
        }
        # BoÅŸ olanlarÄ± temizle
        filtre = {k: v for k, v in filtre.items() if v}
        
        # Verileri Ã§ek ve analiz et
        from analiz.analiz import explicit_implicit_analiz, marka_karsilastirma_testi, veri_kalite_ozeti, korelasyon_hesapla
        import pandas as pd
        
        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadı."}), 404

        test_turu = (proje.get('test_turu') or 'standart').lower()
        is_mcrt = test_turu in ['mcrt', 'mrt']

        if is_mcrt:
            analiz_paketi = mcrt_proje_analizi(db, proje_id, include_stats=False)
            return jsonify({
                "durum": "basarili",
                "test_turu": "mcrt",
                "ozet": analiz_paketi.get("ozet") or [],
                "korelasyon": analiz_paketi.get("korelasyon") or {},
                "istatistik": analiz_paketi.get("istatistik") or [],
                "kalite": analiz_paketi.get("kalite") or {},
                "blok_analizleri": analiz_paketi.get("blok_analizleri") or {},
                "varsayilan_gorunum": analiz_paketi.get("varsayilan_gorunum") or "tek_blok",
                "analiz_motoru": "MCRT"
            })

        df = db.proje_verileri_df(proje_id)

        if df is None or df.empty:
            return jsonify({"durum": "hata", "mesaj": "HenÃ¼z veri yok."})

        # 1. Ana Analiz ve Kalite Filtreleme
        sonuc_df, kalite_raporu = explicit_implicit_analiz(df)
        
        # 2. Ä°statistiksel KarÅŸÄ±laÅŸtÄ±rmalar (p-value, Cohen's d vb.)
        istatistiksel_farklar = marka_karsilastirma_testi(df)
        
        # 3. Veri Kalite Ã–zeti
        kalite_ozeti = veri_kalite_ozeti(df, kalite_raporu)
        
        # 4. Korelasyonlar
        kor_sonuc = korelasyon_hesapla(sonuc_df)

        return jsonify({
            "durum": "basarili", 
            "ozet": sonuc_df.to_dict(orient="records"),
            "korelasyon": kor_sonuc,
            "istatistik": istatistiksel_farklar,
            "kalite": kalite_ozeti
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/analiz_istatistik", methods=["GET"])
@login_required
def proje_analiz_istatistik_api(proje_id):
    try:
        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadı."}), 404

        test_turu = (proje.get('test_turu') or 'standart').lower()
        is_mcrt = test_turu in ['mcrt', 'mrt']

        if is_mcrt:
            from analiz.mcrt_analysis_service import mcrt_proje_analizi
            try:
                analiz_paketi = mcrt_proje_analizi(db, proje_id, include_stats=True)
                return jsonify({
                    "durum": "basarili",
                    "test_turu": "mcrt",
                    "istatistik": analiz_paketi.get("istatistik") or []
                })
            except Exception as e:
                print(f"MCRT istatistik hesaplama hatasi (proje {proje_id}): {e}")
                return jsonify({
                    "durum": "basarili",
                    "test_turu": "mcrt",
                    "istatistik": [],
                    "mesaj": f"MCRT istatistik tablosu hesaplanamadi: {e}"
                })

        from analiz.analiz import marka_karsilastirma_testi
        df = db.proje_verileri_df(proje_id)
        if df is None or df.empty:
            return jsonify({"durum": "basarili", "test_turu": "standart", "istatistik": []})
        return jsonify({
            "durum": "basarili",
            "test_turu": "standart",
            "istatistik": marka_karsilastirma_testi(df)
        })
    except Exception as e:
        print(f"Analiz istatistik endpoint hatasi (proje {proje_id}): {e}")
        return jsonify({
            "durum": "basarili",
            "istatistik": [],
            "mesaj": f"Istatistik tablosu hesaplanamadi: {e}"
        })


@app.route("/api/proje/<int:proje_id>/katilimci_analiz")
@login_required
def katilimci_analiz(proje_id):
    try:
        page_raw = request.args.get("page", "1")
        per_page_raw = request.args.get("per_page", "10")
        try:
            page = max(1, int(page_raw))
        except Exception:
            page = 1
        try:
            per_page = max(1, min(int(per_page_raw), 200))
        except Exception:
            per_page = 10
        proje = db.proje_getir(proje_id)
        if proje and (proje.get('test_turu') in ['mcrt', 'mrt']):
            data = db.proje_katilimci_analizi_mcrt(proje_id)
        else:
            data = db.proje_katilimci_analizi(proje_id)
        toplam_kayit = len(data or [])
        toplam_sayfa = max(1, math.ceil(toplam_kayit / per_page)) if toplam_kayit else 1
        page = min(page, toplam_sayfa)
        baslangic = (page - 1) * per_page
        bitis = baslangic + per_page
        data = (data or [])[baslangic:bitis]
        return jsonify({
            "durum": "basarili",
            "katilimcilar": data,
            "sayfalama": {
                "sayfa": page,
                "sayfa_boyutu": per_page,
                "toplam_kayit": toplam_kayit,
                "toplam_sayfa": toplam_sayfa
            }
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/proje/<int:proje_id>/analiz_rapor", methods=["POST"])
@login_required
def analiz_rapor(proje_id):
    try:
        from analiz.analiz import (
            explicit_implicit_analiz,
            korelasyon_hesapla,
            marka_karsilastirma_testi,
            marka_modern_geleneksel,
        )
        from analiz.mcrt_analysis_service import mcrt_proje_analizi
        from analiz.irt_analysis_service import irt_proje_analizi
        from analiz.rapor_olustur import rapor_olustur, rapor_paketi_olustur

        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadi."}), 404

        data = request.get_json(silent=True) or {}
        include_ai_text = bool(data.get("include_ai_text"))
        ai_slide_pack = data.get("ai_slide_pack") or {}
        ai_text = (data.get("ai_text") or db.ai_analiz_getir(proje_id)) if include_ai_text else None
        test_turu = (proje.get("test_turu") or "standart").lower()
        is_mcrt = test_turu in ["mcrt", "mrt"]
        rapor_meta = {
            "project_name": proje.get("ad") or f"Proje {proje_id}",
            "test_type": "MCRT" if is_mcrt else "IRT",
            "analysis_engine": "MCRT" if is_mcrt else "IRT",
            "quality": {},
            "correlation": {},
            "statistics": [],
            "category_summary": [],
            "blok_analizleri": {},
        }

        if is_mcrt:
            analiz_paketi = mcrt_proje_analizi(db, proje_id)
            sonuc = pd.DataFrame(analiz_paketi.get("ozet") or [])
            if sonuc.empty:
                return jsonify({"durum": "uyari", "mesaj": "Henüz analiz edilecek veri yok."})

            sonuc = sonuc.copy()
            if "implicit_guc" not in sonuc.columns:
                if "implicit_skor" in sonuc.columns:
                    sonuc["implicit_guc"] = sonuc["implicit_skor"]
                elif "mcrt_skor" in sonuc.columns:
                    sonuc["implicit_guc"] = sonuc["mcrt_skor"]
                else:
                    sonuc["implicit_guc"] = 0
            if "explicit_pct" not in sonuc.columns:
                sonuc["explicit_pct"] = sonuc["secilme_orani"] if "secilme_orani" in sonuc.columns else 0
            if "implicit_skor" not in sonuc.columns:
                sonuc["implicit_skor"] = sonuc["implicit_guc"]
            if "n" not in sonuc.columns:
                sonuc["n"] = sonuc["toplam_secilme"] if "toplam_secilme" in sonuc.columns else 0

            rapor_icin_df = sonuc.copy().rename(columns={
                "marka": "Marka",
                "ifade": "İfade",
                "explicit_pct": "Explicit(%)",
                "implicit_guc": "Implicit_Guc"
            })
            marka_df = marka_modern_geleneksel(sonuc)
            rapor_meta["quality"] = analiz_paketi.get("kalite") or {}
            rapor_meta["statistics"] = analiz_paketi.get("istatistik") or []
            rapor_meta["category_summary"] = analiz_paketi.get("kategori_ozet") or []
            rapor_meta["blok_analizleri"] = analiz_paketi.get("blok_analizleri") or {}
            rapor_meta["blok_kaliteleri"] = analiz_paketi.get("blok_kaliteleri") or {}
            rapor_meta["ai_slide_pack"] = ai_slide_pack

        else:
            df = db.proje_verileri_df(proje_id)
            if df.empty:
                return jsonify({"durum": "uyari", "mesaj": "Henüz analiz edilecek veri yok."})

            sonuc, kalite_raporu = explicit_implicit_analiz(df)
            kor_sonuc = korelasyon_hesapla(sonuc)
            istatistik = marka_karsilastirma_testi(df)
            rapor_icin_df = sonuc.copy().rename(columns={
                "marka": "Marka",
                "ifade": "İfade",
                "explicit_pct": "Explicit(%)",
                "implicit_guc": "Implicit_Guc"
            })
            marka_df = marka_modern_geleneksel(sonuc)
            rapor_meta["quality"] = kalite_raporu
            rapor_meta["correlation"] = kor_sonuc
            rapor_meta["statistics"] = istatistik
            rapor_meta["category_summary"] = irt_proje_analizi(db, proje_id).get("kategori_ozet") or []
            rapor_meta["ai_slide_pack"] = ai_slide_pack

        profil_df = db.proje_katilimci_profilleri_df(proje_id)
        dosyalar = rapor_olustur(rapor_icin_df, marka_df, profil_df, ai_text, rapor_meta=rapor_meta)
        paket_yolu = rapor_paketi_olustur(dosyalar, paket_on_eki=f"rapor_paketi_{proje_id}")

        dosya_listesi = []
        for anahtar, tam_yol in dosyalar.items():
            if tam_yol:
                dosya_adi = os.path.basename(tam_yol)
                dosya_listesi.append({
                    "isim": dosya_adi,
                    "url": f"/output/{dosya_adi}"
                })

        return jsonify({
            "durum": "basarili",
            "mesaj": "Rapor olusturuldu!",
            "dosyalar": dosya_listesi,
            "paket_url": f"/output/{os.path.basename(paket_yolu)}",
            "paket_isim": os.path.basename(paket_yolu)
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/analiz")
@login_required
def proje_analiz_api(proje_id):
    try:
        proje = db.proje_getir(proje_id)
        is_mcrt = proje and (proje.get('test_turu') in ['mcrt', 'mrt'])

        if is_mcrt:
            from analiz.mcrt_analysis_service import mcrt_proje_analizi
            return jsonify(mcrt_proje_analizi(db, proje_id, include_stats=False))
        else:
            from analiz.irt_analysis_service import irt_proje_analizi
            return jsonify(irt_proje_analizi(db, proje_id))
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/api/proje/<int:proje_id>/ai_rapor", methods=["POST"])
@login_required
def ai_rapor(proje_id):
    try:
        proje = db.proje_getir(proje_id)
        if not proje:
            return jsonify({"durum": "hata", "mesaj": "Proje bulunamadı."}), 404
        
        is_mcrt = proje.get('test_turu') in ['mcrt', 'mrt']
        proje_ad = proje.get("ad", "")

        # MCRT Analiz Dallanması
        if is_mcrt:
            from analiz.ai_uzman import mcrt_deepseek_rapor_olustur, mcrt_deepseek_slide_pack_olustur, mcrt_slide_pack_html
            from analiz.mcrt_analysis_service import mcrt_proje_analizi
            
            analiz_paketi = mcrt_proje_analizi(db, proje_id)
            ozet = pd.DataFrame(analiz_paketi.get("ozet") or [])
            if ozet.empty:
                return jsonify({"durum": "uyari", "mesaj": "Henüz analiz edilecek veri yok."})
            
            slide_pack = mcrt_deepseek_slide_pack_olustur(
                ozet,
                proje_ad,
                blok_analizleri=analiz_paketi.get("blok_analizleri") or {},
                kalite=analiz_paketi.get("kalite") or {},
                kategori_ozet=analiz_paketi.get("kategori_ozet") or [],
                istatistik=analiz_paketi.get("istatistik") or [],
            )
            ai_html = mcrt_slide_pack_html(slide_pack)
            if not ai_html:
                ai_html = mcrt_deepseek_rapor_olustur(
                    ozet,
                    proje_ad,
                    blok_analizleri=analiz_paketi.get("blok_analizleri") or {},
                    kalite=analiz_paketi.get("kalite") or {},
                    kategori_ozet=analiz_paketi.get("kategori_ozet") or [],
                    istatistik=analiz_paketi.get("istatistik") or [],
                )
            
            return jsonify({
                "durum": "basarili",
                "html": ai_html,
                "slide_pack": slide_pack,
                "kaynak": "yeni"
            })
        
        # Standart IRT Analizi (Aşağıdaki eski mantık devam eder)
        mevcut_analiz = db.ai_analiz_getir(proje_id)
        if mevcut_analiz:
            return jsonify({"durum": "basarili", "html": mevcut_analiz, "kaynak": "hafiza"})

        from analiz.analiz import explicit_implicit_analiz, marka_modern_geleneksel
        from analiz.ai_uzman import deepseek_rapor_olustur

        df = db.proje_verileri_df(proje_id)
        if df.empty:
            return jsonify({"durum": "uyari", "mesaj": "Henüz analiz edilecek veri yok."})

        sonuc, kalite_raporu = explicit_implicit_analiz(df)
        marka_df = marka_modern_geleneksel(sonuc)
        
        ai_html = deepseek_rapor_olustur(sonuc, marka_df, proje_ad)
        db.ai_analiz_kaydet(proje_id, ai_html)

        return jsonify({
            "durum": "basarili",
            "html": ai_html,
            "kaynak": "yeni"
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500
    
@app.route('/api/ai_ifade_onerisi', methods=['POST'])
@login_required
def api_ai_ifade_onerisi():
    data = request.json
    proje_ad = data.get('proje_ad', '')
    markalar = data.get('markalar', [])
    hedef_kitle = data.get('hedef_kitle', '')
    
    from analiz.ai_uzman import ai_ifade_onerisi
    oneriler = ai_ifade_onerisi(proje_ad, markalar, hedef_kitle)
    
    return jsonify({"durum": "basarili", "oneriler": oneriler})


@app.route('/api/ai_kategori_onerisi', methods=['POST'])
@login_required
def api_ai_kategori_onerisi():
    data = request.json or {}
    proje_ad = data.get('proje_ad', '')
    markalar = data.get('markalar', [])
    hedef_kitle = data.get('hedef_kitle', '')
    mevcut_ifadeler = data.get('mevcut_ifadeler', [])

    from analiz.ai_uzman import ai_kategori_onerisi
    kategoriler = ai_kategori_onerisi(proje_ad, markalar, hedef_kitle, mevcut_ifadeler=mevcut_ifadeler)
    return jsonify({"durum": "basarili", "kategoriler": kategoriler})


@app.route('/api/ai_kategori_ifade_onerisi', methods=['POST'])
@login_required
def api_ai_kategori_ifade_onerisi():
    data = request.json or {}
    proje_ad = data.get('proje_ad', '')
    markalar = data.get('markalar', [])
    hedef_kitle = data.get('hedef_kitle', '')
    kategori = (data.get('kategori') or '').strip()
    mevcut_ifadeler = data.get('mevcut_ifadeler', [])
    dislanan_ifadeler = data.get('dislanan_ifadeler', [])

    if not kategori:
        return jsonify({"durum": "hata", "mesaj": "Kategori gerekli."}), 400

    from analiz.ai_uzman import ai_kategoriye_gore_ifade_onerisi
    oneriler = ai_kategoriye_gore_ifade_onerisi(
        proje_ad,
        markalar,
        hedef_kitle,
        kategori,
        mevcut_ifadeler=mevcut_ifadeler,
        dislanan_ifadeler=dislanan_ifadeler,
        limit=4
    )
    return jsonify({"durum": "basarili", "kategori": kategori, "oneriler": oneriler[:4]})


@app.route("/api/proje/<int:proje_id>/katilimci_detaylari", methods=["POST"])
@login_required
def katilimci_detaylari_api(proje_id):
    try:
        veri = request.get_json()
        sifre = veri.get("sifre")
        
        # Admin sifresi ile kontrol (Ekstra gÃ¼venlik katmanÄ±)
        username = session.get("username")
        if not username:
            return jsonify({"durum": "hata", "mesaj": "Oturum bulunamadÄ±"}), 401
            
        user = db.kullanici_dogrula(username)
        if not user or not check_password_hash(user["password_hash"], sifre):
            return jsonify({"durum": "hata", "mesaj": "HatalÄ± ÅŸifre"}), 403
            
        # 1. KatÄ±lÄ±mcÄ± profillerini Ã§ek
        df_profiller = db.proje_katilimci_profilleri_df(proje_id)
        # NaN deÄŸerlerini None (null) yap ki JSON hata vermesin
        df_profiller = df_profiller.where(df_profiller.notna(), None)
        
        # 2. Kalite analizini yap (Neden elendiklerini gÃ¶rmek iÃ§in)
        from analiz.analiz import katilimci_kalite_analizi
        df_ham = db.proje_verileri_df(proje_id)
        kalite_detaylar = []
        if not df_ham.empty:
            _, kalite_raporu = katilimci_kalite_analizi(df_ham)
            kalite_detaylar = kalite_raporu.get('detaylar', [])
            
        # Kalite sonuÃ§larÄ±nÄ± bir sÃ¶zlÃ¼ÄŸe dÃ¶nÃ¼ÅŸtÃ¼r (HÄ±zlÄ± eriÅŸim iÃ§in)
        # DurumlarÄ± frontend ile uyumlu hale getir (OK -> GECERLI)
        kalite_map = {}
        for d in kalite_detaylar:
            oid = d.get('oturum_id')
            if oid:
                # 'sebep' alanÄ±nÄ± 'sorunlar' listesinden birleÅŸtirerek oluÅŸtur
                sebep_metni = ", ".join(d.get('sorunlar', [])) if d.get('sorunlar') else ""
                kalite_map[oid] = {
                    'durum': 'GECERLI' if d['durum'] == 'OK' else 'ELENDI',
                    'sebep': sebep_metni
                }
        
        # 3. Profilleri kalite verisiyle harmanla
        profiller_list = df_profiller.to_dict(orient="records")
        
        # Kesin temizlik: Her bir kaydÄ± gez ve NaN olanlarÄ± None (null) yap
        for p in profiller_list:
            # Ã–nce NaN temizliÄŸi (JSON gÃ¼venliÄŸi iÃ§in)
            for key, val in p.items():
                if isinstance(val, float) and np.isnan(val):
                    p[key] = None
            
            # Kalite verisi eÅŸleÅŸtirme
            q = kalite_map.get(p['oturum_id'])
            if q:
                p['analiz_durumu'] = q['durum']
                p['analiz_sebep'] = q.get('sebep', '')
            else:
                p['analiz_durumu'] = 'BILGI_YOK'
                p['analiz_sebep'] = 'Cevap bulunamadÄ±'
        
        return jsonify({
            "durum": "basarili",
            "profiller": profiller_list
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/katilimci/<oturum_id>/sil", methods=["DELETE"])
@login_required
def katilimci_sil_api(oturum_id):
    try:
        db.katilimci_sil(oturum_id)
        return jsonify({"durum": "basarili", "mesaj": "Katılımcı silindi."})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, port=5000)  # nosemgrep


# -*- coding: utf-8 -*-
"""
VeritabanÄ± Ä°ÅŸlemleri - SQLite / MySQL
Proje bazlÄ± yeni ÅŸema
"""

import sqlite3
import os
import math
import uuid
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

try:
    import mysql.connector
except ImportError:
    mysql = None

load_dotenv()


class Veritabani:

    def __init__(self, db_yolu=None):
        self.db_type = os.getenv("DB_TYPE", "sqlite") # 'sqlite' veya 'mysql'
        
        if self.db_type == "sqlite":
            if db_yolu is None:
                proje_kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                veri_klasoru = os.path.join(proje_kok, "veri")
                os.makedirs(veri_klasoru, exist_ok=True)
                db_yolu = os.path.join(veri_klasoru, "anket.db")
            self.db_yolu = db_yolu
        
        self._tablolari_olustur()

    def _get_cursor(self, conn):
        if self.db_type == "mysql":
            return conn.cursor(dictionary=True)
        else:
            return conn.cursor()

    def _p(self):
        """Placeholder yardÄ±mcÄ±sÄ±: MySQL iÃ§in %s, SQLite iÃ§in ? dÃ¶ner."""
        return "%s" if self.db_type == "mysql" else "?"

    def _baglanti_al(self):
        if self.db_type == "mysql":
            if mysql is None:
                raise RuntimeError("mysql-connector-python is not installed. Run: pip install -r requirements.txt")
            conn = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", ""),
                database=os.getenv("MYSQL_DB", "anket_sistemi"),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            # MySQL'de dict benzeri eriÅŸim iÃ§in
            # Cursor'Ä± fetch ederken dictionary=True kullanacaÄŸÄ±z
            return conn
        else:
            conn = sqlite3.connect(self.db_yolu)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn

    def _tablolari_olustur(self):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        if self.db_type == "sqlite":
            c.execute("CREATE TABLE IF NOT EXISTS projeler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, aciklama TEXT, durum TEXT, benzersiz_kod TEXT, olusturma_tarihi TEXT, katilimci_bilgilendirme TEXT, alistirma_aktif INTEGER, soru_randomize INTEGER, hedef_orneklem INTEGER, test_turu TEXT, panel_complete_url TEXT, panel_screenout_url TEXT, panel_quotafull_url TEXT, ai_analiz TEXT, mcrt_kurgu TEXT, mcrt_yerlesim TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS markalar (id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER, ad TEXT, resim_dosya TEXT, is_noise INTEGER, sira INTEGER, analiz_etiketi TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS ifadeler (id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER, metin TEXT, kategori TEXT, resim_dosya TEXT, sira INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS cevaplar (id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER, katilimci_id TEXT, marka_id INTEGER, ifade_id INTEGER, cevap TEXT, sure_ms INTEGER, tarih TEXT, oturum_id TEXT, is_alistirma INTEGER, baseline_ms INTEGER, dogru_cevap_mi INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS katilimci_profilleri (id INTEGER PRIMARY KEY AUTOINCREMENT, oturum_id TEXT UNIQUE, proje_id INTEGER, ad_soyad TEXT, yas INTEGER, cinsiyet TEXT, meslek TEXT, il TEXT, ilce TEXT, egitim TEXT, ev_durumu TEXT, araba_durumu TEXT, saglik_durumu TEXT, ses_grubu TEXT, cihaz_tipi TEXT, panel_pid TEXT, tarih TEXT, tarayici_bilgisi TEXT, baslangic_tarihi TEXT, bitis_tarihi TEXT, durum TEXT, ip_adresi TEXT, enlem FLOAT, boylam FLOAT, konum_hassasiyet FLOAT, baglanti_hatasi INTEGER, alistirma_hata_sayisi INTEGER, alistirma_toplam INTEGER, alistirma_hata_orani FLOAT, baseline_ms INTEGER)")
        else:
            c.execute("CREATE TABLE IF NOT EXISTS projeler (id INT AUTO_INCREMENT PRIMARY KEY, ad VARCHAR(255), aciklama LONGTEXT, durum VARCHAR(50), benzersiz_kod VARCHAR(50) UNIQUE, olusturma_tarihi VARCHAR(50), katilimci_bilgilendirme LONGTEXT, alistirma_aktif INTEGER, soru_randomize INTEGER, hedef_orneklem INTEGER, test_turu VARCHAR(50), panel_complete_url LONGTEXT, panel_screenout_url LONGTEXT, panel_quotafull_url LONGTEXT, ai_analiz LONGTEXT, mcrt_kurgu VARCHAR(50), mcrt_yerlesim VARCHAR(50))")
            c.execute("CREATE TABLE IF NOT EXISTS markalar (id INT AUTO_INCREMENT PRIMARY KEY, proje_id INTEGER, ad VARCHAR(255), resim_dosya VARCHAR(255), is_noise INT, sira INTEGER, analiz_etiketi TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS ifadeler (id INT AUTO_INCREMENT PRIMARY KEY, proje_id INTEGER, metin LONGTEXT, kategori VARCHAR(100), resim_dosya VARCHAR(255), sira INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS cevaplar (id INT AUTO_INCREMENT PRIMARY KEY, proje_id INTEGER, katilimci_id VARCHAR(100), marka_id INTEGER, ifade_id INTEGER, cevap VARCHAR(50), sure_ms INTEGER, tarih VARCHAR(50), oturum_id VARCHAR(100), is_alistirma INTEGER, baseline_ms INTEGER, dogru_cevap_mi INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS katilimci_profilleri (id INT AUTO_INCREMENT PRIMARY KEY, oturum_id VARCHAR(100) UNIQUE, proje_id INTEGER, ad_soyad VARCHAR(255), yas INTEGER, cinsiyet VARCHAR(20), meslek VARCHAR(255), il VARCHAR(100), ilce VARCHAR(100), egitim VARCHAR(100), ev_durumu VARCHAR(100), araba_durumu VARCHAR(100), saglik_durumu VARCHAR(100), ses_grubu VARCHAR(20), cihaz_tipi VARCHAR(255), panel_pid VARCHAR(255), tarih VARCHAR(50), tarayici_bilgisi LONGTEXT, baslangic_tarihi VARCHAR(50), bitis_tarihi VARCHAR(50), durum VARCHAR(50), ip_adresi VARCHAR(100), enlem FLOAT, boylam FLOAT, konum_hassasiyet FLOAT, baglanti_hatasi INTEGER, alistirma_hata_sayisi INTEGER, alistirma_toplam INTEGER, alistirma_hata_orani FLOAT, baseline_ms INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS katilimci_linkleri (id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER, token TEXT UNIQUE, kullanildi INTEGER, durum TEXT, kullanim_sayisi INTEGER, yeniden_acma_sayisi INTEGER, son_oturum_id TEXT, kullanim_tarihi TEXT, olusturma_tarihi TEXT)") if self.db_type == "sqlite" else c.execute("CREATE TABLE IF NOT EXISTS katilimci_linkleri (id INT AUTO_INCREMENT PRIMARY KEY, proje_id INTEGER, token VARCHAR(100) UNIQUE, kullanildi INTEGER, durum VARCHAR(50), kullanim_sayisi INTEGER, yeniden_acma_sayisi INTEGER, son_oturum_id VARCHAR(100), kullanim_tarihi VARCHAR(50), olusturma_tarihi VARCHAR(50))")
        c.execute("CREATE TABLE IF NOT EXISTS kullanicilar (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, ad_soyad TEXT, rol TEXT, olusturma_tarihi TEXT)") if self.db_type == "sqlite" else c.execute("CREATE TABLE IF NOT EXISTS kullanicilar (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(100) UNIQUE, password_hash VARCHAR(255), ad_soyad VARCHAR(255), rol VARCHAR(50), olusturma_tarihi VARCHAR(50))")
        c.execute("CREATE TABLE IF NOT EXISTS mcrt_secenekler (id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER, metin TEXT, resim_dosya TEXT, sira INTEGER)") if self.db_type == "sqlite" else c.execute("CREATE TABLE IF NOT EXISTS mcrt_secenekler (id INT AUTO_INCREMENT PRIMARY KEY, proje_id INTEGER, metin VARCHAR(255), resim_dosya VARCHAR(255), sira INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS mcrt_cevaplar (id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER, katilimci_id TEXT, oturum_id TEXT, marka_id INTEGER, ifade_id INTEGER, secilen_secenek_id INTEGER, cevap_metin TEXT, sure_ms INTEGER, tarih TEXT, baseline_ms INTEGER, is_alistirma INTEGER)") if self.db_type == "sqlite" else c.execute("CREATE TABLE IF NOT EXISTS mcrt_cevaplar (id INT AUTO_INCREMENT PRIMARY KEY, proje_id INTEGER, katilimci_id VARCHAR(100), oturum_id VARCHAR(100), marka_id INTEGER, ifade_id INTEGER, secilen_secenek_id INTEGER, cevap_metin VARCHAR(255), sure_ms INTEGER, tarih VARCHAR(50), baseline_ms INTEGER, is_alistirma INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS login_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, ip_address TEXT, attempts INTEGER, last_attempt TEXT, lockout_until TEXT)") if self.db_type == "sqlite" else c.execute("CREATE TABLE IF NOT EXISTS login_attempts (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(100), ip_address VARCHAR(100), attempts INTEGER, last_attempt VARCHAR(50), lockout_until VARCHAR(50))")
        conn.commit()
        conn.close()
    def kullanici_olustur(self, username, password_hash, ad_soyad="", rol="admin"):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        tarih = datetime.now().isoformat()
        p = self._p()
        try:
            c.execute(
                f"INSERT INTO kullanicilar (username, password_hash, ad_soyad, rol, olusturma_tarihi) VALUES ({p},{p},{p},{p},{p})",
                (username, password_hash, ad_soyad, rol, tarih)
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def kullanici_dogrula(self, username):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT * FROM kullanicilar WHERE username={p}", (username,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    # --- BRUTE FORCE PROTECTION ---

    def check_login_lockout(self, username, ip):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        tarih_simdi = datetime.now().isoformat()
        
        # KullanÄ±cÄ± adÄ± veya IP bazlÄ± kontrol
        c.execute(f"""
            SELECT * FROM login_attempts 
            WHERE (username={p} OR ip_address={p}) 
            AND lockout_until > {p}
            LIMIT 1
        """, (username, ip, tarih_simdi))
        
        lock = c.fetchone()
        conn.close()
        
        if lock:
            return dict(lock)
        return None

    def track_login_attempt(self, username, ip, success):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        tarih_simdi = datetime.now().isoformat()
        
        if success:
            # BaÅŸarÄ±lÄ± giriÅŸte denemeleri sÄ±fÄ±rla
            c.execute(f"DELETE FROM login_attempts WHERE username={p} OR ip_address={p}", (username, ip))
        else:
            # BaÅŸarÄ±sÄ±z giriÅŸte artÄ±r
            c.execute(f"SELECT * FROM login_attempts WHERE username={p} OR ip_address={p} LIMIT 1", (username, ip))
            row = c.fetchone()
            
            if row:
                attempts = row['attempts'] + 1
                lockout_until = None
                
                # 5 denemeden sonra 15 dakika kilitle
                if attempts >= 5:
                    from datetime import timedelta
                    lockout_until = (datetime.now() + timedelta(minutes=15)).isoformat()
                
                c.execute(f"""
                    UPDATE login_attempts 
                    SET attempts={p}, last_attempt={p}, lockout_until={p} 
                    WHERE id={p}
                """, (attempts, tarih_simdi, lockout_until, row['id']))
            else:
                c.execute(f"""
                    INSERT INTO login_attempts (username, ip_address, attempts, last_attempt) 
                    VALUES ({p}, {p}, 1, {p})
                """, (username, ip, tarih_simdi))
        
        conn.commit()
        conn.close()

    # ========================
    # PROJE CRUD
    # ========================

    def proje_olustur(self, ad, aciklama="", bilgilendirme=""):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        kod = uuid.uuid4().hex[:8]
        tarih = datetime.now().isoformat()
        p = self._p()
        c.execute(
            f"INSERT INTO projeler (ad, aciklama, durum, benzersiz_kod, olusturma_tarihi, katilimci_bilgilendirme, soru_randomize) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (ad, aciklama, "taslak", kod, tarih, bilgilendirme, 0)
        )
        conn.commit()
        proje_id = c.lastrowid
        conn.close()
        return proje_id, kod

    def proje_guncelle(self, proje_id, ad=None, aciklama=None, bilgilendirme=None, alistirma_aktif=None, soru_randomize=None, hedef_orneklem=None, test_turu=None, mcrt_kurgu=None, mcrt_yerlesim=None, panel_complete_url=None, panel_screenout_url=None, panel_quotafull_url=None):
        updates = []
        params = []
        p = self._p()

        fields = [
            ("ad", ad),
            ("aciklama", aciklama),
            ("katilimci_bilgilendirme", bilgilendirme),
            ("alistirma_aktif", 1 if alistirma_aktif is True else (0 if alistirma_aktif is False else None)),
            ("soru_randomize", 1 if soru_randomize is True else (0 if soru_randomize is False else None)),
            ("hedef_orneklem", hedef_orneklem),
            ("test_turu", test_turu),
            ("mcrt_kurgu", mcrt_kurgu),
            ("mcrt_yerlesim", mcrt_yerlesim),
            ("panel_complete_url", panel_complete_url),
            ("panel_screenout_url", panel_screenout_url),
            ("panel_quotafull_url", panel_quotafull_url)
        ]

        for field, value in fields:
            if value is not None:
                updates.append(f"{field}={p}")
                params.append(value)

        if not updates:
            return

        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        params.append(proje_id)
        sorgu = f"UPDATE projeler SET {', '.join(updates)} WHERE id={p}"
        c.execute(sorgu, params)
        conn.commit()
        conn.close()

    def proje_durum_degistir(self, proje_id, yeni_durum):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"UPDATE projeler SET durum={p} WHERE id={p}", (yeni_durum, proje_id))
        conn.commit()
        conn.close()

    def proje_getir(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT * FROM projeler WHERE id={p}", (proje_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def proje_kod_ile_getir(self, kod):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT * FROM projeler WHERE benzersiz_kod={p}", (kod,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def tum_projeler(self, include_archived=True):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        if include_archived:
            c.execute("SELECT * FROM projeler ORDER BY olusturma_tarihi DESC")
        else:
            p = self._p()
            c.execute(f"SELECT * FROM projeler WHERE durum != {p} ORDER BY olusturma_tarihi DESC", ("arsiv",))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def proje_sil(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"DELETE FROM projeler WHERE id={p}", (proje_id,))
        conn.commit()
        conn.close()

    # ========================
    # MARKA CRUD
    # ========================

    def marka_ekle(self, proje_id, ad, resim_dosya="", is_noise=0, analiz_etiketi=""):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT COALESCE(MAX(sira),0)+1 as sira FROM markalar WHERE proje_id={p}", (proje_id,))
        row = c.fetchone()
        sira = row['sira'] if self.db_type == "mysql" else row[0]
        c.execute(
            f"INSERT INTO markalar (proje_id, ad, resim_dosya, is_noise, sira, analiz_etiketi) VALUES ({p},{p},{p},{p},{p},{p})",
            (proje_id, ad, resim_dosya, 1 if is_noise else 0, sira, analiz_etiketi if analiz_etiketi else None)
        )
        conn.commit()
        marka_id = c.lastrowid
        conn.close()
        return marka_id

    def marka_sil(self, marka_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"DELETE FROM markalar WHERE id={p}", (marka_id,))
        conn.commit()
        conn.close()

    def proje_markalari(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT * FROM markalar WHERE proje_id={p} ORDER BY sira", (proje_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ========================
    # IFADE CRUD
    # ========================

    def ifade_ekle(self, proje_id, metin, kategori="", resim_dosya=""):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT COALESCE(MAX(sira),0)+1 as sira FROM ifadeler WHERE proje_id={p}", (proje_id,))
        row = c.fetchone()
        sira = row['sira'] if self.db_type == "mysql" else row[0]
        c.execute(
            f"INSERT INTO ifadeler (proje_id, metin, kategori, resim_dosya, sira) VALUES ({p},{p},{p},{p},{p})",
            (proje_id, metin, kategori or "", resim_dosya, sira)
        )
        conn.commit()
        ifade_id = c.lastrowid
        conn.close()
        return ifade_id

    def ifade_sil(self, ifade_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"DELETE FROM ifadeler WHERE id={p}", (ifade_id,))
        conn.commit()
        conn.close()

    def proje_ifadeleri(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT * FROM ifadeler WHERE proje_id={p} ORDER BY sira", (proje_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ========================
    # CEVAP KAYIT
    # ========================

    def oturum_mevcut_mu(self, oturum_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT COUNT(*) as sayi FROM cevaplar WHERE oturum_id={p}", (oturum_id,))
        res = c.fetchone()
        sayi = res['sayi'] if self.db_type == "mysql" else res[0]
        conn.close()
        return sayi > 0

    def oturum_baslat(self, proje_id, oturum_id, profil_verisi, token=None):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        tarih = datetime.now().isoformat()
        p = self._p()
        
        # 1. Linki Yak (Token varsa)
        if token:
            c.execute(
                f"""UPDATE katilimci_linkleri
                    SET kullanildi=1,
                        kullanim_tarihi={p},
                        durum='basladi',
                        kullanim_sayisi=COALESCE(kullanim_sayisi, 0) + 1,
                        son_oturum_id={p}
                    WHERE token={p} AND proje_id={p} AND kullanildi=0""",
                (tarih, oturum_id, token, proje_id)
            )
            if c.rowcount != 1:
                conn.rollback()
                conn.close()
                raise ValueError("Gecersiz veya daha once kullanilmis katilimci tokeni.")
            
        # 2. Profili 'yarim_kaldi' olarak baslat
        c.execute(f"""
            INSERT INTO katilimci_profilleri 
            (oturum_id, proje_id, ad_soyad, yas, cinsiyet, meslek, egitim, ev_durumu, araba_durumu, saglik_durumu, il, ilce, ses_grubu, tarih, cihaz_tipi, panel_pid, tarayici_bilgisi, baslangic_tarihi, durum, ip_adresi, enlem, boylam, konum_hassasiyet)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
        """, (
            oturum_id, proje_id, 
            profil_verisi.get("ad_soyad"), profil_verisi.get("yas"), 
            profil_verisi.get("cinsiyet"), profil_verisi.get("meslek"),
            profil_verisi.get("egitim"), profil_verisi.get("ev_durumu"),
            profil_verisi.get("araba_durumu"), profil_verisi.get("saglik_durumu"),
            profil_verisi.get("il"), profil_verisi.get("ilce"), 
            profil_verisi.get("ses_grubu"), tarih,
            profil_verisi.get("cihaz_tipi", ""), profil_verisi.get("panel_pid", ""),
            profil_verisi.get("tarayici_bilgisi", ""), tarih, 'yarim_kaldi',
            profil_verisi.get("ip_adresi", ""),
            profil_verisi.get("enlem"), profil_verisi.get("boylam"), profil_verisi.get("konum_hassasiyet")
        ))
        conn.commit()
        conn.close()
        return True

    def toplu_cevap_kaydet(self, proje_id, cevap_listesi, katilimci_id, oturum_id, kalite_metrikleri=None):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        tarih = datetime.now().isoformat()
        p = self._p()
        
        # 1. Mevcut profili 'tamamlandi' yap ve kalite metriklerini ekle
        if kalite_metrikleri:
            c.execute(f"""
                UPDATE katilimci_profilleri 
                SET durum='tamamlandi', 
                    bitis_tarihi={p},
                    alistirma_hata_sayisi={p},
                    alistirma_toplam={p},
                    alistirma_hata_orani={p},
                    baseline_ms={p}
                WHERE oturum_id={p}
            """, (
                tarih, 
                kalite_metrikleri.get("alistirma_hata_sayisi", 0),
                kalite_metrikleri.get("alistirma_toplam", 0),
                kalite_metrikleri.get("alistirma_hata_orani", 0),
                kalite_metrikleri.get("baseline_ms", 0),
                oturum_id
            ))
        else:
            c.execute(f"UPDATE katilimci_profilleri SET durum='tamamlandi', bitis_tarihi={p} WHERE oturum_id={p}", (tarih, oturum_id))

        # 2. CevaplarÄ± kaydet
        for item in cevap_listesi:
            # dogru_cevap_mi null ise SQLite'a None olarak gitsin
            dogru_mi = item.get("dogru_cevap_mi")
            if dogru_mi is True: dogru_val = 1
            elif dogru_mi is False: dogru_val = 0
            else: dogru_val = None

            c.execute(f"""
                INSERT INTO cevaplar (proje_id, katilimci_id, marka_id, ifade_id, cevap, sure_ms, tarih, oturum_id, is_alistirma, baseline_ms, dogru_cevap_mi)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (
                proje_id, katilimci_id,
                None if (item.get("is_alistirma") or item.get("marka_id") == 0) else item.get("marka_id"),
                None if (item.get("is_alistirma") or item.get("ifade_id") == 0) else item.get("ifade_id"),
                item.get("cevap"),
                item.get("sure_ms"),
                tarih,
                oturum_id,
                1 if item.get("is_alistirma") else 0,
                item.get("baseline_ms"),
                dogru_val
            ))
        c.execute(
            f"UPDATE katilimci_linkleri SET durum='tamamlandi' WHERE proje_id={p} AND son_oturum_id={p}",
            (proje_id, oturum_id)
        )

        conn.commit()
        conn.close()
        return len(cevap_listesi)

    # ========================
    # MCRT API
    # ========================

    def mcrt_secenek_ekle(self, proje_id, metin, resim_dosya=""):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT COALESCE(MAX(sira),0)+1 as sira FROM mcrt_secenekler WHERE proje_id={p}", (proje_id,))
        row = c.fetchone()
        sira = row['sira'] if self.db_type == "mysql" else row[0]
        c.execute(
            f"INSERT INTO mcrt_secenekler (proje_id, metin, resim_dosya, sira) VALUES ({p},{p},{p},{p})",
            (proje_id, metin, resim_dosya, sira)
        )
        conn.commit()
        secenek_id = c.lastrowid
        conn.close()
        return secenek_id

    def mcrt_secenek_sil(self, secenek_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"DELETE FROM mcrt_secenekler WHERE id={p}", (secenek_id,))
        conn.commit()
        conn.close()

    def proje_mcrt_secenekleri(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT * FROM mcrt_secenekler WHERE proje_id={p} ORDER BY sira", (proje_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def mcrt_toplu_cevap_kaydet(self, proje_id, cevap_listesi, katilimci_id, oturum_id, kalite_metrikleri=None):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        tarih = datetime.now().isoformat()
        p = self._p()
        
        if kalite_metrikleri:
            c.execute(f"""
                UPDATE katilimci_profilleri 
                SET durum='tamamlandi', 
                    bitis_tarihi={p},
                    alistirma_hata_sayisi={p},
                    alistirma_toplam={p},
                    alistirma_hata_orani={p},
                    baseline_ms={p}
                WHERE oturum_id={p}
            """, (
                tarih, 
                kalite_metrikleri.get("alistirma_hata_sayisi", 0),
                kalite_metrikleri.get("alistirma_toplam", 0),
                kalite_metrikleri.get("alistirma_hata_orani", 0),
                kalite_metrikleri.get("baseline_ms", 0),
                oturum_id
            ))
        else:
            c.execute(f"UPDATE katilimci_profilleri SET durum='tamamlandi', bitis_tarihi={p} WHERE oturum_id={p}", (tarih, oturum_id))

        for item in cevap_listesi:
            c.execute(f"""
                INSERT INTO mcrt_cevaplar (proje_id, katilimci_id, oturum_id, marka_id, ifade_id, secilen_secenek_id, cevap_metin, sure_ms, tarih, baseline_ms, is_alistirma)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (
                proje_id, katilimci_id, oturum_id,
                item.get("marka_id"),
                item.get("ifade_id"),
                item.get("secilen_secenek_id") or item.get("secenek_id"),
                item.get("cevap_metin") or item.get("mcrt_yanit") or item.get("cevap"),
                item.get("sure_ms"),
                tarih,
                item.get("baseline_ms"),
                1 if item.get("is_alistirma") else 0
            ))
        c.execute(
            f"UPDATE katilimci_linkleri SET durum='tamamlandi' WHERE proje_id={p} AND son_oturum_id={p}",
            (proje_id, oturum_id)
        )

        conn.commit()
        conn.close()
        return len(cevap_listesi)

    # ========================
    # PROJE VERÄ° ve Ä°STATÄ°STÄ°K
    # ========================

    def proje_verileri(self, proje_id, marka_id=None):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        sorgu = f"""
            SELECT c.id, c.oturum_id, c.katilimci_id,
                   COALESCE(m.analiz_etiketi, m.ad) as marka,
                   i.metin as ifade,
                   COALESCE(i.kategori, '') as kategori,
                   c.cevap, c.sure_ms, c.tarih, c.is_alistirma, c.baseline_ms
            FROM cevaplar c
            LEFT JOIN markalar m ON c.marka_id = m.id
            LEFT JOIN ifadeler i ON c.ifade_id = i.id
            WHERE c.proje_id = {p}
        """
        params = [proje_id]
        if marka_id:
            sorgu += f" AND c.marka_id = {p}"
            params.append(marka_id)
        sorgu += " ORDER BY c.tarih DESC"
        c.execute(sorgu, params)
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def proje_mcrt_verileri_df(self, proje_id):
        conn = self._baglanti_al()
        p = self._p()
        # MCRT verilerini (mcrt_cevaplar tablosundan) Ã§ek
        query = f"""
            SELECT c.id, c.oturum_id, c.katilimci_id,
                   c.marka_id, c.ifade_id,
                   COALESCE(m.analiz_etiketi, m.ad) as marka,
                   COALESCE(i.metin, 'Genel Algi') as ifade,
                   COALESCE(i.kategori, '') as kategori,
                   c.secilen_secenek_id,
                   c.cevap_metin,
                   c.sure_ms, c.tarih, c.is_alistirma, c.baseline_ms
            FROM mcrt_cevaplar c
            LEFT JOIN markalar m ON c.marka_id = m.id
            LEFT JOIN ifadeler i ON c.ifade_id = i.id
            LEFT JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
            WHERE c.proje_id = {p} AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
            ORDER BY c.tarih
        """
        df = pd.read_sql_query(query, conn, params=[proje_id])
        conn.close()
        return df

    def proje_verileri_df(self, proje_id):
        conn = self._baglanti_al()
        p = self._p()
        # TÃ¼m verileri Ã§ek (Filtreleme analiz modÃ¼lÃ¼nde yapÄ±lacak)
        query = f"""
            SELECT c.id, c.oturum_id, c.katilimci_id,
                   COALESCE(m.analiz_etiketi, m.ad) as marka,
                   m.ad as orijinal_ad,
                   m.is_noise,
                   i.metin as ifade,
                   COALESCE(i.kategori, '') as kategori,
                   c.cevap, c.sure_ms, c.tarih, c.marka_id, c.ifade_id,
                   c.is_alistirma, c.baseline_ms, c.dogru_cevap_mi
            FROM cevaplar c
            LEFT JOIN markalar m ON c.marka_id = m.id
            LEFT JOIN ifadeler i ON c.ifade_id = i.id
            LEFT JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
            WHERE c.proje_id = {p} AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
            ORDER BY c.tarih
        """
        df = pd.read_sql_query(query, conn, params=[proje_id])
        conn.close()
        return df

    def proje_katilimci_profilleri_df(self, proje_id):
        conn = self._baglanti_al()
        p = self._p()
        df = pd.read_sql_query(f"""
            SELECT id, oturum_id, ad_soyad, yas, cinsiyet, meslek, egitim, 
                   ev_durumu, araba_durumu, saglik_durumu, il, ilce, ses_grubu, tarih, 
                   cihaz_tipi, tarayici_bilgisi, baslangic_tarihi, bitis_tarihi, 
                   durum, ip_adresi, enlem, boylam, konum_hassasiyet, panel_pid
            FROM katilimci_profilleri
            WHERE proje_id = {p}
            ORDER BY id DESC
        """, conn, params=[proje_id])
        conn.close()
        return df

    def proje_katilimci_analizi(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        
        query = f"""
            SELECT 
                p.oturum_id, 
                MAX(p.ad_soyad) as ad_soyad, 
                MAX(p.yas) as yas, 
                MAX(p.cinsiyet) as cinsiyet, 
                MAX(p.ses_grubu) as ses,
                COUNT(c.id) as toplam,
                ROUND(AVG(c.sure_ms), 0) as avg_hiz,
                SUM(CASE WHEN (CASE WHEN c.baseline_ms > 0 THEN c.baseline_ms ELSE 1000 END - c.sure_ms) > 50 THEN 1 ELSE 0 END) as guclu_sayi
            FROM katilimci_profilleri p
            JOIN cevaplar c ON LOWER(p.oturum_id) = LOWER(c.oturum_id)
            LEFT JOIN markalar m ON c.marka_id = m.id
            WHERE c.proje_id = {p} AND c.is_alistirma = 0 AND (m.is_noise = 0 OR m.is_noise IS NULL)
            GROUP BY p.oturum_id
            ORDER BY guclu_sayi DESC
        """
        try:
            c.execute(query, (proje_id,))
            rows = c.fetchall()
            
            ozetler = []
            for r in rows:
                oid = r['oturum_id'] if r['oturum_id'] else "unknown"
                ozetler.append({
                    "oturum_id": oid,
                    "pid": str(oid)[:8],
                    "ad_soyad": r['ad_soyad'] or "Ä°simsiz",
                    "yas": r['yas'] or 0,
                    "cinsiyet": r['cinsiyet'] or "-",
                    "ses": r['ses'] or "-",
                    "hiz_ms": r['avg_hiz'] if r['avg_hiz'] else 0,
                    "guclu_cevap": r['guclu_sayi'] if r['guclu_sayi'] else 0,
                    "toplam_cevap": r['toplam'] if r['toplam'] else 0
                })
            return ozetler
        except Exception as e:
            print(f"DB Analiz Kritik Hata: {e}")
            return []
        finally:
            conn.close()

    def proje_katilimci_analizi_mcrt(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()

        query = f"""
            SELECT
                p.oturum_id,
                MAX(p.ad_soyad) as ad_soyad,
                MAX(p.yas) as yas,
                MAX(p.cinsiyet) as cinsiyet,
                MAX(p.ses_grubu) as ses,
                COUNT(c.id) as toplam,
                ROUND(AVG(c.sure_ms), 0) as avg_hiz,
                SUM(CASE WHEN (CASE WHEN c.baseline_ms > 0 THEN c.baseline_ms ELSE 1000 END - c.sure_ms) > 50 THEN 1 ELSE 0 END) as guclu_sayi
            FROM katilimci_profilleri p
            JOIN mcrt_cevaplar c ON LOWER(p.oturum_id) = LOWER(c.oturum_id)
            LEFT JOIN markalar m ON c.marka_id = m.id
            WHERE c.proje_id = {p} AND c.is_alistirma = 0 AND (m.is_noise = 0 OR m.is_noise IS NULL)
            GROUP BY p.oturum_id
            ORDER BY guclu_sayi DESC
        """
        try:
            c.execute(query, (proje_id,))
            rows = c.fetchall()

            ozetler = []
            for r in rows:
                oid = r['oturum_id'] if r['oturum_id'] else "unknown"
                ozetler.append({
                    "oturum_id": oid,
                    "pid": str(oid)[:8],
                    "ad_soyad": r['ad_soyad'] or "Ã„Â°simsiz",
                    "yas": r['yas'] or 0,
                    "cinsiyet": r['cinsiyet'] or "-",
                    "ses": r['ses'] or "-",
                    "hiz_ms": r['avg_hiz'] if r['avg_hiz'] else 0,
                    "guclu_cevap": r['guclu_sayi'] if r['guclu_sayi'] else 0,
                    "toplam_cevap": r['toplam'] if r['toplam'] else 0
                })
            return ozetler
        except Exception as e:
            print(f"MCRT DB Analiz Kritik Hata: {e}")
            return []
        finally:
            conn.close()

    def ai_analiz_kaydet(self, proje_id, metin):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"UPDATE projeler SET ai_analiz = {p} WHERE id = {p}", (metin, proje_id))
        conn.commit()
        conn.close()

    def ai_analiz_getir(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(f"SELECT ai_analiz FROM projeler WHERE id = {p}", (proje_id,))
        row = c.fetchone()
        conn.close()
        return row['ai_analiz'] if self.db_type == "mysql" else row[0] if row else None

    def proje_istatistik(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()

        c.execute(f"SELECT test_turu, mcrt_kurgu FROM projeler WHERE id={p}", (proje_id,))
        proje_row = c.fetchone()
        test_turu = ((proje_row['test_turu'] if self.db_type == "mysql" else proje_row[0]) if proje_row else "standart") or "standart"
        mcrt_kurgu = ((proje_row['mcrt_kurgu'] if self.db_type == "mysql" else proje_row[1]) if proje_row else "cift_blok") or "cift_blok"

        if test_turu in ("mcrt", "mrt"):
            from analiz.mcrt_analiz import mcrt_katilimci_kalite_analizi

            c.execute(f"SELECT oturum_id, durum FROM katilimci_profilleri WHERE proje_id={p} AND LOWER(COALESCE(durum,'')) NOT LIKE 'gecersiz%'", (proje_id,))
            profil_rows = c.fetchall()
            profiller = [dict(r) if self.db_type == "mysql" else {"oturum_id": r[0], "durum": r[1]} for r in profil_rows]
            profil_sayisi = len(profiller)

            c.execute(f"""
                SELECT COUNT(*) as sayi
                FROM mcrt_cevaplar c
                JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
                WHERE c.proje_id={p} AND c.is_alistirma=0 AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
            """, (proje_id,))
            res = c.fetchone()
            toplam_cevap = res['sayi'] if self.db_type == "mysql" else res[0]

            c.execute(f"""
                SELECT COUNT(*) as sayi
                FROM mcrt_cevaplar c
                JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
                WHERE c.proje_id={p} AND c.is_alistirma=1 AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
            """, (proje_id,))
            res = c.fetchone()
            kalibrasyon_cevap = res['sayi'] if self.db_type == "mysql" else res[0]

            c.execute(f"""
                SELECT AVG(c.sure_ms) as sayi
                FROM mcrt_cevaplar c
                JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
                WHERE c.proje_id={p} AND c.is_alistirma=0 AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
            """, (proje_id,))
            res = c.fetchone()
            ort_sure = res['sayi'] if self.db_type == "mysql" else res[0]

            c.execute(f"SELECT COUNT(*) as sayi FROM markalar WHERE proje_id={p} AND (is_noise = 0 OR is_noise IS NULL)", (proje_id,))
            res = c.fetchone()
            marka_sayisi = res['sayi'] if self.db_type == "mysql" else res[0]

            c.execute(f"SELECT COUNT(*) as sayi FROM ifadeler WHERE proje_id={p}", (proje_id,))
            res = c.fetchone()
            ifade_sayisi = res['sayi'] if self.db_type == "mysql" else res[0]

            c.execute(f"SELECT COUNT(*) as sayi FROM mcrt_secenekler WHERE proje_id={p}", (proje_id,))
            res = c.fetchone()
            secenek_sayisi = res['sayi'] if self.db_type == "mysql" else res[0]

            kurgu = str(mcrt_kurgu or "cift_blok").strip().lower().replace("-", "_")
            ifade_tabani = ifade_sayisi if ifade_sayisi else secenek_sayisi
            ifade_trial = math.ceil(ifade_tabani / 4) if ifade_tabani > 0 else 0
            marka_trial = math.ceil(marka_sayisi / 4) if marka_sayisi > 0 else 0
            if kurgu == "marka_merkez":
                beklenen_soru = marka_sayisi * ifade_trial
            elif kurgu == "ifade_merkez":
                beklenen_soru = ifade_tabani * marka_trial
            elif kurgu == "cift_blok":
                beklenen_soru = (marka_sayisi * ifade_trial) + (ifade_tabani * marka_trial)
            else:
                beklenen_soru = (marka_sayisi * ifade_trial) + (ifade_tabani * marka_trial)

            c.execute(f"""
                SELECT c.oturum_id, COUNT(*) as cevap_sayisi, AVG(c.sure_ms) as ort_sure,
                       SUM(CASE WHEN c.sure_ms < 250 THEN 1 ELSE 0 END) as hizli_sayi,
                       SUM(CASE WHEN c.sure_ms > 8000 THEN 1 ELSE 0 END) as yavas_sayi,
                       GROUP_CONCAT(c.cevap_metin) as cevaplar
                FROM mcrt_cevaplar c
                LEFT JOIN markalar m ON c.marka_id = m.id
                WHERE c.proje_id={p} AND c.is_alistirma=0 AND (m.is_noise = 0 OR m.is_noise IS NULL)
                GROUP BY c.oturum_id
            """, (proje_id,))
            katilimci_detay = c.fetchall()

            kalite_outlier_oturumlari = set()
            try:
                kalite_df = self.proje_mcrt_verileri_df(proje_id)
                _, kalite_raporu = mcrt_katilimci_kalite_analizi(kalite_df)
                kalite_outlier_oturumlari = {
                    d.get("oturum_id") for d in kalite_raporu.get("detaylar", [])
                    if d.get("durum") == "ELENDI" and d.get("oturum_id")
                }
            except Exception:
                kalite_outlier_oturumlari = set()

            detay_map = {}
            for kd in katilimci_detay:
                oid = kd['oturum_id'] if self.db_type == "mysql" else kd[0]
                detay_map[oid] = dict(kd) if self.db_type == "mysql" else {
                    "oturum_id": kd[0],
                    "cevap_sayisi": kd[1],
                    "ort_sure": kd[2],
                    "hizli_sayi": kd[3],
                    "yavas_sayi": kd[4],
                    "cevaplar": kd[5],
                }

            tamamlanan = 0
            yarim_kalan = 0
            outliers = 0
            baslatilan_cevapsiz = 0
            for profil in profiller:
                kd = detay_map.get(profil['oturum_id'])
                if not kd:
                    baslatilan_cevapsiz += 1
                    continue

                ort = kd['ort_sure'] or 0
                cevap_s = kd['cevap_sayisi'] or 0
                if cevap_s <= 0:
                    baslatilan_cevapsiz += 1
                    continue
                if profil['oturum_id'] in kalite_outlier_oturumlari:
                    outliers += 1
                elif profil.get('durum') == 'tamamlandi':
                    tamamlanan += 1
                else:
                    yarim_kalan += 1

            c.execute(f"SELECT hedef_orneklem FROM projeler WHERE id={p}", (proje_id,))
            res = c.fetchone()
            hedef = (res['hedef_orneklem'] if self.db_type == "mysql" else res[0]) or 0

            conn.close()
            return {
                "katilimci_sayisi": tamamlanan + yarim_kalan + outliers,
                "profil_sayisi": profil_sayisi,
                "toplam_cevap": toplam_cevap,
                "kalibrasyon_sayisi": kalibrasyon_cevap,
                "tamamlanan_anket": tamamlanan,
                "yarim_kalan": yarim_kalan,
                "outliers": outliers,
                "baslatilan_cevapsiz": baslatilan_cevapsiz,
                "hedef_orneklem": hedef,
                "ortalama_sure_ms": round(float(ort_sure), 1) if ort_sure else 0,
                "marka_sayisi": marka_sayisi,
                "ifade_sayisi": ifade_sayisi,
                "mcrt_secenek_sayisi": secenek_sayisi,
                "beklenen_soru_per_kisi": beklenen_soru
            }
        
        from analiz.analiz import katilimci_kalite_analizi

        c.execute(f"SELECT oturum_id, durum FROM katilimci_profilleri WHERE proje_id={p} AND LOWER(COALESCE(durum,'')) NOT LIKE 'gecersiz%'", (proje_id,))
        profil_rows = c.fetchall()
        profiller = [dict(r) if self.db_type == "mysql" else {"oturum_id": r[0], "durum": r[1]} for r in profil_rows]
        profil_sayisi = len(profiller)
        
        c.execute(f"""
            SELECT COUNT(*) as sayi
            FROM cevaplar c
            JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
            WHERE c.proje_id={p} AND c.is_alistirma=0 AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
        """, (proje_id,))
        res = c.fetchone()
        toplam_cevap = res['sayi'] if self.db_type == "mysql" else res[0]
        
        c.execute(f"""
            SELECT COUNT(*) as sayi
            FROM cevaplar c
            JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
            WHERE c.proje_id={p} AND c.is_alistirma=1 AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
        """, (proje_id,))
        res = c.fetchone()
        kalibrasyon_cevap = res['sayi'] if self.db_type == "mysql" else res[0]
        
        c.execute(f"""
            SELECT AVG(c.sure_ms) as sayi
            FROM cevaplar c
            JOIN katilimci_profilleri kp ON LOWER(c.oturum_id) = LOWER(kp.oturum_id)
            WHERE c.proje_id={p} AND c.is_alistirma=0 AND LOWER(COALESCE(kp.durum,'')) NOT LIKE 'gecersiz%'
        """, (proje_id,))
        res = c.fetchone()
        ort_sure = res['sayi'] if self.db_type == "mysql" else res[0]
        
        c.execute(f"SELECT COUNT(*) as sayi FROM markalar WHERE proje_id={p} AND (is_noise = 0 OR is_noise IS NULL)", (proje_id,))
        res = c.fetchone()
        marka_sayisi = res['sayi'] if self.db_type == "mysql" else res[0]
        
        c.execute(f"SELECT COUNT(*) as sayi FROM ifadeler WHERE proje_id={p}", (proje_id,))
        res = c.fetchone()
        ifade_sayisi = res['sayi'] if self.db_type == "mysql" else res[0]

        beklenen_soru = marka_sayisi * ifade_sayisi
        
        c.execute(f"""
            SELECT c.oturum_id, COUNT(*) as cevap_sayisi, AVG(c.sure_ms) as ort_sure 
            FROM cevaplar c
            LEFT JOIN markalar m ON c.marka_id = m.id
            WHERE c.proje_id={p} AND c.is_alistirma=0 AND (m.is_noise = 0 OR m.is_noise IS NULL)
            GROUP BY c.oturum_id
        """, (proje_id,))
        katilimci_detay = c.fetchall()

        kalite_outlier_oturumlari = set()
        try:
            kalite_df = self.proje_verileri_df(proje_id)
            _, kalite_raporu = katilimci_kalite_analizi(kalite_df)
            kalite_outlier_oturumlari = {
                d.get("oturum_id") for d in kalite_raporu.get("detaylar", [])
                if d.get("durum") == "ELENDI" and d.get("oturum_id")
            }
        except Exception:
            kalite_outlier_oturumlari = set()

        detay_map = {}
        for kd in katilimci_detay:
            oid = kd['oturum_id'] if self.db_type == "mysql" else kd[0]
            detay_map[oid] = dict(kd) if self.db_type == "mysql" else {
                "oturum_id": kd[0],
                "cevap_sayisi": kd[1],
                "ort_sure": kd[2],
            }

        tamamlanan = 0
        yarim_kalan = 0
        outliers = 0
        baslatilan_cevapsiz = 0
        
        MIN_THRESHOLD = 300
        MAX_THRESHOLD = 3000

        for profil in profiller:
            kd = detay_map.get(profil['oturum_id'])
            if not kd:
                baslatilan_cevapsiz += 1
                continue

            ort = kd['ort_sure'] or 0
            cevap_s = kd['cevap_sayisi'] or 0
            if cevap_s <= 0:
                baslatilan_cevapsiz += 1
                continue
            if profil['oturum_id'] in kalite_outlier_oturumlari:
                outliers += 1
            elif profil.get('durum') == 'tamamlandi':
                tamamlanan += 1
            else:
                yarim_kalan += 1

        c.execute(f"SELECT hedef_orneklem FROM projeler WHERE id={p}", (proje_id,))
        res = c.fetchone()
        hedef = (res['hedef_orneklem'] if self.db_type == "mysql" else res[0]) or 0

        conn.close()
        return {
            "katilimci_sayisi": tamamlanan + yarim_kalan + outliers,
            "profil_sayisi": profil_sayisi,
            "toplam_cevap": toplam_cevap,
            "kalibrasyon_sayisi": kalibrasyon_cevap,
            "tamamlanan_anket": tamamlanan,
            "yarim_kalan": yarim_kalan,
            "outliers": outliers,
            "baslatilan_cevapsiz": baslatilan_cevapsiz,
            "hedef_orneklem": hedef,
            "ortalama_sure_ms": round(float(ort_sure), 1) if ort_sure else 0,
            "marka_sayisi": marka_sayisi,
            "ifade_sayisi": ifade_sayisi,
            "beklenen_soru_per_kisi": beklenen_soru
        }

    def proje_yedek_verisi(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        
        c.execute(f"SELECT * FROM projeler WHERE id={p}", (proje_id,))
        proje = dict(c.fetchone())
        
        c.execute(f"SELECT * FROM markalar WHERE proje_id={p}", (proje_id,))
        markalar = [dict(r) for r in c.fetchall()]
        
        c.execute(f"SELECT * FROM ifadeler WHERE proje_id={p}", (proje_id,))
        ifadeler = [dict(r) for r in c.fetchall()]
        
        c.execute(f"SELECT * FROM cevaplar WHERE proje_id={p}", (proje_id,))
        cevaplar = [dict(r) for r in c.fetchall()]
        
        c.execute(f"SELECT * FROM katilimci_profilleri WHERE proje_id={p}", (proje_id,))
        profiller = [dict(r) for r in c.fetchall()]
        
        c.execute(f"SELECT * FROM katilimci_linkleri WHERE proje_id={p}", (proje_id,))
        linkler = [dict(r) for r in c.fetchall()]

        c.execute(f"SELECT * FROM mcrt_secenekler WHERE proje_id={p}", (proje_id,))
        mcrt_secenekler = [dict(r) for r in c.fetchall()]

        c.execute(f"SELECT * FROM mcrt_cevaplar WHERE proje_id={p}", (proje_id,))
        mcrt_cevaplar = [dict(r) for r in c.fetchall()]
        
        conn.close()
        
        return {
            "yedek_surumu": 2,
            "proje": proje,
            "markalar": markalar,
            "ifadeler": ifadeler,
            "cevaplar": cevaplar,
            "profiller": profiller,
            "linkler": linkler,
            "mcrt_secenekler": mcrt_secenekler,
            "mcrt_cevaplar": mcrt_cevaplar,
            "yedek_tarihi": datetime.now().isoformat()
        }

    def proje_yedekten_yukle(self, yedek_verisi, dosya_haritasi=None):
        dosya_haritasi = dosya_haritasi or {}
        proje = yedek_verisi.get("proje") or {}
        markalar = yedek_verisi.get("markalar") or []
        ifadeler = yedek_verisi.get("ifadeler") or []
        cevaplar = yedek_verisi.get("cevaplar") or []
        profiller = yedek_verisi.get("profiller") or []
        linkler = yedek_verisi.get("linkler") or []
        mcrt_secenekler = yedek_verisi.get("mcrt_secenekler") or []
        mcrt_cevaplar = yedek_verisi.get("mcrt_cevaplar") or []

        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()

        try:
            yeni_kod = uuid.uuid4().hex[:8]
            yeni_tarih = datetime.now().isoformat()
            geri_yuklenen_durum = proje.get("durum", "taslak")
            if geri_yuklenen_durum == "canli":
                geri_yuklenen_durum = "taslak"

            c.execute(
                f"""INSERT INTO projeler
                    (ad, aciklama, durum, benzersiz_kod, olusturma_tarihi,
                     katilimci_bilgilendirme, alistirma_aktif, soru_randomize,
                     hedef_orneklem, test_turu, panel_complete_url,
                     panel_screenout_url, panel_quotafull_url, ai_analiz,
                     mcrt_kurgu, mcrt_yerlesim)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    (
                        proje.get("ad", "Geri Yuklenen Proje"),
                        proje.get("aciklama", ""),
                        geri_yuklenen_durum,
                        yeni_kod,
                    proje.get("olusturma_tarihi") or yeni_tarih,
                    proje.get("katilimci_bilgilendirme", ""),
                    proje.get("alistirma_aktif", 0),
                    proje.get("soru_randomize", 0),
                    proje.get("hedef_orneklem", 0),
                    proje.get("test_turu", "standart"),
                    proje.get("panel_complete_url"),
                    proje.get("panel_screenout_url"),
                    proje.get("panel_quotafull_url"),
                    proje.get("ai_analiz"),
                    proje.get("mcrt_kurgu", "cift_blok"),
                    proje.get("mcrt_yerlesim", "grid_standart"),
                )
            )
            yeni_proje_id = c.lastrowid

            marka_id_map = {}
            for item in markalar:
                c.execute(
                    f"""INSERT INTO markalar
                        (proje_id, ad, resim_dosya, is_noise, sira, analiz_etiketi)
                        VALUES ({p},{p},{p},{p},{p},{p})""",
                    (
                        yeni_proje_id,
                        item.get("ad", ""),
                        dosya_haritasi.get(item.get("resim_dosya"), item.get("resim_dosya", "")),
                        item.get("is_noise", 0),
                        item.get("sira", 0),
                        item.get("analiz_etiketi"),
                    )
                )
                marka_id_map[item.get("id")] = c.lastrowid

            ifade_id_map = {}
            for item in ifadeler:
                c.execute(
                    f"""INSERT INTO ifadeler
                        (proje_id, metin, kategori, resim_dosya, sira)
                        VALUES ({p},{p},{p},{p},{p})""",
                    (
                        yeni_proje_id,
                        item.get("metin", ""),
                        item.get("kategori", ""),
                        dosya_haritasi.get(item.get("resim_dosya"), item.get("resim_dosya", "")),
                        item.get("sira", 0),
                    )
                )
                ifade_id_map[item.get("id")] = c.lastrowid

            secenek_id_map = {}
            for item in mcrt_secenekler:
                c.execute(
                    f"""INSERT INTO mcrt_secenekler
                        (proje_id, metin, resim_dosya, sira)
                        VALUES ({p},{p},{p},{p})""",
                    (
                        yeni_proje_id,
                        item.get("metin", ""),
                        dosya_haritasi.get(item.get("resim_dosya"), item.get("resim_dosya", "")),
                        item.get("sira", 0),
                    )
                )
                secenek_id_map[item.get("id")] = c.lastrowid

            eski_oturumler = [str((item.get("oturum_id") or "").strip()) for item in profiller if item.get("oturum_id")]
            oturum_id_map = {}
            for eski_oturum in eski_oturumler:
                oturum_id_map[eski_oturum] = f"restore_{uuid.uuid4().hex[:20]}"

            token_map = {}
            for item in linkler:
                eski_token = item.get("token")
                if eski_token:
                    token_map[eski_token] = uuid.uuid4().hex[:12]

            for item in profiller:
                eski_oturum = str((item.get("oturum_id") or "").strip())
                yeni_oturum = oturum_id_map.get(eski_oturum, f"restore_{uuid.uuid4().hex[:20]}")
                c.execute(
                    f"""INSERT INTO katilimci_profilleri
                        (oturum_id, proje_id, ad_soyad, yas, cinsiyet, meslek, il, ilce,
                         egitim, ev_durumu, araba_durumu, saglik_durumu, ses_grubu,
                         cihaz_tipi, panel_pid, tarih, tarayici_bilgisi, baslangic_tarihi,
                         bitis_tarihi, durum, ip_adresi, enlem, boylam, konum_hassasiyet,
                         baglanti_hatasi, alistirma_hata_sayisi, alistirma_toplam,
                         alistirma_hata_orani, baseline_ms)
                        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    (
                        yeni_oturum,
                        yeni_proje_id,
                        item.get("ad_soyad"),
                        item.get("yas"),
                        item.get("cinsiyet"),
                        item.get("meslek"),
                        item.get("il"),
                        item.get("ilce"),
                        item.get("egitim"),
                        item.get("ev_durumu"),
                        item.get("araba_durumu"),
                        item.get("saglik_durumu"),
                        item.get("ses_grubu"),
                        item.get("cihaz_tipi"),
                        item.get("panel_pid"),
                        item.get("tarih"),
                        item.get("tarayici_bilgisi"),
                        item.get("baslangic_tarihi"),
                        item.get("bitis_tarihi"),
                        item.get("durum", "yarim_kaldi"),
                        item.get("ip_adresi"),
                        item.get("enlem"),
                        item.get("boylam"),
                        item.get("konum_hassasiyet"),
                        item.get("baglanti_hatasi", 0),
                        item.get("alistirma_hata_sayisi", 0),
                        item.get("alistirma_toplam", 0),
                        item.get("alistirma_hata_orani", 0),
                        item.get("baseline_ms", 0),
                    )
                )

            for item in linkler:
                eski_token = item.get("token")
                yeni_token = token_map.get(eski_token, uuid.uuid4().hex[:12])
                son_oturum_id = item.get("son_oturum_id")
                c.execute(
                    f"""INSERT INTO katilimci_linkleri
                        (proje_id, token, kullanildi, durum, kullanim_sayisi,
                         yeniden_acma_sayisi, son_oturum_id, kullanim_tarihi, olusturma_tarihi)
                        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    (
                        yeni_proje_id,
                        yeni_token,
                        item.get("kullanildi", 0),
                        item.get("durum", "aktif"),
                        item.get("kullanim_sayisi", 0),
                        item.get("yeniden_acma_sayisi", 0),
                        oturum_id_map.get(str(son_oturum_id).strip(), None) if son_oturum_id else None,
                        item.get("kullanim_tarihi"),
                        item.get("olusturma_tarihi") or yeni_tarih,
                    )
                )

            for item in cevaplar:
                eski_oturum = str((item.get("oturum_id") or "").strip())
                c.execute(
                    f"""INSERT INTO cevaplar
                        (proje_id, katilimci_id, marka_id, ifade_id, cevap, sure_ms, tarih,
                         oturum_id, is_alistirma, baseline_ms, dogru_cevap_mi)
                        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    (
                        yeni_proje_id,
                        item.get("katilimci_id"),
                        marka_id_map.get(item.get("marka_id")),
                        ifade_id_map.get(item.get("ifade_id")),
                        item.get("cevap"),
                        item.get("sure_ms", 0),
                        item.get("tarih") or yeni_tarih,
                        oturum_id_map.get(eski_oturum, eski_oturum),
                        item.get("is_alistirma", 0),
                        item.get("baseline_ms", 0),
                        item.get("dogru_cevap_mi"),
                    )
                )

            for item in mcrt_cevaplar:
                eski_oturum = str((item.get("oturum_id") or "").strip())
                c.execute(
                    f"""INSERT INTO mcrt_cevaplar
                        (proje_id, katilimci_id, oturum_id, marka_id, ifade_id,
                         secilen_secenek_id, cevap_metin, sure_ms, tarih, baseline_ms, is_alistirma)
                        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    (
                        yeni_proje_id,
                        item.get("katilimci_id"),
                        oturum_id_map.get(eski_oturum, eski_oturum),
                        marka_id_map.get(item.get("marka_id")),
                        ifade_id_map.get(item.get("ifade_id")),
                        secenek_id_map.get(item.get("secilen_secenek_id")),
                        item.get("cevap_metin"),
                        item.get("sure_ms", 0),
                        item.get("tarih") or yeni_tarih,
                        item.get("baseline_ms", 0),
                        item.get("is_alistirma", 0),
                    )
                )

            conn.commit()
            return {"proje_id": yeni_proje_id, "kod": yeni_kod, "ad": proje.get("ad", "Geri Yuklenen Proje")}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def proje_explicit_ozet(self, proje_id, filtre=None):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        
        sorgu = f"""
            SELECT COALESCE(m.analiz_etiketi, m.ad) as marka, i.metin as ifade,
                   COUNT(*) as toplam,
                   SUM(CASE WHEN c.cevap='Evet' THEN 1 ELSE 0 END) as evet_sayisi,
                   AVG(c.sure_ms) as ort_sure,
                   AVG(CASE WHEN c.cevap='Evet' THEN c.sure_ms END) as evet_sure,
                   AVG(CASE WHEN c.cevap='HayÄ±r' THEN c.sure_ms END) as hayir_sure,
                   AVG(
                     CASE 
                        WHEN (50 + (((CASE WHEN c.baseline_ms > 0 THEN c.baseline_ms ELSE 1000 END) - c.sure_ms) / 10)) > 100 THEN 100
                        WHEN (50 + (((CASE WHEN c.baseline_ms > 0 THEN c.baseline_ms ELSE 1000 END) - c.sure_ms) / 10)) < 0 THEN 0
                        ELSE (50 + (((CASE WHEN c.baseline_ms > 0 THEN c.baseline_ms ELSE 1000 END) - c.sure_ms) / 10))
                     END
                   ) as implicit_skor
            FROM cevaplar c
            LEFT JOIN markalar m ON c.marka_id = m.id
            LEFT JOIN ifadeler i ON c.ifade_id = i.id
            LEFT JOIN katilimci_profilleri p_prof ON LOWER(c.oturum_id) = LOWER(p_prof.oturum_id)
            WHERE c.proje_id = {p} AND c.is_alistirma = 0 AND (m.is_noise = 0 OR m.is_noise IS NULL)
        """
        params = [proje_id]
        
        if filtre:
            if filtre.get("cinsiyet"):
                sorgu += f" AND p_prof.cinsiyet = {p}"
                params.append(filtre["cinsiyet"])
            if filtre.get("yas_min"):
                sorgu += f" AND p_prof.yas >= {p}"
                params.append(int(filtre["yas_min"]))
            if filtre.get("yas_max"):
                sorgu += f" AND p_prof.yas <= {p}"
                params.append(int(filtre["yas_max"]))
            if filtre.get("ses_grubu"):
                sorgu += f" AND p_prof.ses_grubu = {p}"
                params.append(filtre["ses_grubu"])
            if filtre.get("il"):
                sorgu += f" AND p_prof.il = {p}"
                params.append(filtre["il"])

        sorgu += " GROUP BY m.id, i.metin ORDER BY COALESCE(m.analiz_etiketi, m.ad), i.metin"
        
        c.execute(sorgu, params)
        rows = c.fetchall()
        conn.close()

        sonuc_listesi = []
        for r in rows:
            d = dict(r)
            d['explicit_pct'] = round((d['evet_sayisi'] / d['toplam'] * 100), 1) if d['toplam'] > 0 else 0
            d['ort_sure'] = round(d['ort_sure'], 1) if d['ort_sure'] else 0
            d['evet_sure'] = round(d['evet_sure'], 1) if d['evet_sure'] else 0
            d['hayir_sure'] = round(d['hayir_sure'], 1) if d['hayir_sure'] else 0
            d['fark_ms'] = round(d['hayir_sure'] - d['evet_sure'], 1) if (d['hayir_sure'] and d['evet_sure']) else 0
            d['implicit_skor'] = round(d['implicit_skor'], 1) if d['implicit_skor'] else 0
            sonuc_listesi.append(d)
        return sonuc_listesi

    def katilimci_linki_olustur(self, proje_id, adet):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        tarih = datetime.now().isoformat()
        p = self._p()
        linkler = []
        for _ in range(adet):
            token = uuid.uuid4().hex[:12]
            c.execute(
                f"INSERT INTO katilimci_linkleri (proje_id, token, olusturma_tarihi) VALUES ({p},{p},{p})",
                (proje_id, token, tarih)
            )
            linkler.append(token)
        conn.commit()
        conn.close()
        return linkler

    def katilimci_linkleri_getir(self, proje_id):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(
            f"SELECT * FROM katilimci_linkleri WHERE proje_id={p} ORDER BY id DESC",
            (proje_id,)
        )
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def katilimci_linki_yeniden_ac(self, proje_id, token):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()

        c.execute(
            f"SELECT * FROM katilimci_linkleri WHERE proje_id={p} AND token={p}",
            (proje_id, token)
        )
        row = c.fetchone()
        if not row:
            conn.close()
            raise ValueError("Link bulunamadi.")

        link = dict(row) if self.db_type == "mysql" else {
            "id": row[0],
            "proje_id": row[1],
            "token": row[2],
            "kullanildi": row[3],
            "kullanim_tarihi": row[4] if len(row) > 4 else None,
            "olusturma_tarihi": row[5] if len(row) > 5 else None,
            "durum": row[6] if len(row) > 6 else None,
            "kullanim_sayisi": row[7] if len(row) > 7 else 0,
            "yeniden_acma_sayisi": row[8] if len(row) > 8 else 0,
            "son_oturum_id": row[9] if len(row) > 9 else None,
        }

        son_oturum_id = link.get("son_oturum_id")
        if son_oturum_id:
            c.execute(
                f"""UPDATE katilimci_profilleri
                    SET durum='gecersiz_admin_yeniden_acildi'
                    WHERE proje_id={p} AND oturum_id={p}""",
                (proje_id, son_oturum_id)
            )

        c.execute(
            f"""UPDATE katilimci_linkleri
                SET kullanildi=0,
                    durum='aktif',
                    son_oturum_id=NULL,
                    kullanim_tarihi=NULL,
                    yeniden_acma_sayisi=COALESCE(yeniden_acma_sayisi, 0) + 1
                WHERE proje_id={p} AND token={p}""",
            (proje_id, token)
        )
        conn.commit()
        conn.close()
        return True

    def katilimci_linki_dogrula(self, token):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        c.execute(
            f"SELECT * FROM katilimci_linkleri WHERE token={p} AND kullanildi=0",
            (token,)
        )
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def katilimci_linki_kullanildi_yap(self, token):
        conn = self._baglanti_al()
        c = self._get_cursor(conn)
        p = self._p()
        tarih = datetime.now().isoformat()
        c.execute(
            f"UPDATE katilimci_linkleri SET kullanildi=1, kullanim_tarihi={p} WHERE token={p}",
            (tarih, token)
        )
        conn.commit()
        conn.close()

    # NOT: proje_verileri_df ve proje_katilimci_profilleri_df yukarÄ±da (satÄ±r 548, 569) tanÄ±mlÄ±dÄ±r.
    # Duplike tanÄ±mlamalar kaldÄ±rÄ±ldÄ±.

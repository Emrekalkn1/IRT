"""
Sunucu veritabani migration scripti.
Tablolar yoksa olusturur, eksik kolonlari ekler.
"""
import sqlite3
import os

DB_PATH = '/root/anket_sistemi/veri/anket.db'

# veri klasoru yoksa olustur
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

def tablo_var_mi(tablo):
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tablo,))
    return c.fetchone() is not None

def kolon_var_mi(tablo, kolon):
    if not tablo_var_mi(tablo):
        return False
    c.execute(f"PRAGMA table_info({tablo})")
    return any(r[1] == kolon for r in c.fetchall())

def kolon_ekle(tablo, kolon, tip):
    if not tablo_var_mi(tablo):
        print(f"  ATLANDI: {tablo} tablosu yok (uygulama ilk acilista olusturacak)")
        return
    if kolon_var_mi(tablo, kolon):
        print(f"  Zaten var: {tablo}.{kolon}")
        return
    try:
        c.execute(f"ALTER TABLE {tablo} ADD COLUMN {kolon} {tip}")
        print(f"  Eklendi: {tablo}.{kolon}")
    except Exception as e:
        print(f"  HATA: {tablo}.{kolon} -> {e}")

print("Migration basladi...")

# katilimci_profilleri
kolon_ekle("katilimci_profilleri", "durum", "TEXT DEFAULT 'yarim_kaldi'")
kolon_ekle("katilimci_profilleri", "ip_adresi", "TEXT")
kolon_ekle("katilimci_profilleri", "enlem", "REAL")
kolon_ekle("katilimci_profilleri", "boylam", "REAL")
kolon_ekle("katilimci_profilleri", "konum_hassasiyet", "REAL")

# markalar
kolon_ekle("markalar", "analiz_etiketi", "TEXT")
kolon_ekle("markalar", "is_noise", "INTEGER DEFAULT 0")

conn.commit()
conn.close()
print("Migration tamamlandi.")

# -*- coding: utf-8 -*-
"""
MySQL Veritabanı Güncelleme Aracı - Gelişmiş Versiyon
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

# Proje kök dizini
PROJE_KOK = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJE_KOK, ".env")
load_dotenv(env_path)

def get_db_connection():
    db_name = os.getenv("MYSQL_DB")
    db_user = os.getenv("MYSQL_USER")
    db_host = os.getenv("MYSQL_HOST", "localhost")
    
    print(f"Bağlantı Deneniyor: Host={db_host}, User={db_user}, DB={db_name}")
    
    if not db_name:
        raise ValueError(".env dosyasında MYSQL_DATABASE bulunamadı!")

    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=os.getenv("MYSQL_PASSWORD"),
        database=db_name,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

def column_exists(cursor, table, column):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
        return cursor.fetchone() is not None
    except Exception:
        return False

def add_column(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        print(f"Sütun ekleniyor: {table}.{column}...")
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"  Başarılı.")
        except Exception as e:
            print(f"  Hata: {e}")
    else:
        print(f"Sütun zaten var: {table}.{column}")

def run_migration():
    print("MySQL Migration basliyor...")
    print(f"Dizin: {PROJE_KOK}")
    print(f"ENV Dosyası: {env_path} ({'Var' if os.path.exists(env_path) else 'YOK!'})")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. katilimci_profilleri
        add_column(cursor, "katilimci_profilleri", "alistirma_hata_sayisi", "INT DEFAULT 0")
        add_column(cursor, "katilimci_profilleri", "alistirma_toplam", "INT DEFAULT 0")
        add_column(cursor, "katilimci_profilleri", "alistirma_hata_orani", "INT DEFAULT 0")
        add_column(cursor, "katilimci_profilleri", "baseline_ms", "INT DEFAULT 0")
        add_column(cursor, "katilimci_profilleri", "durum", "VARCHAR(50) DEFAULT 'yarim_kaldi'")
        add_column(cursor, "katilimci_profilleri", "ip_adresi", "VARCHAR(100)")
        add_column(cursor, "katilimci_profilleri", "enlem", "DECIMAL(10, 8)")
        add_column(cursor, "katilimci_profilleri", "boylam", "DECIMAL(11, 8)")
        add_column(cursor, "katilimci_profilleri", "konum_hassasiyet", "DECIMAL(10, 2)")

        # 2. markalar
        add_column(cursor, "markalar", "analiz_etiketi", "TEXT")
        add_column(cursor, "markalar", "is_noise", "INT DEFAULT 0")

        # 3. cevaplar
        add_column(cursor, "cevaplar", "dogru_cevap_mi", "INT NULL")
        add_column(cursor, "cevaplar", "is_alistirma", "INT DEFAULT 0")
        add_column(cursor, "cevaplar", "baseline_ms", "INT DEFAULT 0")

        conn.commit()
        cursor.close()
        conn.close()
        print("MySQL Migration basariyla tamamlandi!")
    except Exception as e:
        print(f"MIGRATION HATASI: {e}")

if __name__ == "__main__":
    run_migration()

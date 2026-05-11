import sqlite3
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    print("🚀 SQLite -> MySQL Veri Tasima Basladi...")
    
    # 1. Baglantilari kur
    sqlite_conn = sqlite3.connect("veri/anket.db")
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        mysql_conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DB", "anket_sistemi")
        )
        mysql_cursor = mysql_conn.cursor()
        print("✅ MySQL Baglantisi Basarili.")
    except Exception as e:
        print(f"❌ MySQL Baglanti Hatasi (Veritabanini XAMPP/PhpMyAdmin üzerinden olusturdugunuzdan emin olun): {e}")
        return

    # Tablo listesi (Sira önemli: Foreign key hatalari olmamasi icin)
    tablolar = [
        "projeler", "markalar", "ifadeler", "katilimci_profilleri", 
        "cevaplar", "katilimci_linkleri", "kullanicilar"
    ]

    for tablo in tablolar:
        print(f"📦 {tablo} tablosu tasiyor...")
        
        # SQLite'dan verileri cek
        sqlite_cursor.execute(f"SELECT * FROM {tablo}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"ℹ️ {tablo} bos, atlandi.")
            continue
            
        # Sütun isimlerini al
        columns = rows[0].keys()
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)
        
        # MySQL'e yaz
        mysql_cursor.execute(f"DELETE FROM {tablo}") # Varsa temizle
        
        insert_query = f"INSERT INTO {tablo} ({col_names}) VALUES ({placeholders})"
        
        data_to_insert = [tuple(row) for row in rows]
        mysql_cursor.executemany(insert_query, data_to_insert)
        
        print(f"✅ {len(rows)} satir {tablo} tablosuna aktarildi.")

    mysql_conn.commit()
    sqlite_conn.close()
    mysql_conn.close()
    print("🏁 Tasima islemi basariyla tamamlandi! Artik projeyi MySQL ile baslatabilirsiniz.")

if __name__ == "__main__":
    migrate()

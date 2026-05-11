import sqlite3
import os

# Veritabanı veri/ klasöründe bulunuyor
db_path = os.path.join("veri", "anket.db")

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Mevcut tabloları listele
    tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Existing tables in {db_path}: {tables}")
    
    table_name = "katilimci_profilleri"
    if table_name not in tables:
        print(f"Table {table_name} NOT FOUND in database!")
    else:
        existing_columns = [row[1] for row in c.execute(f"PRAGMA table_info({table_name})").fetchall()]
        print(f"Existing columns in {table_name}: {existing_columns}")
        
        columns_to_add = [
            ("egitim", "TEXT"),
            ("ev_durumu", "TEXT"),
            ("araba_durumu", "TEXT"),
            ("saglik_durumu", "TEXT"),
            ("cihaz_tipi", "TEXT"),
            ("panel_pid", "TEXT")
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                    print(f"Added column: {col_name}")
                except Exception as e:
                    print(f"Error adding {col_name}: {e}")
            else:
                print(f"Column already exists: {col_name}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()

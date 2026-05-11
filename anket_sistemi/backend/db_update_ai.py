import sqlite3
import os

db_path = os.path.join("veri", "anket.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("ALTER TABLE projeler ADD COLUMN ai_analiz TEXT")
    conn.commit()
    print("AI Analiz sutunu basariyla eklendi.")
except Exception as e:
    print(f"Bilgi: {e}") # Muhtemelen sutun zaten var

conn.close()

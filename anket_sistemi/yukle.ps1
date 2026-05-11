# --- AYARLAR ---
$IP = "213.202.211.21"
$USER = "root"
$REMOTE_PATH = "/root/anket_sistemi"
$LOCAL_PATH = Get-Location

Write-Host "Guncelleme Basliyor: $IP" -ForegroundColor Cyan

# 1. Klasorleri Tek Tek Gonder (VERITABANI VE .ENV HARIC)
Write-Host "Kodlar gonderiliyor..." -ForegroundColor Yellow
scp -r "$LOCAL_PATH\backend" "${USER}@${IP}:${REMOTE_PATH}/"
scp -r "$LOCAL_PATH\static" "${USER}@${IP}:${REMOTE_PATH}/"
scp "$LOCAL_PATH\requirements.txt" "${USER}@${IP}:${REMOTE_PATH}/"
scp "$LOCAL_PATH\run.py" "${USER}@${IP}:${REMOTE_PATH}/"

# 2. Veritabani Migration (Eksik Kolonlari Ekle)
Write-Host "Veritabani migration calistiriliyor..." -ForegroundColor Yellow
$migrationScript = @'
import sqlite3
db_path = "/root/anket_sistemi/veri/anket.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
cols = [
    ("durum", "TEXT DEFAULT \"yarim_kaldi\""),
    ("ip_adresi", "TEXT"),
    ("enlem", "REAL"),
    ("boylam", "REAL"),
    ("konum_hassasiyet", "REAL"),
]
for col, typ in cols:
    try:
        c.execute(f"ALTER TABLE katilimci_profilleri ADD COLUMN {col} {typ}")
        print(f"Eklendi: {col}")
    except Exception as e:
        print(f"Zaten var: {col}")
conn.commit()
conn.close()
print("Migration tamamlandi.")
'@

ssh "${USER}@${IP}" "python3 -c '$migrationScript'"

# 3. Sunucuda Servisi Yeniden Baslat
Write-Host "Sunucu servisi yeniden baslatiliyor..." -ForegroundColor Yellow
ssh "${USER}@${IP}" "systemctl restart anket"

Write-Host "Guncelleme TAMAMLANDI! Veritabanina dokunulmadi." -ForegroundColor Green
pause

@echo off
color 0b
echo =============================================
echo   Sunucu Guncelleme Basliyor...
echo   NOT: .env ve veritabani dosyalari GONDERILMEZ
echo =============================================

:: 1. Kodlari gonder (scratch ve __pycache__ haric)
echo 1/4: Kodlar aktariliyor...

:: Backend (scratch ve pycache haric)
scp backend\app.py root@213.202.211.21:/root/anket_sistemi/backend/
scp backend\database.py root@213.202.211.21:/root/anket_sistemi/backend/
scp backend\__init__.py root@213.202.211.21:/root/anket_sistemi/backend/
scp backend\db_update_ai.py root@213.202.211.21:/root/anket_sistemi/backend/
scp -r backend\templates root@213.202.211.21:/root/anket_sistemi/backend/

:: Static
scp -r static root@213.202.211.21:/root/anket_sistemi/

:: Analiz
scp -r analiz root@213.202.211.21:/root/anket_sistemi/

:: Diger dosyalar
scp requirements.txt root@213.202.211.21:/root/anket_sistemi/
scp run.py root@213.202.211.21:/root/anket_sistemi/
scp migrate.py root@213.202.211.21:/root/anket_sistemi/
scp db_update_mysql.py root@213.202.211.21:/root/anket_sistemi/

:: 2. Sunucuda kutuphaneler ve izinler
echo 2/4: Kutuphaneler yukleniyor ve izinler duzeltiliyor...
ssh root@213.202.211.21 "cd /root/anket_sistemi && ./venv/bin/pip install -r requirements.txt --quiet && chmod 755 /root && chmod -R 755 /root/anket_sistemi"

:: 3. Veritabani migration
echo 3/4: Veritabani migration calistiriliyor (MySQL)...
ssh root@213.202.211.21 "cd /root/anket_sistemi && ./venv/bin/python3 db_update_mysql.py"

:: 4. Pycache temizle ve servisleri restart et
echo 4/4: Servisler yeniden baslatiliyor...
ssh root@213.202.211.21 "find /root/anket_sistemi -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; systemctl daemon-reload && systemctl restart anket && systemctl restart nginx"

echo =============================================
echo   GUNCELLEME TAMAMLANDI!
echo   Gonderilmeyen: .env, veri/, scratch/
echo =============================================
pause

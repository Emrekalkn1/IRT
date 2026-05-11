# -*- coding: utf-8 -*-
"""
Marka Algi Anket Sistemi - Baslama Dosyasi
"""

import webbrowser
import threading
import time
import os
import sys
import io


# Windows konsolunda UTF-8 destek
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Proje kök dizinini sys.path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app


def tarayici_ac():
    """Flask basladiktan sonra tarayiciyi ac"""
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    print("=" * 50)
    print("  Marka Algi Anket Sistemi")
    print("  http://localhost:5000")
    print("  Admin Panel: http://localhost:5000/secure-mrt-admin")
    print("  Auth Path: http://localhost:5000/secure-mrt-auth")
    print("=" * 50)
    print("\nAnket sistemi calisiyor...\n")

    # Tarayıcıyı arka planda aç
    threading.Thread(target=tarayici_ac, daemon=True).start()

    debug_mode = os.getenv("DEBUG", "0") == "1"
    host_ip = os.getenv("HOST", "127.0.0.1")
    app.run(debug=debug_mode, host=host_ip, port=5000, use_reloader=debug_mode)

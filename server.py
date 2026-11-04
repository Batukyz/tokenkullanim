"""
TokenKullanım Yerel Sunucusu
Çalıştırmak için: python server.py
Tarayıcınız otomatik olarak http://localhost:5000 adresinde açılacaktır.
"""

import http.server
import socketserver
import webbrowser
import os

PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"==================================================")
        print(f" TokenKullanım Sunucusu Başlatıldı!")
        print(f" Adres: {url}")
        print(f" Kapatmak için: CTRL + C tuşlarına basın")
        print(f"==================================================")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu durduruldu.")

if __name__ == "__main__":
    main()

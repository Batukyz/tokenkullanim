@echo off
title TokenKullanim
echo ==================================================
echo  TokenKullanim Uygulamasi Baslatiliyor...
echo ==================================================
python server.py
if errorlevel 1 (
    echo Python bulunamadi, dogrudan tarayicida aciliyor...
    start index.html
)
pause

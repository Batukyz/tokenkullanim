# 🪙 TokenKullanım (Desktop Floating HUD & Token Tracker)

[🇹🇷 Türkçe](README.md) | [🇬🇧 English](README.en.md)

Yapay zeka asistanınızı (Antigravity, Gemini, OpenAI vb.) kullanırken **ekranınızın köşesinde daima en üstte duran küçük yüzen bir masaüstü widget'ıdır**. 
Girdiğiniz her promptun ne kadar token harcadığını, modelin kalan kullanım kotasını ve toplam maliyetinizi gerçek zamanlı olarak izler.

---

## 🖥️ Masaüstü Yüzen Mini Widget'ı Başlatma (En Çok Tercih Edilen)

Bilgisayarınızda doğrudan ekranın köşesine yerleşen mini widget'ı başlatmak için:

1. Klasördeki **`start_widget.bat`** dosyasına **çift tıklayın**.
2. Veya terminalde şu komutu çalıştırın:
   ```bash
   pythonw widget.py
   ```

### 🎛️ Mini Widget'ın Özellikleri:
- **Daima En Üstte (Always on Top):** Kod yazarken veya sohbet ederken ekranınızın köşesinde görünür kalır.
- **Sürüklenebilir:** Başlığından tutarak masaüstünüzde istediğiniz yere taşıyabilirsiniz.
- **Canlı Senkronizasyon (Live Auto-Sync):** Antigravity / Gemini oturumunuzdaki canlı verileri anlık okur; prompt gönderdiğiniz anda sayaç otomatik güncellenir.
- **Kompakt Mod:** `—` butonuna basarak sadece kalan yüzdeyi gösteren küçük bir hap görünümüne küçültebilirsiniz.
- **Model ve Kota Ayarları:** `⚙` butonundan kotayı (1M, 2M, 128k vb.) ve modelinizi değiştirebilirsiniz.

---

## 🌐 Web Sürümü (Tarayıcı Paneli)

Daha detaylı grafikler, geçmiş tablosu ve CSV çıktısı almak isterseniz web arayüzünü kullanabilirsiniz:

- **Canlı Web:** 👉 **[https://batukyz.github.io/tokenkullanim/](https://batukyz.github.io/tokenkullanim/)**
- **Yerel Açılış:** Klasördeki `start.bat` veya `index.html` dosyasına çift tıklayın.

---

## 📁 Proje Dosya Yapısı

```
tokenkullanim/
├── widget.py          # Masaüstü yüzen mini widget (Python Tkinter, 0 kurulum)
├── start_widget.bat   # Mini widget'ı konsolsuz başlatan 1-tık çalıştırıcı
├── index.html         # Web paneli ve görsel tokenizer
├── start.bat          # Web panelini tarayıcıda açan başlatıcı
├── README.md          # Türkçe dokümantasyon
└── README.en.md       # İngilizce dokümantasyon
```

---

## 📜 Lisans
MIT License.

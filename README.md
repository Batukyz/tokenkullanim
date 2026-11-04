# 🪙 TokenKullanım (Token Usage & Budget Tracker)

Yapay zeka modellerine (OpenAI GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Flash, DeepSeek-V3 vb.) gönderilen her promptun ne kadar token tükettiğini, model yanıt maliyetini ve kalan bütçe / token kotanızı anlık olarak hesaplayan modern, hafif ve bağımsız bir takip uygulamasıdır.

---

## 🌟 Öne Çıkan Özellikler

1. **Canlı Prompt & Token Sayacı:**
   - Promptunuzu yazarken gerçek zamanlı olarak **Karakter**, **Kelime** ve **Tahmini Token Sayısı** hesaplanır.
   - Türkçe diline ve özel karakterlerine (`ç, ğ, ı, ö, ş, ü`) duyarlı alt-kelime (BPE) tahmin algoritması kullanır.

2. **Görsel Tokenizer (Ayrıştırıcı Önizlemesi):**
   - Yazdığınız metnin dil modeli tarafından kaç token parçasına bölündüğünü görsel çipler (`chips`) halinde inceler.

3. **Kalan Token & Bütçe İlerleme Çubuğu:**
   - Başlangıç kotası belirleyin (Örn: 100K, 500K, 1.000.000, 5M, 10M token veya özel miktar).
   - Harcama yaptıkça dinamik renk değiştiren ilerleme çubuğu (Yeşil → Turuncu → Kırmızı) ile kalan yüzdenizi görün.

4. **Model Fiyatlandırma & Maliyet Tahmini:**
   - **OpenAI:** GPT-4o, GPT-4o-mini, o3-mini, GPT-4 Turbo
   - **Anthropic:** Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
   - **Google:** Gemini 2.0 Flash, Gemini 1.5 Flash, Gemini 1.5 Pro
   - **DeepSeek & Açık Kaynak:** DeepSeek-V3, DeepSeek-R1, Llama 3.3 70B
   - Her modelin 1M girdi/çıktı token fiyatına göre harcanan USD ($) tutarı tam hesaplanır.

5. **Kullanım Geçmişi & CSV Dışa Aktarma:**
   - Gönderilen her prompt; tarih, saat, seçilen model, girdi/çıktı tokenları, toplam harcama ve o andaki kalan bakiye ile yerel hafızaya (`localStorage`) kaydedilir.
   - Tüm geçmişi CSV formatında tek tıkla Excel/Sheets için dışa aktarabilirsiniz.

6. **Karanlık / Aydınlık Mod:**
   - Göz yormayan modern cam efekti (glassmorphism) ve koyu/açık tema desteği.

---

## 🚀 Çalıştırma Yöntemleri

### Yöntem 1: Çift Tıklayarak (En Basit)
Klasördeki [`index.html`](index.html) veya [`start.bat`](start.bat) dosyasına çift tıklayarak tarayıcınızda doğrudan açıp kullanabilirsiniz. Kurulum veya bağımlılık gerektirmez!

### Yöntem 2: Python Yerel Sunucusu ile
Terminalde klasör içine girip şu komutu çalıştırın:
```bash
python server.py
```
Otomatik olarak varsayılan tarayıcınızda `http://localhost:5000` adresi açılacaktır.

---

## 📁 Proje Dosya Yapısı

```
tokenkullanim/
├── index.html        # Ana web uygulaması (HTML, Modern CSS & Vanilla JS)
├── server.py         # Hafif yerel Python sunucusu (İsteğe bağlı)
├── start.bat         # Windows için tek tıkla başlatıcı
├── README.md         # Proje belgelendirmesi
└── .gitignore        # Git görmezden gelme kuralları
```

---

## 📜 Lisans
MIT License. Dilediğiniz gibi geliştirebilir, projelerinizde kullanabilirsiniz.

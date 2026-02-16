# Simple Browser (PySide6 + QtWebEngine)

Bu proje, `PySide6 + QtWebEngine (Chromium)` tabanlı Python odaklı bir masaüstü tarayıcı iskeleti sunar.

## Eklenen ana özellikler

- Sekme yönetimi (yeni sekme, kapatma)
- URL bar + arama motoru fallback (metin girildiğinde arama)
- Geri/ileri/yenile/home navigasyonu
- Kısayollar (`Ctrl+T`, `Ctrl+W`, `Ctrl+L`, `Ctrl+R`)
- Yer imleri (SQLite)
- Geçmiş (SQLite)
- Download manager (Qt download sinyalleri ile)
- Basit reklam engelleme (domain bazlı interceptor)
- Profil, cookie ve cache path yönetimi (`QWebEngineProfile`)
- Ayarlar ekranı (arama motoru şablonu + engelli domain listesi)

> Not: Bu sürüm “tam tarayıcı” yolunda temel altyapıyı kurar. Uzantı sistemi, şifre yöneticisi entegrasyonu, gelişmiş devtools/debug ve gelişmiş download kuyruğu gibi başlıklar için `requirements.txt` içinde önerilen paketler ayrıca listelenmiştir.

## Kurulum

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Çalıştırma

```bash
python browser.py
```

## Dosyalar

- `browser.py`: Ana uygulama
- `requirements.txt`: Çekirdek + önerilen + opsiyonel Python bağımlılıkları

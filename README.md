# Advanced Python Browser (Tkinter)

Bu proje, Python `tkinter` tabanlı, çok sekmeli ve detaylı ayar seçeneklerine sahip gelişmiş bir metin odaklı tarayıcıdır.

## Öne Çıkan Özellikler

- Çoklu sekme yönetimi (yeni sekme, sekme kapatma)
- Geri / ileri / yenile / anasayfa navigasyonu
- URL veya arama sorgusunu otomatik algılama
- Ayarlanabilir:
  - Anasayfa
  - Arama motoru URL şablonu
  - Ağ timeout süresi
  - User-Agent
  - Yazı tipi ailesi ve boyutu
  - Arka plan / yazı rengi
  - Satır kaydırma modu
  - Satır numarası görünürlüğü
- Yer imleri (ekleme, kalıcı kayıt, menüden açma)
- Çerez gösterimi
- Kaynak kod görüntüleme
- Sayfada metin arama ve vurgulama
- Sayfayı dosyaya kaydetme
- Ayarların JSON dosyasına kalıcı kaydı

## Çalıştırma

```bash
python3 browser.py
```

## Dosyalar

- `browser.py`: Ana tarayıcı uygulaması
- `browser_config.json`: Otomatik oluşan ayar dosyası
- `bookmarks.json`: Otomatik oluşan yer imi dosyası

## Not

Bu tarayıcı bir **metin/HTML kaynak görüntüleyici** yaklaşımıyla çalışır; modern web tarayıcılarındaki JavaScript render motoruna sahip değildir.

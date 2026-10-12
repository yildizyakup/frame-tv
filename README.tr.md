# Frame TV

[English](README.md) · **Türkçe**

Bilgisayardan resim seçip Samsung The Frame TV'de Sanat Modu'nda göstermek için küçük bir masaüstü uygulaması.

Resimler TV'ye gönderilmeden önce 4K'ya (3840×2160) hazırlanır: 16:9'a yakın ve geniş resimler ekranı dolduracak şekilde kırpılır, dikey ve kare resimler paspartuyla ortalanır.

## Kurulum

Tkinter'lı Python 3 gerekir (Debian/Ubuntu/Mint'te `sudo apt install python3-tk python3-venv`).

```bash
./install.sh                 # sanal ortam + "Frame TV" menü kısayolu
.venv/bin/python connect.py 192.168.1.50   # ilk eşleştirme: TV'nin IP adresi; TV ekranında "İzin Ver"e basın
```

TV ile bilgisayar aynı ağda olmalı. TV'nin IP adresini TV'de **Ayarlar → Genel → Ağ → Ağ Durumu**'nda bulabilirsin. `connect.py` adresi `settings.json`'a kaydeder; sonraki çalıştırmalarda tekrar yazmana gerek kalmaz (`FRAME_TV_HOST` ortam değişkeni de kullanılabilir). Modemden TV'ye sabit IP vermek önerilir.

## Kullanım

- **Masaüstü uygulaması:** Menüden "Frame TV"yi açın ya da `.venv/bin/python frame_app.py` komutunu çalıştırın. Resim seçin, yerleşimi belirleyin (otomatik, kırp, paspartu), **TV'de Göster**'e basın. Yüklenenler listesinden resimleri tekrar gösterebilir ya da TV'den silebilirsiniz.
- **Toplu yükleme:** `~/Pictures/Samsung Frame Tv` klasörüne attığınız yeni resimleri yükler.
  ```bash
  .venv/bin/python upload.py            # yükle
  .venv/bin/python upload.py --show     # yükle ve sonuncuyu göster
  .venv/bin/python upload.py --dry-run  # sadece hazırla, gönderme
  ```

## Dil

Arayüz İngilizce ve Türkçe destekliyor. İlk açılışta sistem dili kullanılır (Türkçe sistemde Türkçe, diğerlerinde İngilizce), sonra uygulamanın sağ altındaki **Dil** menüsünden değiştirilebilir. Seçim `settings.json` dosyasına kaydedilir ve `upload.py` ile `connect.py` de aynı dili kullanır.

Yeni bir dil eklemek için `i18n.py` içindeki `STRINGS` sözlüğüne aynı anahtarlarla yeni bir bölüm ve `LANGUAGE_NAMES`'e adını ekleyin. Kod, yorumlar ve tanımlayıcılar İngilizce tutulur; kullanıcıya görünen tüm metinler `i18n.py`'den gelir.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `frame_app.py` | tkinter masaüstü uygulaması |
| `upload.py` | Resim hazırlama (`prepare`) ve klasörden toplu yükleme |
| `connect.py` | İlk eşleştirme ve bağlantı testi |
| `i18n.py` | Çeviriler (İngilizce, Türkçe) ve dil seçimi |
| `install.sh` | Sanal ortam ve menü kısayolu kurulumu |
| `tv-token.txt` | TV eşleştirme anahtarı (git'e girmez) |
| `uploaded.json` | Yüklenen dosya → TV içerik kimliği (`MY_F####`) kaydı (git'e girmez) |
| `settings.json` | Seçilen dil (git'e girmez) |

## Notlar

- [`samsungtvws`](https://github.com/xchwarze/samsung-tv-ws-api) kütüphanesi kullanılıyor ve 2024 model QE65LS03D üzerinde test edildi.
- Yüklenen resimler TV'de "Fotoğraflarım" (`MY-C0002`) kategorisine kaydedilir.
- Samsung'un API'si uygulama kaldırmaya ve ağ ayarlarını değiştirmeye izin vermiyor.

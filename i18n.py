"""Translations and language selection.

The language is read from settings.json; if it has not been chosen yet,
the system locale decides (Turkish locales -> "tr", everything else -> "en").
"""
import json
import locale
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE, "settings.json")

DEFAULT_LANGUAGE = "en"
LANGUAGE_NAMES = {"en": "English", "tr": "Türkçe"}

STRINGS = {
    "en": {
        # Desktop app
        "pick": "Choose Image…",
        "no_image": "No image selected yet",
        "tv_checking": "TV: checking…",
        "tv_on": "TV: {name} ✓",
        "tv_standby": "TV: in standby",
        "tv_unreachable": "TV: unreachable ✗",
        "preview_placeholder": "The preview will appear here",
        "layout": "Layout:",
        "fit_auto": "Automatic",
        "fit_crop": "Fill screen (crop)",
        "fit_matte": "Matte",
        "switch_artmode": "Switch to Art Mode",
        "show_on_tv": "Show on TV",
        "uploaded": "Uploaded",
        "show": "Show",
        "delete_from_tv": "Delete from TV",
        "language": "Language:",
        "error": "Error: {error}",
        "dialog_title": "Choose an image to send to the TV",
        "images": "Images",
        "mode_crop": "cropped",
        "mode_matte": "matted",
        "preview_ready": "Original {width}×{height} → 3840×2160, {mode}. Ready, press “Show on TV”.",
        "preparing": "Preparing…",
        "showing_id": "✓ Showing on TV ({content_id})",
        "sending": "Sending to TV… (a 4K image can take 10–20 s)",
        "select_first": "Select an image from the list first.",
        "showing_name": "✓ Showing {name}",
        "connecting": "Connecting to TV…",
        "confirm_delete": "Delete “{name}” from the TV?\n(The file on this computer is not deleted.)",
        "delete_failed": "The TV did not apply the delete; the image is still on the TV",
        "deleted": "✓ {name} deleted from the TV",
        "deleting": "Deleting…",
        # upload.py
        "cli_nothing_new": "No new images to upload.",
        "cli_open_failed": "✗ {name}: could not open ({error})",
        "cli_showing": "Showing in Art Mode: {content_id}",
        # connect.py
        "connect_ok": "Connected, token saved: {saved}",
        "connect_supported": "Art Mode supported: {value}",
        "connect_artmode": "Art Mode on: {value}",
        "connect_current": "Currently shown artwork: {value}",
        "connect_count": "Artworks on the TV: {value}",
    },
    "tr": {
        "pick": "Resim Seç…",
        "no_image": "Henüz resim seçilmedi",
        "tv_checking": "TV: kontrol ediliyor…",
        "tv_on": "TV: {name} ✓",
        "tv_standby": "TV: bekleme modunda",
        "tv_unreachable": "TV: ulaşılamıyor ✗",
        "preview_placeholder": "Önizleme burada görünecek",
        "layout": "Yerleşim:",
        "fit_auto": "Otomatik",
        "fit_crop": "Ekranı doldur (kırp)",
        "fit_matte": "Paspartu",
        "switch_artmode": "Sanat Modu'na geç",
        "show_on_tv": "TV'de Göster",
        "uploaded": "Yüklenenler",
        "show": "Göster",
        "delete_from_tv": "TV'den Sil",
        "language": "Dil:",
        "error": "Hata: {error}",
        "dialog_title": "TV'ye gönderilecek resmi seç",
        "images": "Resimler",
        "mode_crop": "kırpıldı",
        "mode_matte": "paspartulu",
        "preview_ready": "Orijinal {width}×{height} → 3840×2160, {mode}. Hazır, 'TV'de Göster'e basın.",
        "preparing": "Hazırlanıyor…",
        "showing_id": "✓ TV'de gösteriliyor ({content_id})",
        "sending": "TV'ye gönderiliyor… (4K resimde 10-20 sn sürebilir)",
        "select_first": "Önce listeden bir resim seçin.",
        "showing_name": "✓ {name} gösteriliyor",
        "connecting": "TV'ye bağlanılıyor…",
        "confirm_delete": "'{name}' TV'den silinsin mi?\n(Bilgisayardaki dosya silinmez.)",
        "delete_failed": "TV silme isteğini uygulamadı, resim hâlâ TV'de",
        "deleted": "✓ {name} TV'den silindi",
        "deleting": "Siliniyor…",
        "cli_nothing_new": "Yüklenecek yeni görsel yok.",
        "cli_open_failed": "✗ {name}: açılamadı ({error})",
        "cli_showing": "Sanat Modu'nda gösteriliyor: {content_id}",
        "connect_ok": "Bağlantı OK, token kaydedildi: {saved}",
        "connect_supported": "Sanat Modu destekleniyor: {value}",
        "connect_artmode": "Sanat Modu açık mı: {value}",
        "connect_current": "Şu an gösterilen eser: {value}",
        "connect_count": "TV'deki eser sayısı: {value}",
    },
}


def _load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _system_language():
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if value:
            break
    else:
        value = locale.getlocale()[0] or ""
    return "tr" if value.lower().startswith("tr") else DEFAULT_LANGUAGE


def _initial_language():
    lang = _load_settings().get("language")
    return lang if lang in STRINGS else _system_language()


_current = _initial_language()


def get_language():
    return _current


def set_language(lang):
    """Switch the active language and remember it for the next start."""
    global _current
    if lang not in STRINGS:
        raise ValueError(f"Unsupported language: {lang}")
    _current = lang
    settings = _load_settings()
    settings["language"] = lang
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def t(key, **kwargs):
    """Return the translated string for key, falling back to English."""
    text = STRINGS[_current].get(key) or STRINGS[DEFAULT_LANGUAGE][key]
    return text.format(**kwargs) if kwargs else text

"""Klasördeki görselleri 4K'ya hazırlayıp Frame TV'ye yükler.

Kullanım:
    upload.py                 # yeni görselleri yükle
    upload.py --show          # yükledikten sonra sonuncuyu Sanat Modu'nda göster
    upload.py --dry-run       # sadece hazırla, TV'ye gönderme
"""
import io
import json
import os
import sys
import warnings

from PIL import Image, ImageOps
from samsungtvws import SamsungTVWS

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()  # iPhone HEIC fotoğrafları için
except ImportError:
    pass

HOST = "192.168.1.104"
BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE, "tv-token.txt")
STATE_FILE = os.path.join(BASE, "uploaded.json")
SOURCE_DIR = os.path.expanduser("~/Pictures/Samsung Frame Tv")

W, H = 3840, 2160
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".bmp"}
# Bu oran aralığındaki görseller kırpılarak ekranı doldurur (21:9 ultra geniş dahil),
# dikey/kare görseller ve aşırı geniş panoramalar paspartuyla ortalanır
CROP_MIN_RATIO = (W / H) * 0.88
CROP_MAX_RATIO = 2.5
MATTE_COLOR = (238, 235, 228)  # sıcak kırık beyaz


def prepare(path, fit="auto"):
    """fit: "auto" (orana göre), "crop" (ekranı doldur) veya "matte" (paspartu)."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    ratio = img.width / img.height
    crop = CROP_MIN_RATIO <= ratio <= CROP_MAX_RATIO if fit == "auto" else fit == "crop"
    if crop:
        out = ImageOps.fit(img, (W, H), Image.LANCZOS)
        mode = "kırpıldı"
    else:
        # Kenarlarda en az %6 boşluk bırak ki paspartu gibi dursun
        img = ImageOps.contain(img, (int(W * 0.88), int(H * 0.88)), Image.LANCZOS)
        out = Image.new("RGB", (W, H), MATTE_COLOR)
        out.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
        mode = "paspartulu"
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=95, subsampling=0)
    return buf.getvalue(), mode, img.size


def main():
    dry_run = "--dry-run" in sys.argv
    show = "--show" in sys.argv

    state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
    files = sorted(
        f for f in os.listdir(SOURCE_DIR)
        if os.path.splitext(f)[1].lower() in EXTS and f not in state
    )
    if not files:
        print("Yüklenecek yeni görsel yok.")
        return

    art = None
    if not dry_run:
        tv = SamsungTVWS(host=HOST, port=8002, token_file=TOKEN_FILE, name="Claude", timeout=60)
        art = tv.art()

    last_id = None
    for name in files:
        try:
            data, mode, size = prepare(os.path.join(SOURCE_DIR, name))
        except Exception as e:
            print(f"✗ {name}: açılamadı ({e})")
            continue
        info = f"{name}: {size[0]}x{size[1]} → {W}x{H} {mode}, {len(data) / 1e6:.1f} MB"
        if dry_run:
            print("•", info)
            continue
        content_id = art.upload(data, file_type="JPEG", matte="none", portrait_matte="none")
        state[name] = content_id
        json.dump(state, open(STATE_FILE, "w"), indent=2, ensure_ascii=False)
        last_id = content_id
        print(f"✓ {info} → {content_id}")

    if show and last_id:
        art.select_image(last_id, show=True)
        art.set_artmode(True)
        print("Sanat Modu'nda gösteriliyor:", last_id)


if __name__ == "__main__":
    main()

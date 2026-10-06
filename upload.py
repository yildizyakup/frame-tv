"""Prepare the images in the drop folder at 4K and upload them to the Frame TV.

Usage:
    upload.py                 # upload new images
    upload.py --show          # upload, then show the last one in Art Mode
    upload.py --dry-run       # only prepare, do not send to the TV
"""
import io
import json
import os
import sys
import warnings

from PIL import Image, ImageOps
from samsungtvws import SamsungTVWS

from i18n import t

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()  # for iPhone HEIC photos
except ImportError:
    pass

HOST = "192.168.1.104"
BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE, "tv-token.txt")
STATE_FILE = os.path.join(BASE, "uploaded.json")
SOURCE_DIR = os.path.expanduser("~/Pictures/Samsung Frame Tv")

W, H = 3840, 2160
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".bmp"}
# Images within this aspect ratio range are cropped to fill the screen (21:9 ultrawide
# included); portrait/square images and very wide panoramas are centred on a matte
CROP_MIN_RATIO = (W / H) * 0.88
CROP_MAX_RATIO = 2.5
MATTE_COLOR = (238, 235, 228)  # warm off-white


def prepare(path, fit="auto"):
    """Return (jpeg_bytes, mode, original_size) for a 3840x2160 version of the image.

    fit: "auto" (decide by aspect ratio), "crop" (fill the screen) or "matte".
    mode: "crop" or "matte", whichever was applied.
    """
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    original_size = img.size
    ratio = img.width / img.height
    crop = CROP_MIN_RATIO <= ratio <= CROP_MAX_RATIO if fit == "auto" else fit == "crop"
    if crop:
        out = ImageOps.fit(img, (W, H), Image.LANCZOS)
        mode = "crop"
    else:
        # Leave at least 6% around the edges so it reads as a matte
        img = ImageOps.contain(img, (int(W * 0.88), int(H * 0.88)), Image.LANCZOS)
        out = Image.new("RGB", (W, H), MATTE_COLOR)
        out.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
        mode = "matte"
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=95, subsampling=0)
    return buf.getvalue(), mode, original_size


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def connect_art():
    tv = SamsungTVWS(host=HOST, port=8002, token_file=TOKEN_FILE, name="Claude", timeout=60)
    return tv.art()


def main():
    dry_run = "--dry-run" in sys.argv
    show = "--show" in sys.argv

    state = load_state()
    files = sorted(
        f for f in os.listdir(SOURCE_DIR)
        if os.path.splitext(f)[1].lower() in EXTS and f not in state
    )
    if not files:
        print(t("cli_nothing_new"))
        return

    art = None if dry_run else connect_art()

    last_id = None
    for name in files:
        try:
            data, mode, size = prepare(os.path.join(SOURCE_DIR, name))
        except Exception as e:
            print(t("cli_open_failed", name=name, error=e))
            continue
        info = f"{name}: {size[0]}x{size[1]} → {W}x{H} {t('mode_' + mode)}, {len(data) / 1e6:.1f} MB"
        if dry_run:
            print("•", info)
            continue
        content_id = art.upload(data, file_type="JPEG", matte="none", portrait_matte="none")
        state[name] = content_id
        save_state(state)
        last_id = content_id
        print(f"✓ {info} → {content_id}")

    if show and last_id:
        art.select_image(last_id, show=True)
        art.set_artmode(True)
        print(t("cli_showing", content_id=last_id))


if __name__ == "__main__":
    main()

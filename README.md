# Frame TV

**English** · [Türkçe](README.tr.md)

A small Linux desktop app for showing your own pictures in Art Mode on a Samsung The Frame TV.

Pick an image, choose how it should fit, and press **Show on TV**. Before uploading, every image is prepared at 4K (3840×2160): pictures close to 16:9 (up to 21:9 ultrawide) are cropped to fill the screen, while portrait, square and panorama images are centred on a warm off-white mat, like a framed print. iPhone HEIC photos work too.

## Features

- **Desktop app** (Tkinter): pick an image, choose *auto*, *crop* or *mat*, send it and show it in Art Mode
- **Uploaded list**: show a previous upload again or delete it from the TV
- **TV status**: on, standby or unreachable at a glance
- **Batch upload** from a drop folder (`~/Pictures/Samsung Frame Tv`) for the command line
- **English and Turkish UI**, picked from the system language and switchable in the app

## Install

Needs Python 3 with Tkinter (`sudo apt install python3-tk python3-venv` on Debian/Ubuntu/Mint).

```bash
git clone https://github.com/yildizyakup/frame-tv.git
cd frame-tv
./install.sh                                 # virtualenv + "Frame TV" menu entry
.venv/bin/python connect.py 192.168.1.50     # first pairing: your TV's IP; press Allow on the TV
```

The TV and the computer must be on the same network. Find the TV's IP under **Settings → General → Network → Network Status** on the TV. `connect.py` remembers the address in `settings.json`, so you only type it once (the `FRAME_TV_HOST` environment variable works too). Giving the TV a fixed IP in your router keeps it from changing.

## Usage

- **Desktop app:** open "Frame TV" from the menu, or run `.venv/bin/python frame_app.py`.
- **Batch upload:** drop images into `~/Pictures/Samsung Frame Tv`, then
  ```bash
  .venv/bin/python upload.py            # upload new images
  .venv/bin/python upload.py --show     # upload, then show the last one
  .venv/bin/python upload.py --dry-run  # prepare only, don't send
  ```

## Language

The UI starts in the system language (Turkish locales → Turkish, everything else → English) and can be switched from the **Language** menu at the bottom right. The choice is saved in `settings.json` and shared by `upload.py` and `connect.py`.

To add a language, add a section with the same keys to `STRINGS` in `i18n.py` and its name to `LANGUAGE_NAMES`.

## Files kept out of git

`tv-token.txt` (the pairing token), `settings.json` (language and TV address) and `uploaded.json` (local upload log) are created at runtime and ignored by git.

## Built with

[samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) for the TV's WebSocket API, Pillow and pillow-heif for image preparation, Tkinter for the UI.

## License

MIT

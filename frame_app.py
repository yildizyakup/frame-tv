"""Frame TV masaüstü uygulaması: resim seç, önizle, TV'de Sanat Modu'nda göster."""
import html
import io
import json
import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import requests
from PIL import Image, ImageTk
from samsungtvws import SamsungTVWS

import upload  # prepare(), HOST, TOKEN_FILE, STATE_FILE

PREVIEW_W, PREVIEW_H = 768, 432
PICTURES = os.path.expanduser("~/Pictures")
FIT_OPTIONS = [("Otomatik", "auto"), ("Ekranı doldur (kırp)", "crop"), ("Paspartu", "matte")]


def load_state():
    if os.path.exists(upload.STATE_FILE):
        with open(upload.STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(upload.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def connect_art():
    tv = SamsungTVWS(host=upload.HOST, port=8002, token_file=upload.TOKEN_FILE,
                     name="Claude", timeout=60)
    return tv.art()


class App:
    def __init__(self, root):
        self.root = root
        self.path = None
        self.prepared = None  # 4K JPEG bytes
        self.busy = False

        root.title("Frame TV")
        root.minsize(820, 640)

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")
        ttk.Button(top, text="Resim Seç…", command=self.pick).pack(side="left")
        self.file_label = ttk.Label(top, text="Henüz resim seçilmedi", foreground="#666")
        self.file_label.pack(side="left", padx=12)
        self.tv_label = ttk.Label(top, text="TV: kontrol ediliyor…")
        self.tv_label.pack(side="right")

        self.canvas = tk.Canvas(main, width=PREVIEW_W, height=PREVIEW_H,
                                bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(pady=12)
        self.canvas.create_text(PREVIEW_W // 2, PREVIEW_H // 2, fill="#888",
                                text="Önizleme burada görünecek", font=("Sans", 13))

        opts = ttk.Frame(main)
        opts.pack(fill="x")
        ttk.Label(opts, text="Yerleşim:").pack(side="left")
        self.fit = tk.StringVar(value="auto")
        for label, value in FIT_OPTIONS:
            ttk.Radiobutton(opts, text=label, value=value, variable=self.fit,
                            command=self.refresh_preview).pack(side="left", padx=6)
        self.artmode = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Sanat Modu'na geç", variable=self.artmode).pack(side="right")

        self.send_btn = ttk.Button(main, text="TV'de Göster", command=self.send, state="disabled")
        self.send_btn.pack(fill="x", pady=(12, 4), ipady=6)
        self.status = ttk.Label(main, text="", foreground="#444")
        self.status.pack(fill="x")

        ttk.Separator(main).pack(fill="x", pady=12)
        ttk.Label(main, text="Yüklenenler").pack(anchor="w")
        lst = ttk.Frame(main)
        lst.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(lst, height=5)
        self.listbox.pack(side="left", fill="both", expand=True)
        btns = ttk.Frame(lst)
        btns.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(btns, text="Göster", command=self.show_selected).pack(fill="x")
        ttk.Button(btns, text="TV'den Sil", command=self.delete_selected).pack(fill="x", pady=4)
        self.reload_list()

        threading.Thread(target=self.check_tv, daemon=True).start()

    # --- yardımcılar -------------------------------------------------------
    def ui(self, fn, *args):
        self.root.after(0, fn, *args)

    def set_status(self, text):
        self.ui(self.status.config, {"text": text})

    def run_bg(self, work, done=None, busy_text=None):
        if self.busy:
            return
        self.busy = True
        self.send_btn.config(state="disabled")
        if busy_text:
            self.status.config(text=busy_text)

        def target():
            try:
                result = work()
                if done:
                    self.ui(done, result)
            except Exception as e:
                self.set_status(f"Hata: {e}")
            finally:
                self.busy = False
                self.ui(lambda: self.send_btn.config(
                    state="normal" if self.prepared else "disabled"))

        threading.Thread(target=target, daemon=True).start()

    def check_tv(self):
        try:
            d = requests.get(f"http://{upload.HOST}:8001/api/v2/", timeout=3).json()["device"]
            text = f"TV: {html.unescape(d.get('name', 'bağlı'))} ✓" if d.get("PowerState") == "on" else "TV: bekleme modunda"
        except Exception:
            text = "TV: ulaşılamıyor ✗"
        self.ui(self.tv_label.config, {"text": text})

    # --- resim seçme ve önizleme -------------------------------------------
    def pick(self):
        path = None
        if shutil.which("zenity"):
            res = subprocess.run(
                ["zenity", "--file-selection", "--title=TV'ye gönderilecek resmi seç",
                 f"--filename={PICTURES}/",
                 "--file-filter=Resimler | *.jpg *.jpeg *.png *.webp *.heic *.heif *.tif *.tiff *.bmp "
                 "*.JPG *.JPEG *.PNG *.HEIC"],
                capture_output=True, text=True)
            path = res.stdout.strip() or None
        else:
            path = filedialog.askopenfilename(
                initialdir=PICTURES, title="TV'ye gönderilecek resmi seç",
                filetypes=[("Resimler", "*.jpg *.jpeg *.png *.webp *.heic *.tif *.tiff *.bmp")])
        if path:
            self.path = path
            self.file_label.config(text=os.path.basename(path), foreground="")
            self.refresh_preview()

    def refresh_preview(self):
        if not self.path or self.busy:
            return
        self.prepared = None
        path, fit = self.path, self.fit.get()

        def work():
            data, mode, size = upload.prepare(path, fit)
            thumb = Image.open(io.BytesIO(data))
            thumb.thumbnail((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
            return data, mode, size, thumb

        def done(result):
            data, mode, size, thumb = result
            if path != self.path:
                return  # bu arada başka resim seçildi
            self.prepared = data
            self.photo = ImageTk.PhotoImage(thumb)
            self.canvas.delete("all")
            self.canvas.create_image(PREVIEW_W // 2, PREVIEW_H // 2, image=self.photo)
            self.status.config(text=f"Orijinal {size[0]}×{size[1]} → 3840×2160, {mode}. "
                                    f"Hazır, 'TV'de Göster'e basın.")

        self.run_bg(work, done, "Hazırlanıyor…")

    # --- TV işlemleri -------------------------------------------------------
    def send(self):
        if not self.prepared:
            return
        data, name, show_art = self.prepared, os.path.basename(self.path), self.artmode.get()

        def work():
            art = connect_art()
            content_id = art.upload(data, file_type="JPEG", matte="none", portrait_matte="none")
            state = load_state()
            state[name] = content_id
            save_state(state)
            art.select_image(content_id, show=True)
            if show_art:
                art.set_artmode(True)
            return content_id

        def done(content_id):
            self.status.config(text=f"✓ TV'de gösteriliyor ({content_id})")
            self.reload_list()

        self.run_bg(work, done, "TV'ye gönderiliyor… (4K resimde 10-20 sn sürebilir)")

    def reload_list(self):
        self.items = list(load_state().items())
        self.listbox.delete(0, "end")
        for name, cid in reversed(self.items):
            self.listbox.insert("end", f"{name}   [{cid}]")

    def selected_item(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Frame TV", "Önce listeden bir resim seçin.")
            return None
        return list(reversed(self.items))[sel[0]]

    def show_selected(self):
        item = self.selected_item()
        if not item:
            return
        name, cid = item
        show_art = self.artmode.get()

        def work():
            art = connect_art()
            art.select_image(cid, show=True)
            if show_art:
                art.set_artmode(True)

        self.run_bg(work, lambda _: self.status.config(text=f"✓ {name} gösteriliyor"),
                    "TV'ye bağlanılıyor…")

    def delete_selected(self):
        item = self.selected_item()
        if not item:
            return
        name, cid = item
        if not messagebox.askyesno("Frame TV", f"'{name}' TV'den silinsin mi?\n"
                                               "(Bilgisayardaki dosya silinmez.)"):
            return

        def work():
            art = connect_art()
            art.delete(cid)
            # TV'nin listesine tekrar bakarak gerçekten silindiğini doğrula
            if cid in [a.get("content_id") for a in art.available("MY-C0002")]:
                raise RuntimeError("TV silme isteğini uygulamadı, resim hâlâ TV'de")
            state = load_state()
            state.pop(name, None)
            save_state(state)

        def done(_):
            self.status.config(text=f"✓ {name} TV'den silindi")
            self.reload_list()

        self.run_bg(work, done, "Siliniyor…")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()

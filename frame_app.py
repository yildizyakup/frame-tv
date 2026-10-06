"""Frame TV desktop app: choose an image, preview it, show it in Art Mode on the TV."""
import html
import io
import os
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import requests
from PIL import Image, ImageTk

import i18n
import upload
from i18n import t

PREVIEW_W, PREVIEW_H = 768, 432
PICTURES = os.path.expanduser("~/Pictures")
FIT_OPTIONS = ["auto", "crop", "matte"]
IMAGE_PATTERNS = "*.jpg *.jpeg *.png *.webp *.heic *.heif *.tif *.tiff *.bmp"
MY_PHOTOS_CATEGORY = "MY-C0002"


class App:
    def __init__(self, root):
        self.root = root
        self.path = None
        self.prepared = None  # 4K JPEG bytes ready to upload
        self.thumb = None  # preview image, kept so it survives a UI rebuild
        self.busy = False
        # Status texts are stored as callables so they can be re-rendered in a new language
        self.status_text = lambda: ""
        self.tv_text = lambda: t("tv_checking")
        self.fit = tk.StringVar(value="auto")
        self.artmode = tk.BooleanVar(value=True)
        self.main = None
        self.ui_queue = queue.Queue()  # callbacks from worker threads, run on the Tk thread

        root.title("Frame TV")
        root.minsize(820, 680)
        self.build_ui()
        self.poll_ui_queue()
        threading.Thread(target=self.check_tv, daemon=True).start()

    # --- UI ------------------------------------------------------------------
    def build_ui(self):
        """(Re)build every widget in the current language, keeping the app state."""
        if self.main:
            self.main.destroy()
        self.main = main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")
        ttk.Button(top, text=t("pick"), command=self.pick).pack(side="left")
        self.file_label = ttk.Label(top)
        self.file_label.pack(side="left", padx=12)
        self.tv_label = ttk.Label(top)
        self.tv_label.pack(side="right")
        self.render_file_label()

        self.canvas = tk.Canvas(main, width=PREVIEW_W, height=PREVIEW_H,
                                bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(pady=12)
        self.render_preview()

        opts = ttk.Frame(main)
        opts.pack(fill="x")
        ttk.Label(opts, text=t("layout")).pack(side="left")
        for value in FIT_OPTIONS:
            ttk.Radiobutton(opts, text=t("fit_" + value), value=value, variable=self.fit,
                            command=self.refresh_preview).pack(side="left", padx=6)
        ttk.Checkbutton(opts, text=t("switch_artmode"), variable=self.artmode).pack(side="right")

        self.send_btn = ttk.Button(main, text=t("show_on_tv"), command=self.send)
        self.send_btn.pack(fill="x", pady=(12, 4), ipady=6)
        self.update_send_button()
        self.status = ttk.Label(main, foreground="#444")
        self.status.pack(fill="x")

        ttk.Separator(main).pack(fill="x", pady=12)
        ttk.Label(main, text=t("uploaded")).pack(anchor="w")
        lst = ttk.Frame(main)
        lst.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(lst, height=5)
        self.listbox.pack(side="left", fill="both", expand=True)
        btns = ttk.Frame(lst)
        btns.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(btns, text=t("show"), command=self.show_selected).pack(fill="x")
        ttk.Button(btns, text=t("delete_from_tv"), command=self.delete_selected).pack(fill="x", pady=4)
        self.reload_list()

        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(12, 0))
        codes = list(i18n.LANGUAGE_NAMES)
        self.language = ttk.Combobox(bottom, state="readonly", width=10,
                                     values=[i18n.LANGUAGE_NAMES[c] for c in codes])
        self.language.current(codes.index(i18n.get_language()))
        self.language.bind("<<ComboboxSelected>>",
                           lambda _: self.change_language(codes[self.language.current()]))
        self.language.pack(side="right")
        ttk.Label(bottom, text=t("language")).pack(side="right", padx=(0, 6))

        self.render_status()
        self.render_tv()

    def change_language(self, lang):
        if lang == i18n.get_language():
            return
        i18n.set_language(lang)
        # Rebuild after the combobox event finishes, since the combobox itself is destroyed
        self.root.after(0, self.build_ui)

    def render_file_label(self):
        if self.path:
            self.file_label.config(text=os.path.basename(self.path), foreground="")
        else:
            self.file_label.config(text=t("no_image"), foreground="#666")

    def render_preview(self):
        self.canvas.delete("all")
        if self.thumb:
            self.photo = ImageTk.PhotoImage(self.thumb)
            self.canvas.create_image(PREVIEW_W // 2, PREVIEW_H // 2, image=self.photo)
        else:
            self.canvas.create_text(PREVIEW_W // 2, PREVIEW_H // 2, fill="#888",
                                    text=t("preview_placeholder"), font=("Sans", 13))

    def render_status(self):
        self.status.config(text=self.status_text())

    def render_tv(self):
        self.tv_label.config(text=self.tv_text())

    def update_send_button(self):
        self.send_btn.config(state="normal" if self.prepared and not self.busy else "disabled")

    # --- helpers -------------------------------------------------------------
    def ui(self, fn, *args):
        """Schedule fn on the Tk main thread; safe to call from any thread."""
        self.ui_queue.put((fn, args))

    def poll_ui_queue(self):
        while True:
            try:
                fn, args = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            fn(*args)
        self.root.after(50, self.poll_ui_queue)

    def set_status(self, text_fn):
        self.status_text = text_fn
        self.render_status()

    def say(self, key, **kwargs):
        self.set_status(lambda: t(key, **kwargs))

    def run_bg(self, work, done=None, busy_key=None):
        """Run work() in a thread, then done(result) on the main thread."""
        if self.busy:
            return
        self.busy = True
        self.update_send_button()
        if busy_key:
            self.say(busy_key)

        def target():
            try:
                result = work()
                if done:
                    self.ui(done, result)
            except Exception as e:
                # Bind e now: Python deletes it when the except block ends
                self.ui(lambda err=e: self.say("error", error=err))
            finally:
                self.ui(self.finish_bg)

        threading.Thread(target=target, daemon=True).start()

    def finish_bg(self):
        self.busy = False
        self.update_send_button()

    def check_tv(self):
        try:
            device = requests.get(f"http://{upload.HOST}:8001/api/v2/", timeout=3).json()["device"]
            if device.get("PowerState") == "on":
                name = html.unescape(device.get("name", "Frame"))
                text_fn = lambda: t("tv_on", name=name)
            else:
                text_fn = lambda: t("tv_standby")
        except Exception:
            text_fn = lambda: t("tv_unreachable")

        def apply():
            self.tv_text = text_fn
            self.render_tv()

        self.ui(apply)

    # --- choosing and previewing an image ------------------------------------
    def pick(self):
        if shutil.which("zenity"):
            res = subprocess.run(
                ["zenity", "--file-selection", f"--title={t('dialog_title')}",
                 f"--filename={PICTURES}/",
                 f"--file-filter={t('images')} | {IMAGE_PATTERNS} {IMAGE_PATTERNS.upper()}"],
                capture_output=True, text=True)
            path = res.stdout.strip() or None
        else:
            path = filedialog.askopenfilename(
                initialdir=PICTURES, title=t("dialog_title"),
                filetypes=[(t("images"), IMAGE_PATTERNS)])
        if path:
            self.path = path
            self.render_file_label()
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
                return  # another image was chosen in the meantime
            self.prepared, self.thumb = data, thumb
            self.render_preview()
            self.set_status(lambda: t("preview_ready", width=size[0], height=size[1],
                                      mode=t("mode_" + mode)))

        self.run_bg(work, done, "preparing")

    # --- TV actions ----------------------------------------------------------
    def send(self):
        if not self.prepared:
            return
        data, name, show_art = self.prepared, os.path.basename(self.path), self.artmode.get()

        def work():
            art = upload.connect_art()
            content_id = art.upload(data, file_type="JPEG", matte="none", portrait_matte="none")
            state = upload.load_state()
            state[name] = content_id
            upload.save_state(state)
            art.select_image(content_id, show=True)
            if show_art:
                art.set_artmode(True)
            return content_id

        def done(content_id):
            self.say("showing_id", content_id=content_id)
            self.reload_list()

        self.run_bg(work, done, "sending")

    def reload_list(self):
        # Newest first
        self.items = list(reversed(upload.load_state().items()))
        self.listbox.delete(0, "end")
        for name, content_id in self.items:
            self.listbox.insert("end", f"{name}   [{content_id}]")

    def selected_item(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Frame TV", t("select_first"))
            return None
        return self.items[selection[0]]

    def show_selected(self):
        item = self.selected_item()
        if not item:
            return
        name, content_id = item
        show_art = self.artmode.get()

        def work():
            art = upload.connect_art()
            art.select_image(content_id, show=True)
            if show_art:
                art.set_artmode(True)

        self.run_bg(work, lambda _: self.say("showing_name", name=name), "connecting")

    def delete_selected(self):
        item = self.selected_item()
        if not item:
            return
        name, content_id = item
        if not messagebox.askyesno("Frame TV", t("confirm_delete", name=name)):
            return

        def work():
            art = upload.connect_art()
            art.delete(content_id)
            # Check the TV's list again to make sure the image is really gone
            remaining = [a.get("content_id") for a in art.available(MY_PHOTOS_CATEGORY)]
            if content_id in remaining:
                raise RuntimeError(t("delete_failed"))
            state = upload.load_state()
            state.pop(name, None)
            upload.save_state(state)

        def done(_):
            self.say("deleted", name=name)
            self.reload_list()

        self.run_bg(work, done, "deleting")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()

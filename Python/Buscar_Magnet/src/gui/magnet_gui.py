"""GUI Buscar_Magnet (tkinter): solo presentación y eventos.

Roles delegados: lang/i18n.py (textos), themes/theme.py (estilos),
config.py (persistencia), core/workers.py (hilos).
Uso: ./run.sh (o run.bat) / python src/gui/magnet_gui.py
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
sys.path.insert(0, os.path.join(BASE, 'src'))

from config import save_json, load_config, save_config
from lang.i18n import Language
from themes.theme import apply_theme
from core.workers import search_magnets, verify_magnets


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        cfg = load_config()
        self.language = Language(cfg.get("lang", ""))
        self.dark = cfg.get("dark", False)
        self._engine_code = "sync"
        self.queue = queue.Queue()
        self.results = {}
        self.geometry("700x520")
        self.minsize(520, 360)
        self._build()
        self._apply_all()
        self.url_entry.insert(0, cfg.get("url", ""))
        self.after(100, self._drain)

    def tr(self, key, **kwargs):
        return self.language.tr(key, **kwargs)

    def _build(self):
        menubar = tk.Menu(self, tearoff=0)
        self._menubar = menubar
        self.menu_file = tk.Menu(menubar, tearoff=0)
        self.menu_file.add_command(label="", command=self.destroy)
        menubar.add_cascade(menu=self.menu_file)
        self.menu_view = tk.Menu(menubar, tearoff=0)
        self.dark_var = tk.BooleanVar(value=self.dark)
        self.menu_view.add_checkbutton(label="", variable=self.dark_var,
                                       command=self._toggle_theme)
        menubar.add_cascade(menu=self.menu_view)
        self.menu_lang = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(menu=self.menu_lang)
        self.menu_help = tk.Menu(menubar, tearoff=0)
        self.menu_help.add_command(label="", command=self._about)
        menubar.add_cascade(menu=self.menu_help)
        self.config(menu=menubar)

        form = ttk.Frame(self)
        form.pack(fill=tk.X, padx=8, pady=8)
        self.lbl_url = ttk.Label(form)
        self.lbl_url.grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(form, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW)
        self.lbl_depth = ttk.Label(form)
        self.lbl_depth.grid(row=1, column=0, sticky=tk.W)
        self.depth_entry = ttk.Entry(form, width=6)
        self.depth_entry.insert(0, "2")
        self.depth_entry.grid(row=1, column=1, sticky=tk.W)
        self.lbl_engine = ttk.Label(form)
        self.lbl_engine.grid(row=1, column=2, sticky=tk.W)
        self.engine_combo = ttk.Combobox(form, width=14, state="readonly")
        self.engine_combo.grid(row=1, column=3, sticky=tk.W)
        self.lbl_user = ttk.Label(form)
        self.lbl_user.grid(row=2, column=0, sticky=tk.W)
        self.user_entry = ttk.Entry(form, width=20)
        self.user_entry.grid(row=2, column=1, sticky=tk.W)
        self.lbl_pass = ttk.Label(form)
        self.lbl_pass.grid(row=2, column=2, sticky=tk.W)
        self.pass_entry = ttk.Entry(form, width=20, show="*")
        self.pass_entry.grid(row=2, column=3, sticky=tk.W)
        form.columnconfigure(1, weight=1)

        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=8)
        self.btn_search = ttk.Button(bar, command=self.search)
        self.btn_search.pack(side=tk.LEFT, padx=4)
        self.btn_verify = ttk.Button(bar, command=self.verify)
        self.btn_verify.pack(side=tk.LEFT, padx=4)
        self.btn_save = ttk.Button(bar, command=self.save)
        self.btn_save.pack(side=tk.LEFT, padx=4)
        self.btn_exit = ttk.Button(bar, command=self.destroy)
        self.btn_exit.pack(side=tk.LEFT, padx=4)

        self.list_items = tk.Listbox(self)
        self.list_items.pack(fill=tk.BOTH, expand=True, padx=8)

        self.log = tk.Text(self, height=6, state=tk.DISABLED)
        self.log.pack(fill=tk.X, padx=8, pady=8)
        self.status = tk.Label(self, anchor=tk.W)
        self.status.pack(fill=tk.X, padx=8, pady=(0, 8))

    # ---------- idioma y tema ----------

    def _apply_all(self):
        t = self.tr
        self.title(t("title"))
        for i, key in enumerate(("menu.file", "menu.view", "menu.language", "menu.help")):
            self._menubar.entryconfig(i, label=t(key))
        self.menu_file.entryconfig(0, label=t("action.exit"))
        self.menu_view.entryconfig(0, label=t("action.dark"))
        self.menu_help.entryconfig(0, label=t("action.about"))
        self.menu_lang.delete(0, tk.END)
        self._lang_var = tk.StringVar(value=self.language.current)
        for code in self.language.available():
            self.menu_lang.add_radiobutton(
                label=self.language.name(code), variable=self._lang_var,
                value=code, command=lambda c=code: self._set_lang(c))
        self.lbl_url.config(text=t("url"))
        self.lbl_depth.config(text=t("depth"))
        self.lbl_engine.config(text=t("engine"))
        self.engine_combo.config(values=[t("eng.sync"), t("eng.async")])
        self.engine_combo.current(1 if self._engine_code == "async" else 0)
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine)
        self.lbl_user.config(text=t("user"))
        self.lbl_pass.config(text=t("password"))
        self.btn_search.config(text=t("btn.search"))
        self.btn_verify.config(text=t("btn.verify"))
        self.btn_save.config(text=t("btn.save"))
        self.btn_exit.config(text=t("btn.exit"))
        self._apply_theme()
        self.status.config(text=t("status.ready"))

    def _set_lang(self, code):
        if self.language.set(code):
            save_config({"lang": code})
            self._apply_all()

    def _on_engine(self, _event=None):
        self._engine_code = "async" if self.engine_combo.current() == 1 else "sync"

    def _toggle_theme(self):
        self.dark = self.dark_var.get()
        save_config({"dark": self.dark})
        self._apply_theme()

    def _about(self):
        messagebox.showinfo(self.tr("action.about"), self.tr("msg.about"))

    def _apply_theme(self):
        import tkinter.ttk as _ttk
        apply_theme(self, self.dark, {"log": self.log, "list": self.list_items,
                                      "status": self.status},
                    style=_ttk.Style(self))

    # ---------- trabajo (delega en workers) ----------

    def _write_log(self, text):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

    def _collect(self):
        try:
            depth = int(self.depth_entry.get())
            if depth <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(self.tr("msg.warn"), self.tr("depth"))
            return None
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(self.tr("msg.warn"), self.tr("url"))
            return None
        save_config({"url": url})
        return url, depth

    def search(self):
        params = self._collect()
        if not params:
            return
        self.btn_search.config(state=tk.DISABLED)
        self.btn_verify.config(state=tk.DISABLED)
        self.status.config(text=self.tr("status.running"))
        url, depth = params
        threading.Thread(
            target=search_magnets,
            args=(url, depth, self._engine_code,
                  self.user_entry.get() or None,
                  self.pass_entry.get() or None,
                  self.queue.put),
            daemon=True,
        ).start()

    def verify(self):
        if not self.results:
            messagebox.showwarning(self.tr("msg.warn"), self.tr("msg.no_results"))
            return
        self.btn_search.config(state=tk.DISABLED)
        self.btn_verify.config(state=tk.DISABLED)
        items = list(self.results.items())
        threading.Thread(
            target=verify_magnets,
            args=(items,
                  lambda i, n: self.tr("status.verifying", i=i, n=n),
                  self.queue.put),
            daemon=True,
        ).start()

    def save(self):
        if not self.results:
            messagebox.showwarning(self.tr("msg.warn"), self.tr("msg.no_results"))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                save_json(path, self.results)
            except OSError as e:
                messagebox.showerror(self.tr("msg.error"), str(e))
                return
            self._write_log(self.tr("msg.saved", path=path))

    def _drain(self):
        t = self.tr
        try:
            while True:
                try:
                    kind, payload = self.queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    if kind == "found":
                        self.results = payload
                        self.list_items.delete(0, tk.END)
                        for key in payload:
                            self.list_items.insert(tk.END, key)
                        self._write_log(t("msg.done", n=len(payload)))
                    elif kind == "verified":
                        ok, bad = payload
                        self._write_log(t("msg.verified", ok=ok, bad=len(bad)))
                    elif kind == "progress":
                        i, n = payload
                        self.status.config(text=t("status.verifying", i=i, n=n))
                    elif kind == "error":
                        messagebox.showerror(t("msg.error"), payload)
                    elif kind == "error_libtorrent":
                        messagebox.showerror(
                            t("msg.error"), t("msg.need_lib", cmd=payload))
                    elif kind == "done_search":
                        self.btn_search.config(state=tk.NORMAL)
                        self.status.config(text=t("status.ready"))
                    elif kind == "done_verify":
                        self.btn_verify.config(state=tk.NORMAL)
                        self.status.config(text=t("status.ready"))
                except Exception as e:  # noqa: BLE001 (el polling nunca debe morir)
                    self._write_log(f"ERROR: {e}")
        finally:
            self.after(100, self._drain)


if __name__ == "__main__":
    App().mainloop()

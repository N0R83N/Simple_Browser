import json
import os
import re
import threading
import time
import tkinter as tk
from dataclasses import asdict, dataclass, field
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.parse import quote_plus, urlparse

import http.cookiejar
import urllib.error
import urllib.request


CONFIG_FILE = "browser_config.json"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)


@dataclass
class BrowserSettings:
    homepage: str = "https://example.org"
    search_engine: str = "https://duckduckgo.com/?q={query}"
    timeout: int = 15
    font_family: str = "Consolas"
    font_size: int = 11
    bg_color: str = "#FFFFFF"
    fg_color: str = "#111111"
    auto_wrap_text: bool = True
    show_line_numbers: bool = False
    user_agent: str = DEFAULT_USER_AGENT


@dataclass
class TabState:
    frame: tk.Frame
    url_var: tk.StringVar
    title_var: tk.StringVar
    status_var: tk.StringVar
    content_text: tk.Text
    line_text: tk.Text
    history: list[str] = field(default_factory=list)
    history_index: int = -1
    last_loaded_content: str = ""


class AdvancedPythonBrowser:
    """A customizable, multi-tab, text-centric browser built with Tkinter."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Advanced Python Browser")
        self.root.geometry("1200x800")

        self.settings = self.load_settings()
        self.bookmarks = self.load_bookmarks()

        self.cookie_jar = http.cookiejar.CookieJar()
        self.tabs: dict[str, TabState] = {}

        self.build_ui()
        self.add_tab(url=self.settings.homepage, switch=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.sync_global_status)

        self.status_var = tk.StringVar(value="Hazır")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_bar.pack(fill="x")

        self.create_file_menu()
        self.create_navigation_menu()
        self.create_bookmark_menu()
        self.create_settings_menu()
        self.create_tools_menu()

    def create_file_menu(self) -> None:
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Yeni Sekme", command=lambda: self.add_tab(switch=True))
        file_menu.add_command(label="Sekmeyi Kapat", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Sayfayı Kaydet", command=self.save_current_page)
        file_menu.add_command(label="İçeriği Temizle", command=self.clear_current_content)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.on_close)
        self.menu_bar.add_cascade(label="Dosya", menu=file_menu)

    def create_navigation_menu(self) -> None:
        nav_menu = tk.Menu(self.menu_bar, tearoff=0)
        nav_menu.add_command(label="Geri", command=self.go_back)
        nav_menu.add_command(label="İleri", command=self.go_forward)
        nav_menu.add_command(label="Yenile", command=self.reload_current_tab)
        nav_menu.add_command(label="Anasayfa", command=self.open_homepage)
        self.menu_bar.add_cascade(label="Gezinme", menu=nav_menu)

    def create_bookmark_menu(self) -> None:
        self.bookmark_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.bookmark_menu.add_command(label="Mevcut Sayfayı Yer İmlerine Ekle", command=self.add_bookmark_from_current)
        self.bookmark_menu.add_separator()
        self.rebuild_bookmark_menu()
        self.menu_bar.add_cascade(label="Yer İmleri", menu=self.bookmark_menu)

    def create_settings_menu(self) -> None:
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        settings_menu.add_command(label="Tarayıcı Ayarları", command=self.open_settings_dialog)
        settings_menu.add_command(label="Tema Uygula", command=self.apply_theme_to_all_tabs)
        settings_menu.add_command(label="Satır Numaralarını Aç/Kapat", command=self.toggle_line_numbers)
        self.menu_bar.add_cascade(label="Ayarlar", menu=settings_menu)

    def create_tools_menu(self) -> None:
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Kaynak Kodunu Gör", command=self.show_page_source)
        tools_menu.add_command(label="Sayfada Bul", command=self.find_in_page)
        tools_menu.add_command(label="Çerezleri Göster", command=self.show_cookies)
        self.menu_bar.add_cascade(label="Araçlar", menu=tools_menu)

    def add_tab(self, url: str = "", switch: bool = False) -> None:
        frame = ttk.Frame(self.notebook)
        top_bar = ttk.Frame(frame)
        top_bar.pack(fill="x", padx=8, pady=8)

        title_var = tk.StringVar(value="Yeni Sekme")
        status_var = tk.StringVar(value="Hazır")
        url_var = tk.StringVar(value=url or "")

        back_btn = ttk.Button(top_bar, text="←", width=3, command=self.go_back)
        forward_btn = ttk.Button(top_bar, text="→", width=3, command=self.go_forward)
        reload_btn = ttk.Button(top_bar, text="⟳", width=3, command=self.reload_current_tab)
        home_btn = ttk.Button(top_bar, text="⌂", width=3, command=self.open_homepage)

        back_btn.pack(side="left", padx=2)
        forward_btn.pack(side="left", padx=2)
        reload_btn.pack(side="left", padx=2)
        home_btn.pack(side="left", padx=2)

        url_entry = ttk.Entry(top_bar, textvariable=url_var)
        url_entry.pack(side="left", fill="x", expand=True, padx=6)
        url_entry.bind("<Return>", lambda _e: self.load_from_entry())

        go_btn = ttk.Button(top_bar, text="Git", command=self.load_from_entry)
        stop_btn = ttk.Button(top_bar, text="Durdur", command=lambda: status_var.set("İstek iptal edildi (simülasyon)."))
        go_btn.pack(side="left", padx=2)
        stop_btn.pack(side="left", padx=2)

        body_frame = ttk.Frame(frame)
        body_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        line_text = tk.Text(body_frame, width=5, padx=4, takefocus=0, border=0, background="#F0F0F0", state="disabled")
        content_text = tk.Text(body_frame, wrap="word")
        y_scroll = ttk.Scrollbar(body_frame, orient="vertical", command=self._on_scroll_factory(content_text, line_text))
        x_scroll = ttk.Scrollbar(body_frame, orient="horizontal", command=content_text.xview)
        content_text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        line_text.pack(side="left", fill="y")
        content_text.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")

        content_text.bind("<KeyRelease>", lambda _e: self.update_line_numbers_for_tab(self.current_tab()))
        content_text.bind("<MouseWheel>", lambda _e: self.sync_line_scroll(content_text, line_text))

        tab_state = TabState(
            frame=frame,
            url_var=url_var,
            title_var=title_var,
            status_var=status_var,
            content_text=content_text,
            line_text=line_text,
        )

        self.notebook.add(frame, text=title_var.get())
        tab_id = self.notebook.tabs()[-1]
        self.tabs[tab_id] = tab_state

        self.apply_theme_to_tab(tab_state)
        self.update_line_numbers_for_tab(tab_state)

        if switch:
            self.notebook.select(frame)

        if url:
            self.load_url(url)

    def current_tab_id(self) -> str | None:
        tabs = self.notebook.tabs()
        if not tabs:
            return None
        return self.notebook.select()

    def current_tab(self) -> TabState | None:
        tab_id = self.current_tab_id()
        if not tab_id:
            return None
        return self.tabs.get(tab_id)

    def load_from_entry(self) -> None:
        tab = self.current_tab()
        if not tab:
            return
        self.load_url(tab.url_var.get().strip())

    def normalize_url(self, text: str) -> str:
        text = text.strip()
        if not text:
            return self.settings.homepage

        parsed = urlparse(text)
        if parsed.scheme in {"http", "https"}:
            return text

        if re.match(r"^[\w.-]+\.[a-zA-Z]{2,}(/.*)?$", text):
            return f"https://{text}"

        query = quote_plus(text)
        return self.settings.search_engine.format(query=query)

    def build_opener(self) -> urllib.request.OpenerDirector:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        opener.addheaders = [("User-Agent", self.settings.user_agent)]
        return opener

    def load_url(self, raw_text: str, add_history: bool = True) -> None:
        tab = self.current_tab()
        if not tab:
            return

        target_url = self.normalize_url(raw_text)
        tab.url_var.set(target_url)
        tab.status_var.set("Yükleniyor...")
        self.sync_global_status()

        def worker() -> None:
            started = time.time()
            try:
                opener = self.build_opener()
                with opener.open(target_url, timeout=self.settings.timeout) as response:
                    content_type = response.headers.get("Content-Type", "")
                    raw = response.read()

                text = raw.decode("utf-8", errors="replace")
                elapsed = time.time() - started
                self.root.after(
                    0,
                    lambda: self._handle_loaded_content(
                        tab,
                        target_url,
                        text,
                        content_type,
                        elapsed,
                        add_history,
                    ),
                )
            except urllib.error.HTTPError as err:
                self.root.after(0, lambda: self._handle_error(tab, f"HTTP Hatası: {err.code} - {err.reason}"))
            except urllib.error.URLError as err:
                self.root.after(0, lambda: self._handle_error(tab, f"Ağ Hatası: {err.reason}"))
            except Exception as err:  # noqa: BLE001
                self.root.after(0, lambda: self._handle_error(tab, f"Beklenmeyen Hata: {err}"))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_loaded_content(
        self,
        tab: TabState,
        url: str,
        content: str,
        content_type: str,
        elapsed: float,
        add_history: bool,
    ) -> None:
        tab.content_text.delete("1.0", tk.END)
        tab.content_text.insert(tk.END, content)
        tab.last_loaded_content = content

        title = self.extract_title(content) or url
        tab.title_var.set(title[:40])
        tab.status_var.set(f"Yüklendi: {url} | {content_type or 'Bilinmiyor'} | {elapsed:.2f}s")

        index = self.notebook.index(tab.frame)
        self.notebook.tab(index, text=tab.title_var.get())

        if add_history:
            if tab.history_index < len(tab.history) - 1:
                tab.history = tab.history[: tab.history_index + 1]
            tab.history.append(url)
            tab.history_index = len(tab.history) - 1

        self.update_line_numbers_for_tab(tab)
        self.sync_global_status()

    def _handle_error(self, tab: TabState, message: str) -> None:
        tab.content_text.delete("1.0", tk.END)
        tab.content_text.insert(tk.END, message)
        tab.status_var.set(message)
        self.sync_global_status()

    def extract_title(self, html: str) -> str:
        match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return ""
        return re.sub(r"\s+", " ", match.group(1)).strip()

    def go_back(self) -> None:
        tab = self.current_tab()
        if not tab or tab.history_index <= 0:
            return
        tab.history_index -= 1
        url = tab.history[tab.history_index]
        tab.url_var.set(url)
        self.load_url(url, add_history=False)

    def go_forward(self) -> None:
        tab = self.current_tab()
        if not tab or tab.history_index >= len(tab.history) - 1:
            return
        tab.history_index += 1
        url = tab.history[tab.history_index]
        tab.url_var.set(url)
        self.load_url(url, add_history=False)

    def reload_current_tab(self) -> None:
        tab = self.current_tab()
        if tab:
            self.load_url(tab.url_var.get(), add_history=False)

    def open_homepage(self) -> None:
        self.load_url(self.settings.homepage)

    def close_current_tab(self) -> None:
        tab_id = self.current_tab_id()
        if not tab_id:
            return
        if len(self.notebook.tabs()) == 1:
            messagebox.showinfo("Bilgi", "Son sekme kapatılamaz.")
            return
        self.notebook.forget(tab_id)
        self.tabs.pop(tab_id, None)
        self.sync_global_status()

    def clear_current_content(self) -> None:
        tab = self.current_tab()
        if not tab:
            return
        tab.content_text.delete("1.0", tk.END)
        tab.status_var.set("İçerik temizlendi.")
        self.update_line_numbers_for_tab(tab)
        self.sync_global_status()

    def save_current_page(self) -> None:
        tab = self.current_tab()
        if not tab:
            return

        initial_name = (self.extract_title(tab.last_loaded_content) or "page").replace(" ", "_")
        path = filedialog.asksaveasfilename(
            title="Sayfayı Kaydet",
            defaultextension=".html",
            initialfile=f"{initial_name}.html",
            filetypes=[("HTML", "*.html"), ("Text", "*.txt"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(tab.content_text.get("1.0", tk.END))
            tab.status_var.set(f"Kaydedildi: {path}")
            self.sync_global_status()
        except OSError as err:
            messagebox.showerror("Hata", f"Dosya kaydedilemedi:\n{err}")

    def find_in_page(self) -> None:
        tab = self.current_tab()
        if not tab:
            return

        target = simpledialog.askstring("Bul", "Aranacak metni girin:")
        if not target:
            return

        text = tab.content_text
        text.tag_remove("search_highlight", "1.0", tk.END)

        start = "1.0"
        count = 0
        while True:
            start = text.search(target, start, stopindex=tk.END, nocase=True)
            if not start:
                break
            end = f"{start}+{len(target)}c"
            text.tag_add("search_highlight", start, end)
            start = end
            count += 1

        text.tag_config("search_highlight", background="#FFE08A", foreground="#000000")
        tab.status_var.set(f"'{target}' için {count} sonuç bulundu.")
        self.sync_global_status()

    def show_page_source(self) -> None:
        tab = self.current_tab()
        if not tab:
            return

        source_window = tk.Toplevel(self.root)
        source_window.title(f"Kaynak Kodu - {tab.url_var.get()}")
        source_window.geometry("900x600")

        source_text = tk.Text(source_window, wrap="none")
        source_text.pack(fill="both", expand=True)
        source_text.insert("1.0", tab.last_loaded_content or tab.content_text.get("1.0", tk.END))

    def toggle_line_numbers(self) -> None:
        self.settings.show_line_numbers = not self.settings.show_line_numbers
        self.apply_theme_to_all_tabs()

    def update_line_numbers_for_tab(self, tab: TabState | None) -> None:
        if not tab:
            return
        content = tab.content_text.get("1.0", tk.END)
        line_count = max(content.count("\n"), 1)
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))

        tab.line_text.configure(state="normal")
        tab.line_text.delete("1.0", tk.END)
        tab.line_text.insert("1.0", line_numbers)
        tab.line_text.configure(state="disabled")

    def sync_line_scroll(self, content_text: tk.Text, line_text: tk.Text) -> None:
        line_text.yview_moveto(content_text.yview()[0])

    def _on_scroll_factory(self, content_text: tk.Text, line_text: tk.Text):
        def _scroll(*args):
            content_text.yview(*args)
            line_text.yview(*args)

        return _scroll

    def apply_theme_to_tab(self, tab: TabState) -> None:
        wrap_mode = "word" if self.settings.auto_wrap_text else "none"
        tab.content_text.configure(
            background=self.settings.bg_color,
            foreground=self.settings.fg_color,
            insertbackground=self.settings.fg_color,
            font=(self.settings.font_family, self.settings.font_size),
            wrap=wrap_mode,
        )

        if self.settings.show_line_numbers:
            tab.line_text.pack(side="left", fill="y")
        else:
            tab.line_text.pack_forget()

    def apply_theme_to_all_tabs(self) -> None:
        for tab in self.tabs.values():
            self.apply_theme_to_tab(tab)
            self.update_line_numbers_for_tab(tab)
        self.sync_global_status()

    def open_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Tarayıcı Ayarları")
        dialog.geometry("520x460")
        dialog.transient(self.root)
        dialog.grab_set()

        fields: dict[str, tk.Entry] = {}

        def add_entry(label: str, value: str):
            container = ttk.Frame(dialog)
            container.pack(fill="x", padx=12, pady=6)
            ttk.Label(container, text=label, width=20).pack(side="left")
            entry = ttk.Entry(container)
            entry.insert(0, value)
            entry.pack(side="left", fill="x", expand=True)
            fields[label] = entry

        add_entry("Anasayfa", self.settings.homepage)
        add_entry("Arama Motoru", self.settings.search_engine)
        add_entry("Timeout (sn)", str(self.settings.timeout))
        add_entry("Yazı Tipi", self.settings.font_family)
        add_entry("Yazı Boyutu", str(self.settings.font_size))
        add_entry("Arka Plan", self.settings.bg_color)
        add_entry("Yazı Rengi", self.settings.fg_color)
        add_entry("User-Agent", self.settings.user_agent)

        wrap_var = tk.BooleanVar(value=self.settings.auto_wrap_text)
        ttk.Checkbutton(dialog, text="Metni satırda sar", variable=wrap_var).pack(anchor="w", padx=12, pady=4)

        def save() -> None:
            try:
                self.settings.homepage = fields["Anasayfa"].get().strip() or self.settings.homepage
                self.settings.search_engine = fields["Arama Motoru"].get().strip() or self.settings.search_engine
                self.settings.timeout = max(2, int(fields["Timeout (sn)"].get().strip()))
                self.settings.font_family = fields["Yazı Tipi"].get().strip() or self.settings.font_family
                self.settings.font_size = max(8, int(fields["Yazı Boyutu"].get().strip()))
                self.settings.bg_color = fields["Arka Plan"].get().strip() or self.settings.bg_color
                self.settings.fg_color = fields["Yazı Rengi"].get().strip() or self.settings.fg_color
                self.settings.user_agent = fields["User-Agent"].get().strip() or DEFAULT_USER_AGENT
                self.settings.auto_wrap_text = wrap_var.get()
            except ValueError:
                messagebox.showerror("Hata", "Sayı alanlarına geçerli değer girin.")
                return

            self.apply_theme_to_all_tabs()
            self.save_settings()
            dialog.destroy()

        ttk.Button(dialog, text="Kaydet", command=save).pack(side="right", padx=12, pady=10)

    def show_cookies(self) -> None:
        cookies = [f"{c.name}={c.value}; domain={c.domain}; path={c.path}" for c in self.cookie_jar]
        message = "\n".join(cookies) if cookies else "Kayıtlı çerez yok."
        messagebox.showinfo("Çerezler", message)

    def add_bookmark_from_current(self) -> None:
        tab = self.current_tab()
        if not tab:
            return

        title = simpledialog.askstring("Yer İmi", "Başlık:", initialvalue=tab.title_var.get())
        if not title:
            return

        url = tab.url_var.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Geçerli bir URL yok.")
            return

        self.bookmarks.append({"title": title.strip(), "url": url})
        self.save_bookmarks()
        self.rebuild_bookmark_menu()

    def rebuild_bookmark_menu(self) -> None:
        while self.bookmark_menu.index("end") and self.bookmark_menu.index("end") >= 2:
            self.bookmark_menu.delete(2)

        if not self.bookmarks:
            self.bookmark_menu.add_command(label="(Yer imi yok)", state="disabled")
            return

        for bookmark in self.bookmarks:
            self.bookmark_menu.add_command(
                label=bookmark["title"],
                command=lambda u=bookmark["url"]: self.load_url(u),
            )

    def sync_global_status(self, *_args) -> None:
        tab = self.current_tab()
        self.status_var.set(tab.status_var.get() if tab else "Hazır")

    def load_settings(self) -> BrowserSettings:
        if not os.path.exists(CONFIG_FILE):
            return BrowserSettings()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            return BrowserSettings(**data)
        except (json.JSONDecodeError, TypeError, OSError):
            return BrowserSettings()

    def save_settings(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(asdict(self.settings), file, ensure_ascii=False, indent=2)
        except OSError as err:
            messagebox.showwarning("Uyarı", f"Ayarlar kaydedilemedi: {err}")

    def load_bookmarks(self) -> list[dict[str, str]]:
        bookmark_file = "bookmarks.json"
        if not os.path.exists(bookmark_file):
            return []

        try:
            with open(bookmark_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict) and "url" in item and "title" in item]
            return []
        except (json.JSONDecodeError, OSError):
            return []

    def save_bookmarks(self) -> None:
        try:
            with open("bookmarks.json", "w", encoding="utf-8") as file:
                json.dump(self.bookmarks, file, ensure_ascii=False, indent=2)
        except OSError as err:
            messagebox.showerror("Hata", f"Yer imleri kaydedilemedi: {err}")

    def on_close(self) -> None:
        self.save_settings()
        self.save_bookmarks()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedPythonBrowser(root)
    root.mainloop()

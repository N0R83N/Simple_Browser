from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile, QWebEngineUrlRequestInterceptor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

try:
    from platformdirs import user_cache_dir, user_config_dir, user_data_dir
except ImportError:
    # fallback when optional dependency is not installed
    def user_data_dir(appname: str, appauthor: str) -> str:
        return str(Path.home() / ".local" / "share" / appname)

    def user_config_dir(appname: str, appauthor: str) -> str:
        return str(Path.home() / ".config" / appname)

    def user_cache_dir(appname: str, appauthor: str) -> str:
        return str(Path.home() / ".cache" / appname)


APP_NAME = "SimpleBrowser"
APP_AUTHOR = "SimpleBrowser"


@dataclass
class BrowserPaths:
    data_dir: Path
    config_dir: Path
    cache_dir: Path
    db_path: Path
    settings_path: Path


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, blocked_domains: set[str]) -> None:
        super().__init__()
        self.blocked_domains = blocked_domains

    def interceptRequest(self, info) -> None:  # type: ignore[override]
        host = info.requestUrl().host().lower()
        for blocked in self.blocked_domains:
            if host == blocked or host.endswith(f".{blocked}"):
                info.block(True)
                return


class BrowserStorage:
    def __init__(self, paths: BrowserPaths) -> None:
        self.paths = paths
        self.connection = sqlite3.connect(self.paths.db_path)
        self._prepare_tables()

    def _prepare_tables(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT NOT NULL,
                visited_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()

    def add_bookmark(self, title: str, url: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO bookmarks(title, url) VALUES(?, ?)",
            (title or url, url),
        )
        self.connection.commit()

    def list_bookmarks(self) -> list[tuple[str, str]]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT title, url FROM bookmarks ORDER BY id DESC")
        return cursor.fetchall()

    def add_history(self, title: str, url: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO history(title, url) VALUES(?, ?)", (title, url))
        self.connection.commit()

    def list_history(self, limit: int = 200) -> list[tuple[str, str]]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT COALESCE(title, url), url FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()


class Sidebar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.bookmarks = QListWidget()
        self.history = QListWidget()
        self.bookmarks.setAlternatingRowColors(True)
        self.history.setAlternatingRowColors(True)
        self.bookmarks.setToolTip("Bookmarks")
        self.history.setToolTip("History")
        layout.addWidget(self.bookmarks)
        layout.addWidget(self.history)


class BrowserWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.paths = self._prepare_paths()
        self.settings = self._load_settings()
        self.storage = BrowserStorage(self.paths)
        self.profile = self._build_profile()

        self.setWindowTitle("Simple Browser - PySide6")
        self.resize(1280, 800)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_urlbar)

        self.sidebar = Sidebar()
        self.sidebar.bookmarks.itemDoubleClicked.connect(
            lambda item: self.navigate(item.data(Qt.UserRole))
        )
        self.sidebar.history.itemDoubleClicked.connect(
            lambda item: self.navigate(item.data(Qt.UserRole))
        )

        splitter = QSplitter()
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tabs)
        splitter.setSizes([280, 1000])
        self.setCentralWidget(splitter)

        self._build_toolbar()
        self._build_shortcuts()

        self.setStatusBar(QStatusBar())
        self.profile.downloadRequested.connect(self.handle_download)

        self.add_tab(QUrl("https://www.google.com"), "Yeni Sekme")
        self.refresh_sidebar()

    def _prepare_paths(self) -> BrowserPaths:
        data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
        config_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
        cache_dir = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
        data_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return BrowserPaths(
            data_dir=data_dir,
            config_dir=config_dir,
            cache_dir=cache_dir,
            db_path=data_dir / "browser.db",
            settings_path=config_dir / "settings.json",
        )

    def _load_settings(self) -> dict:
        default = {
            "search_engine": "https://duckduckgo.com/?q={query}",
            "blocked_domains": ["doubleclick.net", "googlesyndication.com"],
            "homepage": "https://www.google.com",
        }
        if self.paths.settings_path.exists():
            with self.paths.settings_path.open("r", encoding="utf-8") as fp:
                default.update(json.load(fp))
        return default

    def _save_settings(self) -> None:
        with self.paths.settings_path.open("w", encoding="utf-8") as fp:
            json.dump(self.settings, fp, indent=2, ensure_ascii=False)

    def _build_profile(self) -> QWebEngineProfile:
        profile = QWebEngineProfile("main", self)
        profile.setPersistentStoragePath(str(self.paths.data_dir / "profile"))
        profile.setCachePath(str(self.paths.cache_dir / "webcache"))
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        interceptor = AdBlockInterceptor(set(self.settings.get("blocked_domains", [])))
        profile.setUrlRequestInterceptor(interceptor)
        self.interceptor = interceptor
        return profile

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)

        back_action = QAction("←", self)
        back_action.triggered.connect(lambda: self.current_view().back())
        toolbar.addAction(back_action)

        next_action = QAction("→", self)
        next_action.triggered.connect(lambda: self.current_view().forward())
        toolbar.addAction(next_action)

        reload_action = QAction("⟳", self)
        reload_action.triggered.connect(lambda: self.current_view().reload())
        toolbar.addAction(reload_action)

        home_action = QAction("Home", self)
        home_action.triggered.connect(
            lambda: self.navigate(self.settings.get("homepage", "https://www.google.com"))
        )
        toolbar.addAction(home_action)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_from_bar)
        toolbar.addWidget(self.url_bar)

        bookmark_action = QAction("★", self)
        bookmark_action.triggered.connect(self.add_bookmark)
        toolbar.addAction(bookmark_action)

        menu_toolbar = QToolBar("Tools")
        self.addToolBar(menu_toolbar)

        new_tab_action = QAction("Yeni Sekme", self)
        new_tab_action.triggered.connect(lambda: self.add_tab())
        menu_toolbar.addAction(new_tab_action)

        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self.configure_settings)
        menu_toolbar.addAction(settings_action)

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.url_bar.setFocus)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=lambda: self.add_tab())
        QShortcut(
            QKeySequence("Ctrl+W"), self, activated=lambda: self.close_tab(self.tabs.currentIndex())
        )
        QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self.current_view().reload())

    def add_tab(self, qurl: Optional[QUrl] = None, label: str = "Yeni Sekme") -> None:
        if qurl is None:
            qurl = QUrl(self.settings.get("homepage", "https://www.google.com"))

        browser = QWebEngineView()
        page = browser.page()
        page.setProfile(self.profile)
        browser.setUrl(qurl)

        index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.loadFinished.connect(lambda ok, b=browser: self.on_load_finished(ok, b))

    def current_view(self) -> QWebEngineView:
        return self.tabs.currentWidget()

    def close_tab(self, index: int) -> None:
        if self.tabs.count() == 1:
            return
        self.tabs.removeTab(index)

    def navigate_from_bar(self) -> None:
        self.navigate(self.url_bar.text())

    def navigate(self, text: str) -> None:
        if " " in text or "." not in text:
            template = self.settings.get("search_engine", "https://duckduckgo.com/?q={query}")
            target = template.format(query=text.replace(" ", "+"))
        else:
            target = text if text.startswith(("http://", "https://")) else f"https://{text}"
        self.current_view().setUrl(QUrl(target))

    def update_urlbar(self, qurl: QUrl, browser: QWebEngineView) -> None:
        if browser != self.current_view():
            return
        self.url_bar.setText(qurl.toString())
        self.url_bar.setCursorPosition(0)

    def sync_urlbar(self, _: int) -> None:
        current = self.current_view()
        if current:
            self.url_bar.setText(current.url().toString())

    def update_tab_title(self, title: str, browser: QWebEngineView) -> None:
        index = self.tabs.indexOf(browser)
        if index >= 0:
            self.tabs.setTabText(index, title[:25] or "Yeni Sekme")

    def on_load_finished(self, ok: bool, browser: QWebEngineView) -> None:
        if not ok:
            self.statusBar().showMessage("Sayfa yüklenemedi", 3000)
            return
        title = browser.title() or browser.url().toString()
        url = browser.url().toString()
        self.storage.add_history(title, url)
        self.refresh_sidebar()

    def add_bookmark(self) -> None:
        current = self.current_view()
        if not current:
            return
        self.storage.add_bookmark(current.title() or current.url().toString(), current.url().toString())
        self.refresh_sidebar()
        self.statusBar().showMessage("Yer imi eklendi", 2000)

    def refresh_sidebar(self) -> None:
        self.sidebar.bookmarks.clear()
        for title, url in self.storage.list_bookmarks():
            self._add_list_item(self.sidebar.bookmarks, title, url)

        self.sidebar.history.clear()
        for title, url in self.storage.list_history():
            self._add_list_item(self.sidebar.history, title, url)

    def _add_list_item(self, widget: QListWidget, text: str, url: str) -> None:
        from PySide6.QtWidgets import QListWidgetItem

        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, url)
        item.setToolTip(url)
        widget.addItem(item)

    def handle_download(self, item: QWebEngineDownloadRequest) -> None:
        suggested = item.downloadFileName() or "download.bin"
        target, _ = QFileDialog.getSaveFileName(self, "Dosyayı Kaydet", suggested)
        if not target:
            item.cancel()
            return
        item.setDownloadDirectory(str(Path(target).parent))
        item.setDownloadFileName(Path(target).name)
        item.accept()
        item.receivedBytesChanged.connect(
            lambda: self.statusBar().showMessage(
                f"İndiriliyor: {item.receivedBytes()}/{item.totalBytes()} bytes"
            )
        )

    def configure_settings(self) -> None:
        current_search = self.settings.get("search_engine", "")
        new_search, ok = QInputDialog.getText(
            self,
            "Arama Motoru",
            "Arama URL şablonu ({query} kullanılmalı):",
            text=current_search,
        )
        if ok and "{query}" in new_search:
            self.settings["search_engine"] = new_search

        current_blocked = ", ".join(self.settings.get("blocked_domains", []))
        blocked_text, ok = QInputDialog.getText(
            self,
            "Reklam Engelleme",
            "Engellenecek domainler (virgülle):",
            text=current_blocked,
        )
        if ok:
            blocked = [x.strip() for x in blocked_text.split(",") if x.strip()]
            self.settings["blocked_domains"] = blocked
            self.interceptor.blocked_domains = set(blocked)

        self._save_settings()
        QMessageBox.information(self, "Ayarlar", "Ayarlar kaydedildi.")


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = BrowserWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

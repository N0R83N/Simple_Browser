# Simple Browser

A desktop browser prototype built with Python, PySide6, and QtWebEngine. It includes tabs, URL and search navigation, browsing history, bookmarks, downloads, and basic domain filtering.

## Run

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
python browser.py
```

The core browser uses PySide6 and QtWebEngine. Optional integrations listed in `requirements.txt` add features such as keyring support and ad-block filtering.
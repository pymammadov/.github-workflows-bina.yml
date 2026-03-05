# bina.az-statistika

`bina.az-statistika` Bina.az saytından həyət evi elanlarını toplayıb AZN/m² dəyərinə görə filtr edən və Telegram-a bildiriş göndərə bilən sadə Python layihəsidir.

## Fayllar

- `bina_heyet_monitor.py` — elanları yoxlayır, filtr edir və `sent` cədvəlində izləyir.
- `state/bina_sent.sqlite3` — göndərilmiş elan ID-lərinin saxlandığı SQLite bazası.
- `requirements.txt` — asılılıqlar.

## İşlətmə

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export NOTIFIER=none
python3 bina_heyet_monitor.py --once
```

## Ətraf mühit dəyişənləri

- `BINAAZ_LIST_URL` (default: Baku həyət evi linki)
- `PAGES` (default: `3`)
- `REQUEST_DELAY_SEC` (default: `1.3`)
- `MAX_AZN_PER_M2` (default: `1000`)
- `DB_PATH` (default: `state/bina_sent.sqlite3`)
- `NOTIFIER` (`telegram` və ya `none`)
- `KEYWORDS` (vergüllə ayrılmış açar sözlər)
- `TG_BOT_TOKEN`, `TG_CHAT_ID` (`NOTIFIER=telegram` üçün)

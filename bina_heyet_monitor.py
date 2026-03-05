#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import sqlite3
import argparse
from dataclasses import dataclass
from typing import Optional, List, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL_DEFAULT = "https://bina.az/baki/alqi-satqi/heyet-evleri"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "az,en;q=0.8,ru;q=0.7",
}


@dataclass
class Listing:
    listing_id: str
    url: str
    title: str
    price_azn: Optional[float]
    area_m2: Optional[float]
    azn_per_m2: Optional[float]
    location: str


def num_from_text(text: str) -> Optional[float]:
    if not text:
        return None
    s = re.sub(r"[^\d,\.]", "", text)
    if not s:
        return None
    # 12,5 -> 12.5
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    # 150,000 -> 150000 (if comma used as thousands)
    if s.count(",") > 1:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def extract_id(url: str) -> str:
    m = re.search(r"(\d{5,})", url)
    return m.group(1) if m else str(abs(hash(url)))


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def init_db(db_path: str) -> None:
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent (
            listing_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            sent_at INTEGER NOT NULL
        );
    """)
    con.commit()
    con.close()


def is_sent(db_path: str, listing_id: str) -> bool:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM sent WHERE listing_id=? LIMIT 1;", (listing_id,))
    ok = cur.fetchone() is not None
    con.close()
    return ok


def mark_sent(db_path: str, listing_id: str, url: str) -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO sent(listing_id, url, sent_at) VALUES(?,?,?);",
        (listing_id, url, int(time.time()))
    )
    con.commit()
    con.close()


def fetch_html(s: requests.Session, url: str, timeout: int = 30) -> str:
    r = s.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def parse_list_page_for_item_links(list_html: str, list_url: str) -> List[str]:
    """
    Maksimum dayanıqlılıq üçün:
    - /items/123456 formatlı linkləri tuturuq
    - həm relative, həm absolute qəbul edirik
    """
    soup = BeautifulSoup(list_html, "lxml")
    links: Set[str] = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue

        # Bina item url pattern: /items/1234567
        if re.search(r"/items/\d{5,}", href):
            full = urljoin(list_url, href)
            links.add(full.split("?")[0].rstrip("/"))

    return sorted(links)


def parse_item_page(item_html: str, item_url: str) -> Listing:
    soup = BeautifulSoup(item_html, "lxml")

    # Title (fallback)
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
    if not title:
        title = soup.title.get_text(" ", strip=True) if soup.title else "Elan"

    # Location/address (best-effort)
    location = ""
    # try common patterns
    for sel in ["div.product-map__left__address", "div.product-map__left", "div.location", "div.product__title"]:
        node = soup.select_one(sel)
        if node:
            t = node.get_text(" ", strip=True)
            if t and len(t) <= 120:
                location = t
                break

    # ---- Price extraction (best-effort) ----
    price_azn: Optional[float] = None

    # 1) meta tags sometimes have price
    for meta_key in [
        ("property", "product:price:amount"),
        ("property", "og:price:amount"),
        ("name", "price"),
    ]:
        tag = soup.find("meta", attrs={meta_key[0]: meta_key[1]})
        if tag and tag.get("content"):
            price_azn = num_from_text(tag["content"])
            if price_azn:
                break

    # 2) visible price text (₼ / AZN)
    if price_azn is None:
        text = soup.get_text(" ", strip=True)
        m = re.search(r"(\d[\d\s]{2,})\s*(AZN|₼)", text)
        if m:
            price_azn = num_from_text(m.group(1))

    # ---- Area extraction (m²) ----
    area_m2: Optional[float] = None
    text = soup.get_text(" ", strip=True)

    # Prefer patterns around "Sahə/Sahəsi"
    m_area = re.search(r"(Sah[əəsi]*\s*[:\-]?\s*)(\d+(?:[.,]\d+)?)\s*(m2|m²)", text, re.IGNORECASE)
    if m_area:
        area_m2 = num_from_text(m_area.group(2))

    # Fallback: first plausible m² mention
    if area_m2 is None:
        m2 = re.search(r"(\d+(?:[.,]\d+)?)\s*(m2|m²)", text, re.IGNORECASE)
        if m2:
            area_m2 = num_from_text(m2.group(1))

    azn_per_m2 = None
    if price_azn and area_m2 and area_m2 > 0:
        azn_per_m2 = price_azn / area_m2

    return Listing(
        listing_id=extract_id(item_url),
        url=item_url,
        title=title,
        price_azn=price_azn,
        area_m2=area_m2,
        azn_per_m2=azn_per_m2,
        location=location
    )


def build_message(items: List[Listing], limit: int = 10) -> str:
    items = items[:limit]
    lines = [f"Bina.az (həyət evi): {len(items)} yeni elan ≤ 1000 AZN/m²"]
    for i, it in enumerate(items, 1):
        p = f"{int(it.price_azn):,}".replace(",", " ") if it.price_azn else "?"
        a = f"{it.area_m2:g}" if it.area_m2 else "?"
        pm2 = f"{it.azn_per_m2:.0f}" if it.azn_per_m2 else "?"
        loc = f" | {it.location}" if it.location else ""
        lines.append(f"{i}) {pm2} AZN/m² | {p} AZN | {a} m²{loc}\n{it.url}")
    return "\n\n".join(lines)


def send_telegram(message: str) -> None:
    token = os.getenv("TG_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TG_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Telegram üçün TG_BOT_TOKEN və TG_CHAT_ID lazımdır.")
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(api, json={
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    }, timeout=30)
    r.raise_for_status()


def run_once() -> int:
    list_url = os.getenv("BINAAZ_LIST_URL", BASE_URL_DEFAULT).strip()
    pages = int(os.getenv("PAGES", "3"))
    delay = float(os.getenv("REQUEST_DELAY_SEC", "1.3"))
    max_azn_per_m2 = float(os.getenv("MAX_AZN_PER_M2", "1000"))
    db_path = os.getenv("DB_PATH", "state/bina_sent.sqlite3").strip()
    notifier = os.getenv("NOTIFIER", "telegram").strip().lower()  # telegram | none
    keywords_csv = os.getenv("KEYWORDS", "").strip()
    keywords = [k.strip().lower() for k in keywords_csv.split(",") if k.strip()] if keywords_csv else []

    init_db(db_path)

    s = session()

    all_item_links: List[str] = []
    for page in range(1, pages + 1):
        page_url = list_url
        # Bina.az pagination parametrləri dəyişə bilər; bu fallback üsuldur:
        # çox vaxt ?page=2 kimi işləyir. İşləməsə, sadəcə 1-ci səhifəni oxuyacaq.
        if page > 1:
            join_char = "&" if "?" in page_url else "?"
            page_url = f"{page_url}{join_char}page={page}"

        html = fetch_html(s, page_url)
        links = parse_list_page_for_item_links(html, page_url)
        all_item_links.extend(links)
        time.sleep(delay)

    # unique, keep order-ish
    seen = set()
    item_links = []
    for u in all_item_links:
        if u not in seen:
            seen.add(u)
            item_links.append(u)

    matches: List[Listing] = []

    for u in item_links:
        lid = extract_id(u)
        # artıq göndərilibsə, keç
        if is_sent(db_path, lid):
            continue

        try:
            item_html = fetch_html(s, u)
        except Exception:
            continue

        it = parse_item_page(item_html, u)

        # Filtr: qiymət və sahə mütləq olsun
        if it.azn_per_m2 is None:
            time.sleep(delay)
            continue

        if it.azn_per_m2 <= max_azn_per_m2:
            if keywords:
                hay = (it.title + " " + it.location + " " + it.url).lower()
                if not any(k in hay for k in keywords):
                    time.sleep(delay)
                    continue
            matches.append(it)

        time.sleep(delay)

    if not matches:
        return 0

    # ən ucuz AZN/m² əvvəl
    matches.sort(key=lambda x: x.azn_per_m2 if x.azn_per_m2 is not None else 10**18)

    msg = build_message(matches)

    if notifier == "telegram":
        send_telegram(msg)
    elif notifier == "none":
        print(msg)
    else:
        raise RuntimeError("NOTIFIER yalnız 'telegram' və ya 'none' ola bilər.")

    for it in matches:
        mark_sent(db_path, it.listing_id, it.url)

    return len(matches)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="Bir dəfə yoxla və çıx.")
    args = ap.parse_args()

    if args.once:
        n = run_once()
        print(f"Sent: {n}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

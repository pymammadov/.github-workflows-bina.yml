#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from dateutil import parser as dtparser
from playwright.sync_api import sync_playwright


# Bakı vaxtı (+04:00)
BAKU_TZ = timezone(timedelta(hours=4))


def normalize_settlement(raw: str) -> str:
    s = re.sub(r"\s+", " ", raw).strip()
    # "q." varsa təmizlə
    s = re.sub(r"\s*q\.$", "", s, flags=re.IGNORECASE).strip()
    return s


def parse_listing_datetime(text: str) -> Optional[datetime]:
    """
    Bina.az detal səhifəsində tarix formatları dəyişə bilər.
    Bu funksiya səhifə mətnindən tarix tapmağa çalışır.
    """
    # Tipik: "Yeniləndi: 02.03.2026" və ya "02.03.2026, 23:08"
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})(?:,\s*(\d{2}:\d{2}))?", text)
    if not m:
        return None

    date_part = m.group(1)
    time_part = m.group(2) or "00:00"
    dt = dtparser.parse(f"{date_part} {time_part}", dayfirst=True)
    return dt.replace(tzinfo=BAKU_TZ)


def extract_settlement_from_page(text: str) -> Optional[str]:
    """
    Breadcrumb / adres bloklarından qəsəbəni tutmağa çalışır.
    Məs: "Bakı, Xəzər r., Zirə q." -> Zirə
    """
    # ən sadə: "Zirə q." kimi hissəni tut
    m = re.search(r"([A-Za-zƏəÖöÜüĞğÇçŞşİı\- ]+)\s+q\.", text)
    if m:
        return normalize_settlement(m.group(1))

    # alternativ: "Zirə" tək də qala bilər — ehtiyac olarsa genişləndir
    return None


def run_scan(start_url: str, pages_to_scan: int, wait_ms: int, lookback_days: int) -> None:
    now = datetime.now(tz=BAKU_TZ)
    since = now - timedelta(days=lookback_days)

    settlement_counts: Counter[str] = Counter()
    scanned = 0
    kept = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i in range(1, pages_to_scan + 1):
            url = f"{start_url}&page={i}"
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(wait_ms)

            # siyahıdan item linklərini götür
            links = page.eval_on_selector_all(
                "a[href^='/items/']",
                "els => Array.from(new Set(els.map(e => e.href)))",
            )

            for link in links:
                scanned += 1
                page.goto(link, wait_until="networkidle")
                page.wait_for_timeout(800)

                txt = page.inner_text("body")

                dt = parse_listing_datetime(txt)
                if not dt or dt < since:
                    continue

                settlement = extract_settlement_from_page(txt)
                if not settlement:
                    continue

                settlement_counts[settlement] += 1
                kept += 1

            print(
                f"Scanned list page {i}: total detail pages visited so far={scanned}, "
                f"kept(last{lookback_days}d)={kept}"
            )

        browser.close()

    total = sum(settlement_counts.values())
    print(f"\n=== TOP qəsəbələr (son {lookback_days} gün) ===")
    for name, count in settlement_counts.most_common(20):
        pct = (count / total * 100) if total else 0
        print(f"{name:20s}  {count:4d}  ({pct:5.1f}%)")

    print(f"\nTOTAL counted (last {lookback_days} days): {total}")
    print(f"Since: {since.isoformat()}  To: {now.isoformat()}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Bina.az qəsəbə trend analizeri (son N gün).")
    ap.add_argument(
        "--start-url",
        default="https://bina.az/baki/alqi-satqi/heyet-evleri?items_view=list",
        help="Siyahı URL-i",
    )
    ap.add_argument("--pages", type=int, default=50, help="Skan ediləcək səhifə sayı")
    ap.add_argument("--wait-ms", type=int, default=2000, help="Siyahı səhifəsi gözləmə vaxtı (ms)")
    ap.add_argument("--days", type=int, default=14, help="Neçə günə baxılsın")
    args = ap.parse_args()

    run_scan(
        start_url=args.start_url,
        pages_to_scan=args.pages,
        wait_ms=args.wait_ms,
        lookback_days=args.days,
    )


if __name__ == "__main__":
    main()

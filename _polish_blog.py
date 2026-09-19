# -*- coding: utf-8 -*-
"""Polish blog hero descriptions + sync nav industries link."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

sys.stdout.reconfigure(encoding="utf-8")

BLOG = Path(r"D:\copy\wooooo\ufeel.sa\blog")


def fix_jammed_periods(text: str) -> str:
    # Arabic/Latin letter immediately after sentence punctuation
    text = re.sub(r"([.؟!])([\u0600-\u06FFa-zA-Z])", r"\1 \2", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_description(text: str, title: str) -> str:
    t = fix_jammed_periods(text or "")
    if title:
        if t.startswith(title):
            t = t[len(title) :].lstrip("؟? \u200f\u200e")
        compact = title.replace("؟", "").replace("?", "")
        if t.startswith(compact):
            t = t[len(compact) :].lstrip("؟? \u200f\u200e")
    t = t.replace("...", "…")
    if "…" in t:
        t = t.split("…")[0].strip()
    t = fix_jammed_periods(t)
    parts = re.split(r"(?<=[.؟!])\s+", t)
    out = " ".join(p for p in parts[:2] if p).strip()
    if len(out) > 220:
        out = out[:210].rsplit(" ", 1)[0] + "…"
    return out or t[:180]


def sync_nav(soup: BeautifulSoup) -> None:
    """Insert قطاعاتنا after خدماتنا when missing (desktop + mobile nav)."""
    for nav in soup.find_all("nav"):
        if nav.find("a", href=re.compile(r"industries\.html")):
            continue
        services = None
        for a in nav.find_all("a", href=True):
            if a["href"].endswith("services.html") and a.get_text(strip=True) in {
                "خدماتنا",
                "الخدمات",
            }:
                services = a
                break
        if not services:
            continue
        link = soup.new_tag(
            "a",
            href="../industries.html",
            attrs={
                "class": services.get("class", []),
            },
        )
        # copy click handler for mobile menus
        if services.has_attr("@click"):
            link["@click"] = services["@click"]
        link.append(NavigableString("\n    قطاعاتنا\n"))
        services.insert_after(link)
        services.insert_after(NavigableString("\n"))


def process(path: Path) -> None:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    title_el = soup.select_one(".blog-post__hero h1")
    desc_el = soup.select_one('.blog-post__hero p[itemprop="description"]')
    title = title_el.get_text(strip=True) if title_el else ""
    if desc_el:
        cleaned = clean_description(desc_el.get_text(" ", strip=True), title)
        desc_el.clear()
        desc_el.append(cleaned)

    # Fix Instagram broken localize if present
    for a in soup.find_all("a", href=True):
        if a["href"].endswith("digital-track.com.html"):
            a["href"] = "https://www.instagram.com/"

    sync_nav(soup)

    out = str(soup)
    if not out.lstrip().lower().startswith("<!doctype"):
        out = "<!DOCTYPE html>\n" + out
    path.write_text(out, encoding="utf-8")
    print("OK", path.name)


def main() -> None:
    for f in sorted(BLOG.glob("*.html")):
        process(f)


if __name__ == "__main__":
    main()

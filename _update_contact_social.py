# -*- coding: utf-8 -*-
"""Update WhatsApp/phone + keep only Facebook social links site-wide."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\copy\wooooo\ufeel.sa")

OLD_PHONE = "966500000000"
NEW_PHONE = "966501281585"
NEW_TEL = "+966501281585"
NEW_DISPLAY = "+966 50 128 1585"
FB_URL = "https://www.facebook.com/share/17wG841DGd/?mibextid=wwXIfr"

FB_SVG = """<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" class="h-4 w-4"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>"""

REMOVE_LABELS = {"Instagram", "X", "LinkedIn", "Snapchat", "Twitter", "تيك توك", "سناب شات"}


def replace_phones(text: str) -> str:
    text = text.replace(f"wa.me/{OLD_PHONE}", f"wa.me/{NEW_PHONE}")
    text = text.replace(f"tel:+{OLD_PHONE}", f"tel:{NEW_TEL}")
    text = text.replace(f"+{OLD_PHONE}", NEW_TEL)
    text = text.replace(OLD_PHONE, NEW_PHONE)
    text = text.replace("+966 50 000 0000", NEW_DISPLAY)
    text = text.replace("+96650 000 0000", NEW_DISPLAY)
    text = text.replace("50 000 0000", "50 128 1585")
    return text


def facebook_anchor(soup: BeautifulSoup, class_attr) -> object:
    a = soup.new_tag(
        "a",
        href=FB_URL,
        target="_blank",
        rel="noopener noreferrer",
        attrs={
            "class": class_attr
            or "social-links__item inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-white/55 transition-all duration-300 hover:border-white/20 hover:bg-white/[0.06] hover:text-white",
            "aria-label": "Facebook",
        },
    )
    icon = BeautifulSoup(FB_SVG, "html.parser")
    a.append(icon.svg)
    return a


def prune_social_nav(soup: BeautifulSoup) -> None:
    for nav in soup.find_all("nav", class_=re.compile(r"social-links")):
        items = list(nav.find_all("a", recursive=False))
        if not items:
            items = list(nav.find_all("a"))
        class_attr = None
        for a in items:
            if a.get("class"):
                class_attr = a.get("class")
                break
        # clear children and keep only Facebook
        nav.clear()
        nav.append(NavigableString("\n"))
        nav.append(facebook_anchor(soup, class_attr))
        nav.append(NavigableString("\n"))


def prune_footer_instagram_rows(soup: BeautifulSoup) -> None:
    """Remove footer contact rows that only link to Instagram / non-ready socials."""
    for a in list(soup.find_all("a", href=True)):
        href = a["href"]
        label = a.get("aria-label") or ""
        text = a.get_text(" ", strip=True).lower()
        if any(
            x in href
            for x in (
                "instagram.com",
                "snapchat.com",
                "linkedin.com",
                "x.com/",
                "twitter.com",
                "tiktok.com",
            )
        ):
            # keep if somehow facebook - else remove parent li if in footer contact
            parent_li = a.find_parent("li")
            if parent_li and parent_li.find_parent("ul"):
                parent_li.decompose()
            else:
                a.decompose()
            continue
        if label in REMOVE_LABELS and "facebook.com" not in href:
            a.decompose()


def update_facebook_urls(soup: BeautifulSoup) -> None:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "facebook.com" in href:
            a["href"] = FB_URL
            if a.get("aria-label") in REMOVE_LABELS | {"Facebook", None}:
                a["aria-label"] = "Facebook"
            # if it's a social icon with wrong svg (instagram etc), replace svg when in social-links
            parent_nav = a.find_parent("nav", class_=re.compile(r"social-links"))
            if parent_nav:
                # will be rebuilt in prune_social_nav
                pass


def update_json_ld(soup: BeautifulSoup) -> None:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        s = replace_phones(script.string)
        s = re.sub(
            r'"sameAs"\s*:\s*\[[^\]]*\]',
            f'"sameAs":["{FB_URL}"]',
            s,
        )
        script.clear()
        script.append(s)


def process_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw2 = replace_phones(raw)
    # quick facebook profile replacements before parse
    raw2 = re.sub(
        r"https://www\.facebook\.com/profile\.php\?id=61593710270768/?",
        FB_URL,
        raw2,
    )

    soup = BeautifulSoup(raw2, "html.parser")
    prune_social_nav(soup)
    prune_footer_instagram_rows(soup)
    update_facebook_urls(soup)
    update_json_ld(soup)

    # displayed phone spans
    for span in soup.find_all(string=re.compile(r"\+966\s*50\s*000\s*0000|50\s*000\s*0000")):
        new = replace_phones(str(span))
        span.replace_with(new)

    out = str(soup)
    if not out.lstrip().lower().startswith("<!doctype"):
        out = "<!DOCTYPE html>\n" + out
    if out == raw:
        return False
    path.write_text(out, encoding="utf-8")
    return True


def main() -> None:
    files = list(ROOT.rglob("*.html"))
    ok = 0
    for f in files:
        if "_boost" in str(f):
            continue
        if process_file(f):
            ok += 1
            print("OK", f.relative_to(ROOT))
    print(f"DONE {ok}/{len(files)}")

    # verify leftovers
    leftovers = []
    for f in ROOT.rglob("*.html"):
        t = f.read_text(encoding="utf-8", errors="ignore")
        if OLD_PHONE in t or "instagram.com" in t.lower() or "snapchat.com" in t.lower():
            leftovers.append(str(f.relative_to(ROOT)))
    print("leftover phone/instagram/snap:", leftovers[:20], "count", len(leftovers))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Improve design of all local blog post pages."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\copy\wooooo\ufeel.sa")
BLOG = ROOT / "blog"

STATIC_PAGES = {
    "": "../index.html",
    "/": "../index.html",
    "about-us": "../about-us.html",
    "services": "../services.html",
    "blog": "../blog.html",
    "jobs": "../jobs.html",
    "contact-us": "../contact-us.html",
    "industries": "../industries.html",
    "privacy-policy": "../privacy-policy.html",
    "terms-and-conditions": "../terms-and-conditions.html",
}


def localize_dt_url(url: str) -> str:
    if not url or "digital-track.com" not in url:
        return url

    # assets
    m = re.search(r"/build/assets/([^?#]+)", url)
    if m:
        return f"../build/assets/{m.group(1)}"

    parsed = urlparse(url)
    path = unquote(parsed.path or "/").strip("/")
    frag = f"#{parsed.fragment}" if parsed.fragment else ""

    if path in STATIC_PAGES:
        return STATIC_PAGES[path] + frag

    if path.startswith("blog/"):
        slug = path[len("blog/") :]
        if not slug:
            return "../blog.html" + frag
        if not slug.endswith(".html"):
            slug = f"{slug}.html"
        return slug + frag

    if path.startswith("services/"):
        slug = path[len("services/") :]
        if slug and not slug.endswith(".html"):
            slug = f"{slug}.html"
        return f"../services/{slug}" + frag if slug else "../services.html" + frag

    # bare domain
    if not path:
        return "../index.html" + frag

    # fallback: keep relative-ish
    return f"../{path}.html{frag}" if not path.endswith(".html") else f"../{path}{frag}"


def fix_urls_in_soup(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(True):
        for attr in ("href", "src", "content"):
            if not tag.has_attr(attr):
                continue
            val = tag.get(attr)
            if not isinstance(val, str) or "digital-track.com" not in val:
                continue
            # skip JSON-LD content that is whole graph — handled separately
            if attr == "content" and tag.name == "script":
                continue
            if attr == "content" and tag.get("itemprop") not in {
                "mainEntityOfPage",
                "url",
                "image",
            } and tag.name not in {"meta", "link"}:
                # og:url etc — localize when it's a page URL
                if "digital-track.com" in val and "/build/" not in val:
                    tag[attr] = localize_dt_url(val)
                elif "/build/assets/" in val:
                    tag[attr] = localize_dt_url(val)
                continue
            tag[attr] = localize_dt_url(val)

    # scripts with remote ENDPOINT — leave or neutralize
    for script in soup.find_all("script"):
        if script.string and "digital-track.com/_boost" in script.string:
            script.string = script.string.replace(
                "https://digital-track.com/_boost/browser-logs",
                "../_boost/browser-logs.html",
            )


def inject_css(soup: BeautifulSoup) -> None:
    if soup.find("link", href=re.compile(r"blog-enhance\.css")):
        return
    link = soup.new_tag("link", rel="stylesheet", href="../build/assets/blog-enhance.css")
    app_css = soup.find("link", href=re.compile(r"app-.*\.css"))
    if app_css:
        app_css.insert_after(link)
    elif soup.head:
        soup.head.append(link)


def clean_description(text: str, title: str) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    if title:
        # title jammed into start without separator
        if t.startswith(title):
            t = t[len(title) :].lstrip("؟? \u200f\u200e")
        # also handle glued title+body
        compact_title = title.replace("؟", "").replace("?", "")
        if t.startswith(compact_title):
            t = t[len(compact_title) :].lstrip("؟? \u200f\u200e")
    t = t.replace("...", "…")
    if "…" in t:
        t = t.split("…")[0].strip()
    parts = re.split(r"(?<=[.؟!])\s+", t)
    out = " ".join(p for p in parts[:2] if p).strip()
    if len(out) > 220:
        out = out[:210].rsplit(" ", 1)[0] + "…"
    return out or t[:180]


def enhance_body(soup: BeautifulSoup) -> None:
    body = soup.select_one("[data-blog-body]")
    if not body:
        return

    for el in body.find_all(True):
        if el.has_attr("style"):
            style = el.get("style", "")
            style = re.sub(r"text-align\s*:\s*right\s*;?", "", style, flags=re.I).strip(" ;")
            if style:
                el["style"] = style
            else:
                del el["style"]
        if el.has_attr("data-list-item-id"):
            del el["data-list-item-id"]

    for h3 in body.find_all("h3"):
        h3.name = "h2"

    paragraphs = [p for p in body.find_all("p", recursive=False)]
    if paragraphs:
        first = paragraphs[0]
        strong = first.find("strong")
        if strong and first.get_text(strip=True) == strong.get_text(strip=True):
            first.decompose()
            paragraphs = [p for p in body.find_all("p", recursive=False)]

    if paragraphs:
        classes = paragraphs[0].get("class") or []
        if "blog-lead" not in classes:
            paragraphs[0]["class"] = classes + ["blog-lead"]

    # Status flow with <br> → step chips
    for p in list(body.find_all("p")):
        html_inside = "".join(str(c) for c in p.contents)
        if html_inside.count("<br") >= 3 and "<ul" not in html_inside and "<li" not in html_inside:
            parts = [
                re.sub(r"<[^>]+>", "", x).strip()
                for x in re.split(r"<br\s*/?>", html_inside, flags=re.I)
            ]
            parts = [x for x in parts if x]
            if 3 <= len(parts) <= 12 and all(len(x) < 48 for x in parts):
                wrap = soup.new_tag("div", attrs={"class": "blog-steps"})
                for part in parts:
                    span = soup.new_tag("span")
                    span.string = part
                    wrap.append(span)
                p.replace_with(wrap)

    ps = body.find_all("p")
    if ps:
        last = ps[-1]
        if last.find("strong") and len(last.get_text(strip=True)) > 40:
            classes = last.get("class") or []
            if "blog-callout" not in classes:
                last["class"] = classes + ["blog-callout"]


def enhance_hero(soup: BeautifulSoup) -> None:
    hero = soup.select_one(".blog-post__hero")
    if not hero:
        return

    for img_wrap in hero.select(".mt-8.overflow-hidden"):
        classes = img_wrap.get("class") or []
        if "blog-post__cover" not in classes:
            img_wrap["class"] = classes + ["blog-post__cover"]

    title_el = hero.select_one("h1")
    desc_el = hero.select_one('p[itemprop="description"]')
    title = title_el.get_text(strip=True) if title_el else ""
    if desc_el:
        cleaned = clean_description(desc_el.get_text(" ", strip=True), title)
        desc_el.clear()
        desc_el.append(cleaned)


def ensure_blog_post_script(soup: BeautifulSoup) -> None:
    # already present at end usually — just ensure local path after fix_urls
    existing = soup.find("script", src=re.compile(r"blog-post-"))
    if existing:
        return
    body = soup.body
    if not body:
        return
    preload = soup.new_tag(
        "link",
        rel="modulepreload",
        attrs={"as": "script", "href": "../build/assets/blog-post-DrbnFPru.js"},
    )
    script = soup.new_tag(
        "script", type="module", src="../build/assets/blog-post-DrbnFPru.js"
    )
    body.append(preload)
    body.append(script)


def process_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")

    fix_urls_in_soup(soup)
    inject_css(soup)
    enhance_body(soup)
    enhance_hero(soup)
    ensure_blog_post_script(soup)

    out = str(soup)
    if not out.lstrip().lower().startswith("<!doctype"):
        out = "<!DOCTYPE html>\n" + out

    path.write_text(out, encoding="utf-8")
    return True


def main() -> None:
    files = sorted(BLOG.glob("*.html"))
    ok = 0
    for f in files:
        if process_file(f):
            ok += 1
            print("OK", f.name)
    print(f"DONE {ok}/{len(files)}")


if __name__ == "__main__":
    main()

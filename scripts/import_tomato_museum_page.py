#!/usr/bin/env python3
"""Import the original Tomato Industrial Museum detail page into the local mirror."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

import normalize_local_routes as routes_helper
from disable_parent_landing_pages import update_page


ROOT = Path(__file__).resolve().parent.parent
ROUTE = "/museums/tomato-industrial-museum/"
TARGET = ROOT / "museums" / "tomato-industrial-museum" / "index.html"
LISTING = ROOT / "allmuseums" / "index.html"
OLD_LINK = "index.htmlmuseums/tomato-industrial-museum/"


def remove_retired_navigation(html: str, routes: dict[str, str]) -> str:
    hidden = {"blog", "how-to-get-here", "contact", "archaeolog", "churches", "events"}

    def clean_nav(match: re.Match[str]) -> str:
        def clean_item(item_match: re.Match[str]) -> str:
            item = item_match.group(0)
            for attribute in routes_helper.ATTR_RE.finditer(item):
                if attribute.group(1).lower() != "href":
                    continue
                target = routes_helper.map_url(attribute.group(3), "/", routes, {})
                if urlsplit(target).path.strip("/").split("/")[0].lower() in hidden:
                    return ""
            return item

        return routes_helper.SIMPLE_LI_RE.sub(clean_item, match.group(0))

    return routes_helper.NAV_RE.sub(clean_nav, html)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Captured original HTML")
    args = parser.parse_args()
    if TARGET.exists():
        raise SystemExit(f"Refusing to overwrite existing page: {TARGET}")

    routes = routes_helper.known_routes()
    routes[ROUTE.strip("/")] = ROUTE
    routes[ROUTE.strip("/") + "/index.html"] = ROUTE

    html = args.source.read_text(encoding="utf-8", errors="replace")
    for expected in ("TOMATO INDUSTRIAL MUSEUM", "Vlychada Beach, Santorini", "tomato-museum.webp"):
        if expected not in html:
            raise ValueError(f"Original page is missing {expected!r}")
    html = remove_retired_navigation(html, routes)
    html = routes_helper.ensure_root_base(html)

    def local_link(match: re.Match[str]) -> str:
        name, quote, old = match.groups()
        new = routes_helper.map_url(old, ROUTE, routes, {})
        return f"{name}={quote}{new}{quote}"

    html = routes_helper.ATTR_RE.sub(local_link, html)
    for folder in ("wp-content", "wp-includes", "wp-admin", "wp-json"):
        html = html.replace(f"https://santorini.gr/{folder}/", f"/{folder}/")
        html = html.replace(f"https:\\/\\/santorini.gr\\/{folder}\\/", f"\\/{folder}\\/")
    html = html.replace("https://santorini.gr/xmlrpc.php", "/xmlrpc.php")
    html = html.replace('href="https://santorini.gr"', 'href="/"')
    if "local-cookie-state.js" not in html:
        html = html.replace("</body>", '<script src="/local-cookie-state.js"></script>\n</body>', 1)

    listing = LISTING.read_text(encoding="utf-8")
    if listing.count(OLD_LINK) != 2:
        raise ValueError(f"Expected two broken listing links; found {listing.count(OLD_LINK)}")
    if not (ROOT / "wp-content/uploads/2026/03/tomato-museum.webp").is_file():
        raise FileNotFoundError("Local museum image is missing")
    if not (ROOT / "wp-content/uploads/elementor/css/post-2203.css").is_file():
        raise FileNotFoundError("Local detail-page stylesheet is missing")

    TARGET.parent.mkdir(parents=True, exist_ok=False)
    TARGET.write_text(html, encoding="utf-8")
    update_page(TARGET)
    LISTING.write_text(listing.replace(OLD_LINK, ROUTE), encoding="utf-8")
    print(f"Imported {TARGET} ({TARGET.stat().st_size} bytes)")
    print(f"Repaired both Tomato card links in {LISTING}")


if __name__ == "__main__":
    main()

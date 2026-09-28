#!/usr/bin/env python3
"""Convert captured top-level HTML pages into local /slug/ routes.

The first --apply run preserves the pre-migration HTML in
route-migration-backup-20260922/. Legacy .html URLs become redirects, while
the canonical page content lives at <slug>/index.html. Running --apply again
is safe and re-applies navigation/link normalization without moving pages a
second time.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / "route-migration-backup-20260922"
SKIP_TOP_LEVEL = {"index.html", "history-english-backup.html", "index-approx-backup.html"}
HIDDEN_NAV_SLUGS = {"blog", "how-to-get-here", "archaeolog", "churches"}

ATTR_RE = re.compile(r"\b(href|action)\s*=\s*([\"'])(.*?)\2", re.I | re.S)
BASE_RE = re.compile(r"<base\b[^>]*\bhref\s*=\s*([\"']).*?\1[^>]*?/?>", re.I | re.S)
SIMPLE_LI_RE = re.compile(r"<li\b[^>]*>(?:(?!<li\b).)*?</li\s*>", re.I | re.S)
NAV_RE = re.compile(r"<nav\b[^>]*>.*?</nav\s*>", re.I | re.S)
SHORTLINK_RE = re.compile(
    r"<link\b(?=[^>]*\brel\s*=\s*([\"'])shortlink\1)[^>]*\bhref\s*=\s*([\"'])(.*?)\2[^>]*>",
    re.I | re.S,
)


def known_routes() -> dict[str, str]:
    routes = {"index.html": "/", "history.html": "/history/", "history/index.html": "/history/"}
    for page in ROOT.glob("*.html"):
        if page.name in SKIP_TOP_LEVEL:
            continue
        routes[page.name.lower()] = f"/{page.stem}/"
        routes[f"{page.stem.lower()}/index.html"] = f"/{page.stem}/"
        routes[f"{page.stem.lower()}/"] = f"/{page.stem}/"
    # Canonical pages can already have been moved by an earlier run.
    for page in ROOT.glob("*/index.html"):
        if page.parent.name not in {"wp-content", "wp-includes", "node_modules", "scripts"}:
            routes[f"{page.parent.name.lower()}/index.html"] = f"/{page.parent.name}/"
            routes[f"{page.parent.name.lower()}/"] = f"/{page.parent.name}/"
            # Keep the original captured filename as a route alias even after
            # the content has moved and that filename has become a redirect.
            routes[f"{page.parent.name.lower()}.html"] = f"/{page.parent.name}/"
    return routes


def is_legacy_redirect(text: str) -> bool:
    return bool(re.search(r"data-local-route-redirect|location\.replace\s*\(", text, re.I))


def route_for_path(path: str, routes: dict[str, str]) -> str | None:
    decoded = unquote(path).replace("\\", "/")
    while decoded.startswith("./"):
        decoded = decoded[2:]
    candidates = (decoded.lower(), decoded.lstrip("/").lower())
    for candidate in candidates:
        if candidate in routes:
            return routes[candidate]
    return None


def make_post_id_routes(pages: list[tuple[Path, str]], routes: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path, route in pages:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in SHORTLINK_RE.finditer(text):
            parsed = urlsplit(match.group(3))
            post_id = parse_qs(parsed.query).get("p", [None])[0]
            if post_id:
                result.setdefault(post_id, route)
    return result


def map_url(value: str, current_route: str, routes: dict[str, str], post_ids: dict[str, str]) -> str:
    value = value.strip()
    if not value or value.startswith(("data:", "javascript:", "mailto:", "tel:", "sms:", "blob:")):
        return value
    if value.startswith("#"):
        return current_route + value

    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return value
    internal_host = parsed.netloc.lower().removeprefix("www.") in {"santorini.gr", "www.santorini.gr"}
    if parsed.netloc and not internal_host:
        return value

    path = parsed.path
    if not path and parsed.query:
        return value
    mapped = route_for_path(path, routes)
    if mapped is None and Path(unquote(path)).name.lower() == "index.html":
        post_id = parse_qs(parsed.query).get("p", [None])[0]
        if post_id and post_id in post_ids:
            mapped = post_ids[post_id]
        elif path in {"index.html", "/index.html", ""}:
            mapped = "/"
    if mapped is None:
        # Keep existing root-relative paths (assets, anchors, and externalized files) local.
        return value

    # A WordPress shortlink query is an alias for a captured page, not page state.
    query = "" if parse_qs(parsed.query).get("p") and (mapped != "/" or Path(unquote(path)).name == "index.html") else (f"?{parsed.query}" if parsed.query else "")
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{mapped}{query}{fragment}"


def strip_unwanted_nav_items(text: str, routes: dict[str, str]) -> tuple[str, int]:
    removed = 0

    def nav_replacer(nav_match: re.Match[str]) -> str:
        nonlocal removed
        nav = nav_match.group(0)

        def item_replacer(item_match: re.Match[str]) -> str:
            nonlocal removed
            item = item_match.group(0)
            for attr_match in ATTR_RE.finditer(item):
                if attr_match.group(1).lower() != "href":
                    continue
                target = map_url(attr_match.group(3), "/", routes, {})
                slug = target.strip("/").split("/")[0].lower()
                if slug in HIDDEN_NAV_SLUGS:
                    removed += 1
                    return ""
            return item

        return SIMPLE_LI_RE.sub(item_replacer, nav)

    return NAV_RE.sub(nav_replacer, text), removed


def ensure_root_base(text: str) -> str:
    base_tag = '<base href="/">'
    if BASE_RE.search(text):
        return BASE_RE.sub(base_tag, text, count=1)
    head = re.search(r"<head\b[^>]*>", text, re.I)
    if not head:
        raise ValueError("HTML document has no <head> element")
    return text[: head.end()] + "\n\t" + base_tag + text[head.end() :]


def redirect_html(slug: str) -> str:
    target = f"/{slug}/"
    return f"""<!doctype html>
<html lang="en-US">
<head>
  <meta charset="UTF-8">
  <meta name="robots" content="noindex">
  <meta name="data-local-route-redirect" content="{target}">
  <title>Local page moved</title>
  <script>location.replace({target!r} + location.search + location.hash);</script>
</head>
<body><p>This page has moved to <a href="{target}">{target}</a>.</p></body>
</html>
"""


def page_targets() -> list[tuple[Path, str]]:
    targets: list[tuple[Path, str]] = [(ROOT / "index.html", "/")]
    for route_dir in sorted(ROOT.iterdir()):
        if not route_dir.is_dir() or route_dir.name.startswith(".") or route_dir.name in {
            "assets", "comments", "inspect_output", "outputs", "reference", "scripts",
            "wp-content", "wp-includes", "node_modules", "route-migration-backup-20260922",
        }:
            continue
        candidate = route_dir / "index.html"
        if candidate.is_file():
            targets.append((candidate, f"/{route_dir.name}/"))
    return targets


def run(apply: bool) -> None:
    routes = known_routes()
    moves: list[tuple[Path, Path]] = []
    aliases: list[tuple[Path, str]] = []

    for source in sorted(ROOT.glob("*.html")):
        if source.name in SKIP_TOP_LEVEL:
            continue
        slug = source.stem
        destination = ROOT / slug / "index.html"
        content = source.read_text(encoding="utf-8", errors="replace")
        if source.name == "history.html" and destination.exists():
            aliases.append((source, slug))
        elif is_legacy_redirect(content) and destination.exists():
            aliases.append((source, slug))
        elif destination.exists():
            raise FileExistsError(f"Refusing to overwrite an existing route: {destination}")
        else:
            moves.append((source, destination))
            aliases.append((source, slug))

    if not apply:
        print(f"Would move {len(moves)} page(s) into /slug/index.html and create/update {len(aliases)} legacy redirects.")
        print("Routes already present:")
        for source, destination in moves:
            print(f"  {source.name} -> /{source.stem}/ ({destination})")
        print("Would preserve pre-migration pages under:", BACKUP)
        return

    # Preserve the current, already-edited project before changing paths/content.
    backup_candidates = [ROOT / "index.html", ROOT / "history" / "index.html"]
    backup_candidates += [source for source, _ in moves]
    backup_candidates += [source for source, _ in aliases if source.exists()]
    for source in dict.fromkeys(backup_candidates):
        if not source.is_file():
            continue
        destination = BACKUP / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(source, destination)

    for source, destination in moves:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    targets = page_targets()
    routes = known_routes()
    post_ids = make_post_id_routes(targets, routes)
    changed_pages = 0
    removed_nav_items = 0

    for page, route in targets:
        text = page.read_text(encoding="utf-8", errors="replace")
        text, removed = strip_unwanted_nav_items(text, routes)
        removed_nav_items += removed
        text = ensure_root_base(text)

        def attr_replacer(match: re.Match[str]) -> str:
            name, quote, old = match.groups()
            new = map_url(old, route, routes, post_ids)
            return f"{name}={quote}{new}{quote}"

        text = ATTR_RE.sub(attr_replacer, text)
        page.write_text(text, encoding="utf-8")
        changed_pages += 1

    for source, slug in aliases:
        source.write_text(redirect_html(slug), encoding="utf-8")

    print(f"Canonical pages normalized: {changed_pages}")
    print(f"Legacy .html redirects written: {len(aliases)}")
    print(f"Unwanted Blog/How-to nav entries removed: {removed_nav_items}")
    print(f"Backup: {BACKUP}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the route migration; default is a dry run.")
    args = parser.parse_args()
    run(args.apply)


if __name__ == "__main__":
    main()

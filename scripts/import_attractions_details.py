#!/usr/bin/env python3
"""Import the requested Attractions detail pages as local directory routes.

The source documents are captured from the original site first.  This script
rewrites only the requested listing cards and saves their page assets locally,
so the mirror never depends on santorini.gr for page images or Elementor CSS.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
CAPTURES = Path('/tmp/santorini-attractions-import')
ORIGIN = 'https://santorini.gr'

PAGES = (
    {
        'capture': 'museum-koutsogiannopoulos.html',
        'route': 'museums/museum-koutsogiannopoulos/',
        'listing': 'allmuseums/index.html',
        'old': 'index.htmlmuseums/museum-koutsogiannopoulos/',
    },
    {
        'capture': 'oia.html',
        'route': 'villagescpt/oia/',
        'listing': 'villages/index.html',
        'old': 'index.htmlvillagescpt/oia/',
    },
    {
        'capture': 'fira.html',
        'route': 'villagescpt/fira/',
        'listing': 'villages/index.html',
        'old': 'index.htmlvillagescpt/fira/',
    },
    {
        'capture': 'kamari.html',
        'route': 'beachescpt/kamari/',
        'listing': 'beaches/index.html',
        'old': 'index.htmlbeachescpt/kamari/',
    },
    {
        'capture': 'perivolos.html',
        'route': 'beachescpt/perivolos/',
        'listing': 'beaches/index.html',
        'old': 'index.htmlbeachescpt/perivolos/',
    },
    {
        'capture': 'volcano.html',
        'route': 'volcano/',
        'listing': None,
        'old': None,
    },
)

RESOURCE_RE = re.compile(r"\b(?:src|href|poster|data-src|data-bg)\s*=\s*([\"'])(.*?)\1", re.I | re.S)
SRCSET_RE = re.compile(r"\bsrcset\s*=\s*([\"'])(.*?)\1", re.I | re.S)
CSS_URL_RE = re.compile(r"url\(\s*([\"']?)(.*?)\1\s*\)", re.I | re.S)


def load_helpers():
    spec = importlib.util.spec_from_file_location('local_routes', ROOT / 'scripts' / 'normalize_local_routes.py')
    if not spec or not spec.loader:
        raise RuntimeError('Could not load local route helpers')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_hidden_nav_items(text: str, helpers, routes: dict[str, str]) -> tuple[str, int]:
    hidden = {'blog', 'how-to-get-here', 'contact', 'archaeolog', 'churches'}
    removed = 0

    def nav_replacer(nav_match: re.Match[str]) -> str:
        nonlocal removed

        def item_replacer(item_match: re.Match[str]) -> str:
            nonlocal removed
            item = item_match.group(0)
            for attr_match in helpers.ATTR_RE.finditer(item):
                if attr_match.group(1).lower() != 'href':
                    continue
                target = helpers.map_url(attr_match.group(3), '/', routes, {})
                if target.strip('/').split('/')[0].lower() in hidden:
                    removed += 1
                    return ''
            return item

        return helpers.SIMPLE_LI_RE.sub(item_replacer, nav_match.group(0))

    return helpers.NAV_RE.sub(nav_replacer, text), removed


def normalize_page(text: str, route: str, helpers, routes: dict[str, str]) -> tuple[str, int]:
    text, removed = remove_hidden_nav_items(text, helpers, routes)
    text = helpers.ensure_root_base(text)

    def attr_replacer(match: re.Match[str]) -> str:
        name, quote, value = match.groups()
        return f'{name}={quote}{helpers.map_url(value, "/" + route, routes, {})}{quote}'

    text = helpers.ATTR_RE.sub(attr_replacer, text)
    for section in ('wp-content', 'wp-includes', 'wp-admin', 'wp-json'):
        text = text.replace(f'https://santorini.gr/{section}/', f'/{section}/')
        text = text.replace(f'https://www.santorini.gr/{section}/', f'/{section}/')
        text = text.replace(f'https:\\/\\/santorini.gr\\/{section}\\/', f'\\/{section}\\/')
    text = text.replace('https://santorini.gr/xmlrpc.php', '/xmlrpc.php')
    text = text.replace('href="https://santorini.gr"', 'href="/"')
    text = text.replace('href="https://www.santorini.gr"', 'href="/"')
    if 'local-cookie-state.js' not in text:
        text = text.replace('</body>', '<script src="/local-cookie-state.js"></script>\n</body>', 1)
    return text, removed


def resource_path(value: str, base_url: str = ORIGIN + '/') -> tuple[str, str] | None:
    value = value.strip().strip('"\'')
    if not value or value.startswith(('data:', '#', 'javascript:')):
        return None
    parsed = urlsplit(urljoin(base_url, value))
    if parsed.netloc not in {'santorini.gr', 'www.santorini.gr'}:
        return None
    path = unquote(parsed.path)
    if not path.startswith(('/wp-content/', '/wp-includes/')):
        return None
    if '..' in Path(path).parts:
        return None
    return path, f'{ORIGIN}{path}' + (f'?{parsed.query}' if parsed.query else '')


def page_resources(text: str) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for match in RESOURCE_RE.finditer(text):
        item = resource_path(match.group(2))
        if item:
            found.add(item)
    for match in SRCSET_RE.finditer(text):
        for candidate in match.group(2).split(','):
            item = resource_path(candidate.strip().split()[0])
            if item:
                found.add(item)
    for match in CSS_URL_RE.finditer(text):
        item = resource_path(match.group(2))
        if item:
            found.add(item)
    return found


def download_assets(initial: set[tuple[str, str]]) -> int:
    pending = list(initial)
    seen: set[str] = set()
    downloaded = 0
    while pending:
        path, url = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        destination = ROOT / path.lstrip('/')
        if destination.is_file() and destination.stat().st_size:
            data = destination.read_bytes()
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0 local Santorini mirror'})
            try:
                with urlopen(request, timeout=30) as response:
                    data = response.read()
            except Exception as error:
                raise RuntimeError(f'Unable to download {url}: {error}') from error
            destination.write_bytes(data)
            downloaded += 1
        if destination.suffix.lower() == '.css':
            css = data.decode('utf-8', errors='replace')
            base = url.rsplit('/', 1)[0] + '/'
            for match in CSS_URL_RE.finditer(css):
                item = resource_path(match.group(2), base)
                if item:
                    pending.append(item)
    return downloaded


def replace_listing_url(page: Path, old: str, route: str) -> int:
    content = page.read_text(encoding='utf-8', errors='replace')
    new = '/' + route
    count = content.count(old)
    if count == 0:
        if content.count(new) != 2:
            raise RuntimeError(f'Expected two links for {route} in {page}, found neither old nor canonical form')
        return 0
    if count != 2:
        raise RuntimeError(f'Expected exactly two broken links for {route} in {page}; found {count}')
    page.write_text(content.replace(old, new), encoding='utf-8')
    return count


def main() -> None:
    helpers = load_helpers()
    routes = helpers.known_routes()
    for page in PAGES:
        route = page['route']
        routes[route] = '/' + route
        routes[route + 'index.html'] = '/' + route

    total_assets = 0
    total_hidden = 0
    for spec in PAGES:
        source = CAPTURES / spec['capture']
        if not source.is_file():
            raise RuntimeError(f'Missing captured source: {source}')
        route = spec['route']
        text, hidden = normalize_page(source.read_text(encoding='utf-8', errors='replace'), route, helpers, routes)
        target = ROOT / route / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        total_hidden += hidden
        total_assets += download_assets(page_resources(text))
        if spec['listing']:
            changed = replace_listing_url(ROOT / spec['listing'], spec['old'], route)
            print(f'{route}: wrote page; fixed {changed} listing link attributes')
        else:
            print(f'{route}: refreshed existing local route')
    print(f'Downloaded {total_assets} missing local assets; removed {total_hidden} hidden navigation items')


if __name__ == '__main__':
    main()

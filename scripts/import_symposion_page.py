#!/usr/bin/env python3
"""Import the captured Symposion source into the local nested route."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path('/tmp/symposion-cultural-center.html')
TARGET = ROOT / 'museums' / 'symposion-cultural-center' / 'index.html'


def load_route_helpers():
    spec = importlib.util.spec_from_file_location('local_routes', ROOT / 'scripts' / 'normalize_local_routes.py')
    if not spec or not spec.loader:
        raise RuntimeError('Could not load route helpers')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_nav_slugs(text: str, helpers, routes: dict[str, str]) -> tuple[str, int]:
    hidden = {'blog', 'how-to-get-here', 'contact', 'archaeolog', 'churches'}
    removed = 0

    def nav_replacer(nav_match: re.Match[str]) -> str:
        nonlocal removed
        nav = nav_match.group(0)

        def item_replacer(item_match: re.Match[str]) -> str:
            nonlocal removed
            item = item_match.group(0)
            for attr_match in helpers.ATTR_RE.finditer(item):
                if attr_match.group(1).lower() != 'href':
                    continue
                target = helpers.map_url(attr_match.group(3), '/', routes, {})
                slug = target.strip('/').split('/')[0].lower()
                if slug in hidden:
                    removed += 1
                    return ''
            return item

        return helpers.SIMPLE_LI_RE.sub(item_replacer, nav)

    return helpers.NAV_RE.sub(nav_replacer, text), removed


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f'Missing source capture: {SOURCE}')
    helpers = load_route_helpers()
    routes = helpers.known_routes()
    routes['museums/symposion-cultural-center/'] = '/museums/symposion-cultural-center/'
    routes['museums/symposion-cultural-center/index.html'] = '/museums/symposion-cultural-center/'

    text = SOURCE.read_text(encoding='utf-8', errors='replace')
    text, removed = remove_nav_slugs(text, helpers, routes)
    text = helpers.ensure_root_base(text)

    def attr_replacer(match: re.Match[str]) -> str:
        name, quote, old = match.groups()
        new = helpers.map_url(old, '/museums/symposion-cultural-center/', routes, {})
        return f'{name}={quote}{new}{quote}'

    text = helpers.ATTR_RE.sub(attr_replacer, text)
    text = text.replace('https://santorini.gr/wp-content/', '/wp-content/')
    text = text.replace('https://santorini.gr/wp-includes/', '/wp-includes/')
    text = text.replace('https://santorini.gr/wp-admin/', '/wp-admin/')
    text = text.replace('https://santorini.gr/wp-json/', '/wp-json/')
    text = text.replace('https://santorini.gr/xmlrpc.php', '/xmlrpc.php')
    text = text.replace('https:\\/\\/santorini.gr\\/wp-content\\/', '\\/wp-content\\/')
    text = text.replace('https:\\/\\/santorini.gr\\/wp-includes\\/', '\\/wp-includes\\/')
    text = text.replace('https:\\/\\/santorini.gr\\/wp-admin\\/', '\\/wp-admin\\/')
    text = text.replace('https:\\/\\/santorini.gr\\/wp-json\\/', '\\/wp-json\\/')
    text = text.replace('href="https://santorini.gr"', 'href="/"')
    text = text.replace('href="https://www.santorini.gr"', 'href="/"')
    if 'local-cookie-state.js' not in text:
        text = text.replace('</body>', '<script src="/local-cookie-state.js"></script>\n</body>', 1)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding='utf-8')

    all_museums = ROOT / 'allmuseums' / 'index.html'
    page = all_museums.read_text(encoding='utf-8')
    old = 'index.htmlmuseums/symposion-cultural-center/'
    new = '/museums/symposion-cultural-center/'
    count = page.count(old)
    if count == 0 and page.count(new) == 2:
        count = 0
    elif count != 2:
        raise RuntimeError(f'Expected two Symposion listing URLs, found {count}')
    if count:
        all_museums.write_text(page.replace(old, new), encoding='utf-8')
    print(f'Wrote {TARGET}')
    print(f'Removed {removed} hidden navigation entries')
    print(f'Updated {count} Symposion listing URLs in {all_museums}')


if __name__ == '__main__':
    main()

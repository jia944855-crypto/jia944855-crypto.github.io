#!/usr/bin/env python3
"""Remove the Archaeological and Churches Attractions categories from the mirror."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKIP = {'route-migration-backup-20260922', 'node_modules', '.git'}
TARGETS = ('archaeolog', 'churches')
NAV_ITEM = re.compile(
    r'<li\b[^>]*>\s*<a\b(?=[^>]*\bhref\s*=\s*(["\'])/(?:archaeolog|churches)/\1)[^>]*>.*?</a>\s*</li>\s*',
    re.I | re.S,
)


def canonical_pages() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob('index.html')
        if not any(part in SKIP for part in path.relative_to(ROOT).parts)
    )


def remove_element(text: str, tag: str, element_id: str) -> tuple[str, int]:
    opener = re.compile(
        rf'<{tag}\b(?=[^>]*\bdata-id\s*=\s*(["\']){re.escape(element_id)}\1)[^>]*>',
        re.I | re.S,
    )
    match = opener.search(text)
    if not match:
        return text, 0
    tags = re.compile(rf'</?{tag}\b[^>]*>', re.I | re.S)
    depth = 0
    for token in tags.finditer(text, match.start()):
        depth += -1 if token.group(0).startswith('</') else 1
        if depth == 0:
            return text[:match.start()] + text[token.end():], 1
    raise ValueError(f'Unclosed <{tag}> for data-id={element_id}')


def remove_archaeological_slide(text: str) -> tuple[str, int]:
    title = re.search(r'<h3 class="caption"\s*>Archaeological Sites</h3>', text)
    if not title:
        return text, 0
    start = text.rfind('<div class="single-slide">', 0, title.start())
    if start < 0:
        raise ValueError('Archaeological slide has no .single-slide container')
    tags = re.compile(r'</?div\b[^>]*>', re.I | re.S)
    depth = 0
    for token in tags.finditer(text, start):
        depth += -1 if token.group(0).startswith('</') else 1
        if depth == 0:
            updated = text[:start] + text[token.end():]
            updated = updated.replace('01/03', '01/02', 1).replace('02/03', '02/02', 1)
            return updated, 1
    raise ValueError('Unclosed Archaeological slide')


def main() -> None:
    changed_pages = 0
    nav_items = 0
    for page in canonical_pages():
        content = page.read_text(encoding='utf-8', errors='replace')
        updated, removed = NAV_ITEM.subn('', content)
        nav_items += removed
        if page == ROOT / 'index.html':
            for element_id in ('c5ef979', 'e36f6e1'):
                updated, count = remove_element(updated, 'a', element_id)
                if count != 1:
                    raise ValueError(f'Missing homepage Attractions card {element_id}')
            updated, count = remove_archaeological_slide(updated)
            if count != 1:
                raise ValueError('Missing Archaeological homepage slide')
        elif page == ROOT / 'attractions' / 'index.html':
            for element_id in ('2c408c5d', '3e7514c6', '17ffb1f'):
                updated, count = remove_element(updated, 'div', element_id)
                if count != 1:
                    raise ValueError(f'Missing Attractions component {element_id}')
            updated = updated.replace(
                'cobbled paths and century-old churches and monasteries.',
                'cobbled paths.',
            )
        if updated != content:
            page.write_text(updated, encoding='utf-8')
            changed_pages += 1

    removed_pages = []
    for slug in TARGETS:
        route = ROOT / slug
        page = route / 'index.html'
        if page.is_file():
            page.unlink()
            route.rmdir()
            removed_pages.append(str(page.relative_to(ROOT)))
        legacy = ROOT / f'{slug}.html'
        if legacy.is_file():
            legacy.unlink()
            removed_pages.append(str(legacy.relative_to(ROOT)))

    print(f'Updated {changed_pages} pages; removed {nav_items} navigation entries')
    print('Deleted routes:', ', '.join(removed_pages))


if __name__ == '__main__':
    main()

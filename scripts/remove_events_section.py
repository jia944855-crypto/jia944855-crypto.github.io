#!/usr/bin/env python3
"""Remove the local What to Do → Events feature without touching other sections."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_PARTS = {'route-migration-backup-20260922', '.git', 'node_modules'}

# Each captured page has desktop and mobile copies of the same submenu item.
EVENT_NAV_ITEM = re.compile(
    r'<li\b[^>]*>(?:(?!<li\b).)*?<a\b(?=[^>]*\bhref\s*=\s*(["\'])/events/\1)[^>]*>.*?</a>(?:(?!<li\b).)*?</li>\s*',
    re.I | re.S,
)
DIV_TAG = re.compile(r'</?div\b[^>]*>', re.I)
HOME_EVENTS_CONTAINER = re.compile(
    r'<div\b(?=[^>]*\bdata-id\s*=\s*(["\'])60534c7\1)[^>]*>', re.I | re.S
)


def canonical_pages() -> list[Path]:
    pages = [ROOT / 'index.html']
    for candidate in ROOT.rglob('index.html'):
        if candidate == ROOT / 'index.html':
            continue
        if any(part in EXCLUDED_PARTS for part in candidate.relative_to(ROOT).parts):
            continue
        pages.append(candidate)
    return sorted(set(pages))


def closing_div(text: str, start: int) -> int:
    depth = 0
    for match in DIV_TAG.finditer(text, start):
        if match.group(0).lower().startswith('</'):
            depth -= 1
            if depth == 0:
                return match.end()
        else:
            depth += 1
    raise ValueError('Unterminated Events container')


def remove_home_events(text: str) -> tuple[str, int]:
    match = HOME_EVENTS_CONTAINER.search(text)
    if not match:
        return text, 0
    end = closing_div(text, match.start())
    return text[:match.start()] + text[end:], 1


def main() -> None:
    nav_removed = 0
    changed_pages = 0
    for page in canonical_pages():
        text = page.read_text(encoding='utf-8', errors='replace')
        updated, removed = EVENT_NAV_ITEM.subn('', text)
        if page == ROOT / 'index.html':
            updated, home_removed = remove_home_events(updated)
        else:
            home_removed = 0
        if updated != text:
            page.write_text(updated, encoding='utf-8')
            changed_pages += 1
        nav_removed += removed
        if home_removed:
            print(f'Removed homepage Festivals and Events section from {page}')

    event_directory = ROOT / 'events'
    if event_directory.exists():
        shutil.rmtree(event_directory)
        print(f'Removed {event_directory}')
    legacy = ROOT / 'events.html'
    if legacy.exists():
        legacy.unlink()
        print(f'Removed {legacy}')

    print(f'Updated {changed_pages} canonical page(s); removed {nav_removed} Events navigation item(s)')


if __name__ == '__main__':
    main()

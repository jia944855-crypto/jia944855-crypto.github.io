#!/usr/bin/env python3
"""Make category labels submenu-only and remove their unused landing pages.

Run again after importing new mirrored pages. Only canonical index.html pages are
rewritten; child pages, media assets, and the archived migration backup are kept.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PARENTS = ('about-santorini', 'attractions', 'what-to-do', 'what-to-eat')
EXCLUDED = {'route-migration-backup-20260922', '.git', 'node_modules'}
ANCHOR = re.compile(r'<a\b[^>]*>', re.I)
HREF = re.compile(r'\s+href="/(' + '|'.join(PARENTS) + r')/"', re.I)
SCRIPT = '<script src="/local-parent-menu.js"></script>'


def pages() -> list[Path]:
    return sorted(
        page for page in ROOT.rglob('index.html')
        if not any(part in EXCLUDED for part in page.relative_to(ROOT).parts)
        and not any(part in PARENTS for part in page.relative_to(ROOT).parts)
    )


def update_page(page: Path) -> tuple[int, int]:
    source = page.read_text(encoding='utf-8')
    count = 0

    def change_anchor(match: re.Match[str]) -> str:
        nonlocal count
        anchor = match.group()
        if not HREF.search(anchor) or 'class="elementor-item' not in anchor:
            return anchor
        count += 1
        anchor = HREF.sub('', anchor, count=1)
        anchor = anchor[:-1] + ' data-submenu-only role="button" aria-haspopup="true" aria-expanded="false"' + anchor[-1]
        if 'tabindex=' not in anchor:
            anchor = anchor[:-1] + ' tabindex="0"' + anchor[-1]
        return anchor

    updated = ANCHOR.sub(change_anchor, source)
    if page == ROOT / 'index.html':
        for old, new in (('/about-santorini/', '/history/'), ('/what-to-eat/', '/gastronomy/')):
            # Only the two non-navigation Discover More links remain at this point.
            updated = updated.replace(f'href="{old}"', f'href="{new}"')
    if 'data-submenu-only' in updated and SCRIPT not in updated:
        if '</body>' not in updated:
            raise ValueError(f'Missing closing body in {page}')
        updated = updated.replace('</body>', SCRIPT + '\n</body>', 1)
    remaining = HREF.findall(updated)
    if remaining:
        raise ValueError(f'Dead parent links remain in {page}: {remaining}')
    if updated != source:
        page.write_text(updated, encoding='utf-8')
    return count, int(updated != source)


def remove_landing_pages() -> None:
    for slug in PARENTS:
        folder = ROOT / slug
        landing = folder / 'index.html'
        if folder.exists():
            contents = list(folder.iterdir())
            if contents != [landing]:
                raise ValueError(f'Refusing to remove non-empty/nonstandard directory: {folder}')
            landing.unlink()
            folder.rmdir()
            print(f'Removed /{slug}/')
        legacy = ROOT / f'{slug}.html'
        if legacy.exists():
            legacy.unlink()
            print(f'Removed {legacy.name}')


def main() -> None:
    updated_pages = 0
    parent_labels = 0
    for page in pages():
        labels, changed = update_page(page)
        parent_labels += labels
        updated_pages += changed
    remove_landing_pages()
    print(f'Updated {updated_pages} pages; changed {parent_labels} parent labels')


if __name__ == '__main__':
    main()

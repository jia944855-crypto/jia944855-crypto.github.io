#!/usr/bin/env python3
"""Keep only Kamari and Perivolos cards in the local Beaches listing."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'beaches' / 'index.html'
CSS = ROOT / 'wp-content' / 'uploads' / 'elementor' / 'css' / 'post-922.css'
BACKUP = ROOT / 'route-migration-backup-20260922' / 'beaches-before-card-prune.html'
REMOVE_POST_IDS = ('1577', '1576', '1574')
KEEP_POST_IDS = ('1575', '1573')
DIV_TAG = re.compile(r'</?div\b[^>]*>', re.I)


def card_span(source: str, post_id: str) -> tuple[int, int]:
    opener = re.search(
        rf'<div\b(?=[^>]*\bclass="jet-listing-grid__item\b[^\"]*")'
        rf'(?=[^>]*\bdata-post-id="{post_id}")[^>]*>',
        source,
    )
    if opener is None:
        raise ValueError(f'Card {post_id} not found')
    depth = 0
    for tag in DIV_TAG.finditer(source, opener.start()):
        depth += -1 if tag.group().lower().startswith('</') else 1
        if depth == 0:
            return opener.start(), tag.end()
    raise ValueError(f'Card {post_id} has no closing div')


def set_two_column_css() -> None:
    css = CSS.read_text(encoding='utf-8')
    old = 'elementor-element-7bfc3da > .jet-listing-grid > .jet-listing-grid__items{--columns:3;}'
    new = 'elementor-element-7bfc3da > .jet-listing-grid > .jet-listing-grid__items{--columns:2;}'
    if old in css:
        CSS.write_text(css.replace(old, new, 1), encoding='utf-8')
    elif new not in css:
        raise ValueError('Beach listing CSS column rule not found')


def main() -> None:
    source = PAGE.read_text(encoding='utf-8')
    if all(f'data-post-id="{item}"' not in source for item in REMOVE_POST_IDS):
        set_two_column_css()
        print('The three beach cards are already removed')
        return
    if not BACKUP.exists():
        shutil.copy2(PAGE, BACKUP)

    spans = sorted((card_span(source, item) for item in REMOVE_POST_IDS), reverse=True)
    if any(lower_end > higher_start for (_, lower_end), (higher_start, _) in zip(spans[1:], spans)):
        raise ValueError('Beach card ranges overlap')
    updated = source
    for start, end in spans:
        updated = updated[:start] + updated[end:]

    replacements = (
        ('grid-col-desk-3 grid-col-tablet-3 grid-col-mobile-1',
         'grid-col-desk-2 grid-col-tablet-2 grid-col-mobile-1'),
        ('&quot;columns&quot;:3', '&quot;columns&quot;:2'),
        ('&quot;columns_tablet&quot;:3', '&quot;columns_tablet&quot;:2'),
    )
    for old, new in replacements:
        if old not in updated:
            raise ValueError(f'Expected listing setting not found: {old}')
        updated = updated.replace(old, new)

    for post_id in REMOVE_POST_IDS:
        if f'data-post-id="{post_id}"' in updated:
            raise ValueError(f'Unwanted card {post_id} remains')
    for post_id in KEEP_POST_IDS:
        if updated.count(f'data-post-id="{post_id}"') != 1:
            raise ValueError(f'Retained card {post_id} is missing or duplicated')
    for broken in ('hidden-beaches/', 'vlychada/', 'perissa/'):
        if broken in updated:
            raise ValueError(f'Broken card link remains: {broken}')
    for valid in ('href="/beachescpt/kamari/"', 'href="/beachescpt/perivolos/"'):
        if valid not in updated:
            raise ValueError(f'Retained local link missing: {valid}')

    PAGE.write_text(updated, encoding='utf-8')
    set_two_column_css()
    print(f'Removed {len(spans)} cards; retained Kamari and Perivolos in a two-column listing')
    print(f'Original page backed up at {BACKUP}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Keep only Oia and Fira in the local Villages listing."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from prune_beach_cards import card_span


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'villages' / 'index.html'
CSS = ROOT / 'wp-content' / 'uploads' / 'elementor' / 'css' / 'post-446.css'
BACKUP = ROOT / 'route-migration-backup-20260922' / 'villages-before-card-prune.html'
KEEP = {'1597': ('Oia', '/villagescpt/oia/'), '1590': ('Fira', '/villagescpt/fira/')}
CARD_IDS = re.compile(r'<div class="jet-listing-grid__item\b[^>]*data-post-id="(\d+)"')


def set_two_column_css() -> None:
    css = CSS.read_text(encoding='utf-8')
    old = 'elementor-element-6a8f6aa > .jet-listing-grid > .jet-listing-grid__items{--columns:3;}'
    new = 'elementor-element-6a8f6aa > .jet-listing-grid > .jet-listing-grid__items{--columns:2;}'
    if old in css:
        CSS.write_text(css.replace(old, new, 1), encoding='utf-8')
    elif new not in css:
        raise ValueError('Villages three-column CSS rule not found')


def main() -> None:
    source = PAGE.read_text(encoding='utf-8')
    found = CARD_IDS.findall(source)
    if found == list(KEEP):
        set_two_column_css()
        print('Villages listing already has only Oia and Fira')
        return
    if len(found) != 12 or len(set(found)) != 12 or not set(KEEP).issubset(found):
        raise ValueError(f'Unexpected Villages card inventory: {found}')
    if not BACKUP.exists():
        shutil.copy2(PAGE, BACKUP)

    remove = [post_id for post_id in found if post_id not in KEEP]
    spans = sorted((card_span(source, post_id) for post_id in remove), reverse=True)
    if any(lower_end > higher_start for (_, lower_end), (higher_start, _) in zip(spans[1:], spans)):
        raise ValueError('Villages card ranges overlap')
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

    if CARD_IDS.findall(updated) != list(KEEP):
        raise ValueError('Oia/Fira card inventory or order changed unexpectedly')
    if 'index.htmlvillagescpt/' in updated:
        raise ValueError('Broken Villages card URL remains')
    for name, path in KEEP.values():
        if f'>{name}</h2>' not in updated or f'href="{path}"' not in updated:
            raise ValueError(f'Retained {name} card or link missing')

    PAGE.write_text(updated, encoding='utf-8')
    set_two_column_css()
    print(f'Removed {len(remove)} cards; kept Oia and Fira side by side')
    print(f'Original page backed up at {BACKUP}')


if __name__ == '__main__':
    main()

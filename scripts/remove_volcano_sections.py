#!/usr/bin/env python3
"""Remove only the History module from the local volcano page."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'volcano' / 'index.html'
CSS = ROOT / 'wp-content' / 'uploads' / 'elementor' / 'css' / 'post-1397.css'
BACKUP = ROOT / 'route-migration-backup-20260922' / 'volcano-before-section-removal.html'
DIV_TAG = re.compile(r'</?div\b[^>]*>', re.I)
REMOVE_IDS = (
    '32bdaa68',  # The Minoan Eruption button
    '3c65307e',  # A window to the past heading
    '5290b2e7',  # complete historical section, including its text and dividers
)
HISTORY_BACKGROUND = ('background-image:url("https://santorini.gr/wp-content/uploads/'
                      '2025/01/shutterstock_2370032955-1.jpg");')


def element_span(source: str, element_id: str) -> tuple[int, int]:
    opener = re.search(
        rf'<div\b(?=[^>]*\bdata-id="{re.escape(element_id)}")[^>]*>',
        source,
        re.I,
    )
    if opener is None:
        raise ValueError(f'Could not find Elementor module {element_id}')
    depth = 0
    for tag in DIV_TAG.finditer(source, opener.start()):
        depth += -1 if tag.group().lower().startswith('</') else 1
        if depth == 0:
            return opener.start(), tag.end()
    raise ValueError(f'Unclosed Elementor module {element_id}')


def main() -> None:
    source = PAGE.read_text(encoding='utf-8')
    if 'data-id="5290b2e7"' not in source:
        css = CSS.read_text(encoding='utf-8')
        if HISTORY_BACKGROUND in css:
            CSS.write_text(css.replace(HISTORY_BACKGROUND, ''), encoding='utf-8')
            print('Removed lingering historical lava background reference')
        else:
            print('Volcano sections already removed; no changes made')
        return
    if not BACKUP.exists():
        shutil.copy2(PAGE, BACKUP)

    spans = sorted((element_span(source, item) for item in REMOVE_IDS), reverse=True)
    if any(lower_end > higher_start for (_, lower_end), (higher_start, _) in zip(spans[1:], spans)):
        raise ValueError('Module ranges overlap; refusing to edit')
    updated = source
    for start, end in spans:
        updated = updated[:start] + updated[end:]

    old_intro = ('Discover the ancient secrets and fascinating geology of the world-famous '
                 'volcano of Santorini, which shaped the island and defined its fate with the '
                 'massive Minoan Eruption, known to be among the largest volcanic eruptions in history.')
    new_intro = ('Discover the ancient secrets and fascinating geology of the world-famous '
                 'volcano of Santorini.')
    if updated.count(old_intro) != 2:
        raise ValueError('Unexpected intro/metadata; refusing to edit')
    updated = updated.replace(old_intro, new_intro)
    old_meta = ('The Volcano of Santorini ' + new_intro +
                ' The Creation of Santorini The Minoan Eruption Koloumpos Volcano '
                'Visiting the Volcano Listen To The [&hellip;]')
    new_meta = ('The Volcano of Santorini ' + new_intro +
                ' The Creation of Santorini Koloumpos Volcano Visiting the Volcano.')
    if old_meta not in updated:
        raise ValueError('Unexpected Open Graph description; refusing to edit')
    updated = updated.replace(old_meta, new_meta, 1)

    for forbidden in ('id="eruption"', 'href="/volcano/#eruption"', 'Historical Times'):
        if forbidden in updated:
            raise ValueError(f'Removed content still present: {forbidden}')
    for retained in ('id="creation"', 'id="koloumpos"', 'id="visiting"', 'elementor-tab-content-2971',
                     '8_kyellow_10016.jpg'):
        if retained not in updated:
            raise ValueError(f'Retained content missing: {retained}')

    css = CSS.read_text(encoding='utf-8')
    trimmed_css = css.replace(HISTORY_BACKGROUND, '')

    PAGE.write_text(updated, encoding='utf-8')
    CSS.write_text(trimmed_css, encoding='utf-8')
    print(f'Removed {len(spans)} historical modules')
    print(f'Original page backed up at {BACKUP}')


if __name__ == '__main__':
    main()

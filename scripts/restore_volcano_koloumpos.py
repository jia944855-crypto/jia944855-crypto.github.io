#!/usr/bin/env python3
"""Restore the Koloumpos panel from the local backup, leaving History removed.

The original post-1397.css is read from stdin so its five Koloumpos rules can
be restored in the exact original responsive locations without touching other
local CSS changes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from remove_volcano_sections import element_span, HISTORY_BACKGROUND


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'volcano' / 'index.html'
BACKUP = ROOT / 'route-migration-backup-20260922' / 'volcano-before-section-removal.html'
CSS = ROOT / 'wp-content' / 'uploads' / 'elementor' / 'css' / 'post-1397.css'
KOLOUMPOS_RULE = re.compile(r'[^{}]*elementor-element-eb62c3d[^{}]*\{[^{}]*\}')


def extract(source: str, element_id: str) -> str:
    start, end = element_span(source, element_id)
    return source[start:end]


def main() -> None:
    source = PAGE.read_text(encoding='utf-8')
    backup = BACKUP.read_text(encoding='utf-8')
    if 'data-id="5290b2e7"' in source:
        raise ValueError('Historical module unexpectedly present; refusing to modify')
    if 'data-id="eb62c3d"' in source:
        print('Koloumpos already restored')
        return

    original_css = sys.stdin.read()
    local_css = CSS.read_text(encoding='utf-8')
    without_koloumpos = KOLOUMPOS_RULE.sub('', original_css).replace(HISTORY_BACKGROUND, '')
    if without_koloumpos != local_css:
        raise ValueError('Local CSS differs from the expected original; refusing to overwrite')
    restored_css = original_css.replace(HISTORY_BACKGROUND, '')
    if len(KOLOUMPOS_RULE.findall(restored_css)) != 5:
        raise ValueError('Expected exactly five Koloumpos CSS rules')

    button = extract(backup, '4b49f34d')
    panel = extract(backup, 'eb62c3d')
    button_target = '<div class="elementor-element elementor-element-1c65b85 '
    panel_target = '<div class="elementor-element elementor-element-1e5e38c9 '
    if source.count(button_target) != 1 or source.count(panel_target) != 1:
        raise ValueError('Expected insertion points not found exactly once')
    updated = source.replace(button_target, button + '\n\t\t\t\t' + button_target, 1)
    updated = updated.replace(panel_target, panel + '\n\t\t' + panel_target, 1)
    updated = updated.replace(
        'The Creation of Santorini Visiting the Volcano.',
        'The Creation of Santorini Koloumpos Volcano Visiting the Volcano.',
        1,
    )
    if 'id="koloumpos"' not in updated or 'href="/volcano/#koloumpos"' not in updated:
        raise ValueError('Koloumpos panel or navigation was not restored')
    if 'id="eruption"' in updated or 'Historical Times' in updated:
        raise ValueError('Historical module was inadvertently restored')

    PAGE.write_text(updated, encoding='utf-8')
    CSS.write_text(restored_css, encoding='utf-8')
    print('Restored Koloumpos panel, button and exact original responsive CSS')


if __name__ == '__main__':
    main()

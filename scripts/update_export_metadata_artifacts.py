#!/usr/bin/env python3
"""Deterministic updates for index/manifest metadata using runtime export timestamp."""
from __future__ import annotations
import json, re
from pathlib import Path

def update_index_timestamp(index_path: Path, generated_utc: str) -> bool:
    txt = index_path.read_text(encoding='utf-8')
    new = re.sub(r'(<strong>Generated \(UTC\):</strong>\s*)[^<]+', lambda m: m.group(1) + generated_utc, txt, count=1)
    if new != txt:
        index_path.write_text(new, encoding='utf-8')
        return True
    return False

def update_manifests(export_dir: Path, generated_utc: str, note: str) -> bool:
    changed = False
    jp = export_dir / 'EXPORT_MANIFEST.json'
    if jp.exists():
        data = json.loads(jp.read_text(encoding='utf-8'))
        if data.get('export_timestamp_utc') != generated_utc:
            data['export_timestamp_utc'] = generated_utc
            changed = True
        notes = data.get('notes')
        if isinstance(notes, list):
            if note not in notes:
                notes.append(note); changed = True
        elif isinstance(notes, str):
            if note not in notes:
                data['notes'] = notes + '\n' + note; changed = True
        else:
            data['notes'] = [note]; changed = True
        if changed:
            jp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    mp = export_dir / 'EXPORT_MANIFEST.md'
    if mp.exists():
        txt = mp.read_text(encoding='utf-8')
        new = re.sub(r'(- Export timestamp \(UTC\): `)([^`]+)(`[^\n]*)', lambda m: m.group(1)+generated_utc+m.group(3), txt, count=1)
        if note not in new:
            new = new.replace('\n## Broken internal links', f'\n- Note: {note}\n\n## Broken internal links', 1)
        if new != txt:
            mp.write_text(new, encoding='utf-8')
            changed = True
    return changed

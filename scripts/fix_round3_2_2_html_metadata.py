#!/usr/bin/env python3
"""Safe correction helper for Round 3.2.2 HTML export metadata.

Fixes malformed generated-timestamp metadata caused by unsafe regex replacement
where a digit-prefixed timestamp was concatenated after \1 (e.g. producing
`P26-...` artifacts). Uses an unambiguous replacement to preserve the label.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERN = re.compile(r'(<strong>Generated \(UTC\):</strong>\s*)[^<]+')
MALFORMED = re.compile(r'P\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')


def fix_file(path: Path, utc_timestamp: str | None = None) -> bool:
    text = path.read_text(encoding='utf-8')
    original = text

    # Correct already-malformed `P26-...` artifacts while restoring the label.
    if 'P26-' in text or MALFORMED.search(text):
        text = re.sub(
            r'<br>P(\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)(</div>)',
            lambda m: f'<br><strong>Generated (UTC):</strong> 20{m.group(1)}{m.group(2)}',
            text,
        )
        text = re.sub(
            r'(<strong>Generated \(UTC\):</strong>\s*)P(\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)',
            lambda m: m.group(1) + '20' + m.group(2),
            text,
        )

    # If an explicit timestamp is provided, apply safely (never r"\1"+digits).
    if utc_timestamp is not None:
        text = PATTERN.sub(lambda m: m.group(1) + utc_timestamp, text)

    if text != original:
        path.write_text(text, encoding='utf-8')
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--utc-timestamp', dest='utc_timestamp')
    args = ap.parse_args()
    changed = 0
    for p in args.paths:
        if fix_file(Path(p), args.utc_timestamp):
            print(f'fixed {p}')
            changed += 1
        else:
            print(f'unchanged {p}')
    print(f'changed={changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

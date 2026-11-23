#!/usr/bin/env python3
"""Correct malformed `Generated (UTC)` metadata in exported HTML files.

Integrated with the corrected exporter formatting approach: restores the label and
emits the timestamp as a separate value without regex backreference concatenation.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from export_cares_documentation_html import format_generated_meta
except Exception:  # fallback for direct execution contexts
    import html
    def format_generated_meta(timestamp_utc: str) -> str:
        return f"<strong>Generated (UTC):</strong> {html.escape(timestamp_utc)}"

MALFORMED_RE = re.compile(r'<br>\s*P(\d{2})(-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*</div>')
# Also repair cases where label/value block is malformed but year was preserved oddly.
LABEL_BLOCK_RE = re.compile(r'(<div class="meta">.*?<strong>Generated \(UTC\):</strong>\s*)([^<]+)(</div>)', re.S)


def repair_metadata(html_text: str, timestamp_utc: str | None = None) -> tuple[str, bool]:
    original = html_text
    if 'P26-' in html_text or MALFORMED_RE.search(html_text):
        # restore from malformed PYY-... form to 20YY-...
        def repl(m: re.Match[str]) -> str:
            ts = timestamp_utc or f"20{m.group(1)}{m.group(2)}"
            return f"<br>{format_generated_meta(ts)}</div>"
        html_text = MALFORMED_RE.sub(repl, html_text)
    return html_text, html_text != original


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--timestamp-utc')
    args = ap.parse_args(argv)
    changed = 0
    for p in [Path(x) for x in args.paths]:
        txt = p.read_text(encoding='utf-8')
        new, did = repair_metadata(txt, args.timestamp_utc)
        if did:
            p.write_text(new, encoding='utf-8')
            changed += 1
            print(f'fixed {p}')
    print(f'changed={changed}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

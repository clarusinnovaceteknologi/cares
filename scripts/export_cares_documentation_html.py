#!/usr/bin/env python3
"""
Deterministic CARES documentation HTML exporter (corrected normal pipeline).

Key guarantees for Round 3.2.2.2:
- Metadata label and UTC timestamp are emitted as separate, correctly formatted
  HTML elements (no regex backreference concatenation on digit-prefixed timestamps).
- Export timestamp is taken from actual runtime UTC at export execution.
- ZIP is written outside the export directory and never includes nested archives.
- Complete export package is assembled: regenerated pages for available sources and
  preserved carried-forward exported artifacts where source markdown is unavailable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import zipfile
from pathlib import Path

try:
    from markdown_it import MarkdownIt
except Exception as e:  # pragma: no cover
    raise SystemExit(f"markdown-it-py is required: {e}")

EXPORT_DIR_NAME = "cares-documentation-html"
ZIP_NAME = "CARES_DOCUMENTATION_HTML.zip"
CSS_BLOCK = r""":root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--border:#d1d9e0;--link:#0969da;--code-bg:#f6f8fa;--pre-bg:#f6f8fa;--table-header:#f6f8fa;--nav-bg:#f6f8fa}
@media (prefers-color-scheme: dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--border:#30363d;--link:#4493f8;--code-bg:#161b22;--pre-bg:#161b22;--table-header:#161b22;--nav-bg:#161b22}}
*{box-sizing:border-box} body{margin:0;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg)}
.wrap{max-width:1100px;margin:0 auto;padding:24px}
.topbar{background:var(--nav-bg);border-bottom:1px solid var(--border);padding:10px 24px;position:sticky;top:0;z-index:5}
.topbar a{color:var(--link);text-decoration:none;font-weight:600}
.meta{color:var(--muted);font-size:13px;margin:8px 0 20px}
article{padding-bottom:40px}
h1,h2,h3,h4,h5,h6{line-height:1.25;margin-top:1.4em;margin-bottom:.6em}
h1{font-size:2em;border-bottom:1px solid var(--border);padding-bottom:.3em}
h2{font-size:1.5em;border-bottom:1px solid var(--border);padding-bottom:.3em}
a{color:var(--link)} code{background:var(--code-bg);padding:.15em .35em;border-radius:6px;font-size:.9em}
pre{background:var(--pre-bg);padding:16px;overflow:auto;border-radius:8px;border:1px solid var(--border)}
pre code{background:none;padding:0;font-size:.9em}
table{border-collapse:collapse;width:100%;margin:1em 0;display:block;overflow:auto}
th,td{border:1px solid var(--border);padding:8px 12px;vertical-align:top}
th{background:var(--table-header)} blockquote{margin:0;padding:0 1em;color:var(--muted);border-left:4px solid var(--border)}
img{max-width:100%;height:auto} hr{border:0;border-top:1px solid var(--border);margin:24px 0}
ul,ol{padding-left:2em}
.mermaid{background:var(--pre-bg);border:1px solid var(--border);border-radius:8px;padding:12px}
.hljs .k,.hljs .kd,.hljs .kn,.hljs .kr{font-weight:600}

pre { line-height: 125%; }
td.linenos .normal { color: inherit; background-color: transparent; padding-left: 5px; padding-right: 5px; }
span.linenos { color: inherit; background-color: transparent; padding-left: 5px; padding-right: 5px; }
td.linenos .special { color: #000000; background-color: #ffffc0; padding-left: 5px; padding-right: 5px; }
span.linenos.special { color: #000000; background-color: #ffffc0; padding-left: 5px; padding-right: 5px; }
.hljs .hll { background-color: #ffffcc }
.hljs { background: #f8f8f8; }
.hljs .c { color: #3D7B7B; font-style: italic } /* Comment */
.hljs .err { border: 1px solid #F00 } /* Error */
.hljs .k { color: #008000; font-weight: bold } /* Keyword */
.hljs .o { color: #666 } /* Operator */
.hljs .ch { color: #3D7B7B; font-style: italic } /* Comment.Hashbang */
.hljs .cm { color: #3D7B7B; font-style: italic } /* Comment.Multiline */
.hljs .cp { color: #9C6500 } /* Comment.Preproc */
.hljs .cpf { color: #3D7B7B; font-style: italic } /* Comment.PreprocFile */
.hljs .c1 { color: #3D7B7B; font-style: italic } /* Comment.Single */
.hljs .cs { color: #3D7B7B; font-style: italic } /* Comment.Special */
.hljs .gd { color: #A00000 } /* Generic.Deleted */
.hljs .ge { font-style: italic } /* Generic.Emph */
.hljs .ges { font-weight: bold; font-style: italic } /* Generic.EmphStrong */
.hljs .gr { color: #E40000 } /* Generic.Error */
.hljs .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.hljs .gi { color: #008400 } /* Generic.Inserted */
.hljs .go { color: #717171 } /* Generic.Output */
.hljs .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.hljs .gs { font-weight: bold } /* Generic.Strong */
.hljs .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.hljs .gt { color: #04D } /* Generic.Traceback */
.hljs .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.hljs .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.hljs .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.hljs .kp { color: #008000 } /* Keyword.Pseudo */
.hljs .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.hljs .kt { color: #B00040 } /* Keyword.Type */
.hljs .m { color: #666 } /* Literal.Number */
.hljs .s { color: #BA2121 } /* Literal.String */
.hljs .na { color: #687822 } /* Name.Attribute */
.hljs .nb { color: #008000 } /* Name.Builtin */
.hljs .nc { color: #00F; font-weight: bold } /* Name.Class */
.hljs .no { color: #800 } /* Name.Constant */
.hljs .nd { color: #A2F } /* Name.Decorator */
.hljs .ni { color: #717171; font-weight: bold } /* Name.Entity */
.hljs .ne { color: #CB3F38; font-weight: bold } /* Name.Exception */
.hljs .nf { color: #00F } /* Name.Function */
.hljs .nl { color: #767600 } /* Name.Label */
.hljs .nn { color: #00F; font-weight: bold } /* Name.Namespace */
.hljs .nt { color: #008000; font-weight: bold } /* Name.Tag */
.hljs .nv { color: #19177C } /* Name.Variable */
.hljs .ow { color: #A2F; font-weight: bold } /* Operator.Word */
.hljs .w { color: #BBB } /* Text.Whitespace */
.hljs .mb { color: #666 } /* Literal.Number.Bin */
.hljs .mf { color: #666 } /* Literal.Number.Float */
.hljs .mh { color: #666 } /* Literal.Number.Hex */
.hljs .mi { color: #666 } /* Literal.Number.Integer */
.hljs .mo { color: #666 } /* Literal.Number.Oct */
.hljs .sa { color: #BA2121 } /* Literal.String.Affix */
.hljs .sb { color: #BA2121 } /* Literal.String.Backtick */
.hljs .sc { color: #BA2121 } /* Literal.String.Char */
.hljs .dl { color: #BA2121 } /* Literal.String.Delimiter */
.hljs .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.hljs .s2 { color: #BA2121 } /* Literal.String.Double */
.hljs .se { color: #AA5D1F; font-weight: bold } /* Literal.String.Escape */
.hljs .sh { color: #BA2121 } /* Literal.String.Heredoc */
.hljs .si { color: #A45A77; font-weight: bold } /* Literal.String.Interpol */
.hljs .sx { color: #008000 } /* Literal.String.Other */
.hljs .sr { color: #A45A77 } /* Literal.String.Regex */
.hljs .s1 { color: #BA2121 } /* Literal.String.Single */
.hljs .ss { color: #19177C } /* Literal.String.Symbol */
.hljs .bp { color: #008000 } /* Name.Builtin.Pseudo */
.hljs .fm { color: #00F } /* Name.Function.Magic */
.hljs .vc { color: #19177C } /* Name.Variable.Class */
.hljs .vg { color: #19177C } /* Name.Variable.Global */
.hljs .vi { color: #19177C } /* Name.Variable.Instance */
.hljs .vm { color: #19177C } /* Name.Variable.Magic */
.hljs .il { color: #666 } /* Literal.Number.Integer.Long */
"""

MD_LINK_RE = re.compile(r'(!)?\[((?:[^\]\\]|\\.)*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_generated_meta(timestamp_utc: str) -> str:
    # Emit label and value as separate nodes; never concatenate timestamp after \1.
    return f"<strong>Generated (UTC):</strong> {html.escape(timestamp_utc)}"


def build_meta_block(*, source: str | None, generated_utc: str, extra: str | None = None) -> str:
    parts = []
    if source is not None:
        parts.append(f"<strong>Source:</strong> <code>{html.escape(source)}</code>")
    parts.append(format_generated_meta(generated_utc))
    if extra:
        parts.append(extra)
    return '<div class="meta">' + '<br>'.join(parts) + '</div>'


def make_md() -> MarkdownIt:
    return MarkdownIt("gfm-like")


def rewrite_md_links(markdown_text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        bang, label, target = m.group(1) or "", m.group(2), m.group(3)
        if bang == "!":
            return m.group(0)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        # split fragment/query
        frag = ""
        base = target
        if "#" in base:
            base, frag = base.split("#", 1)
            frag = "#" + frag
        lower = base.lower()
        if lower == "readme.md" or lower.endswith("/readme.md"):
            base = base[:-3] + ".html"  # README.md -> README.html (preserve path)
        elif base.endswith(".md"):
            base = base + ".html"
        elif base == "README" or base.endswith("/README"):
            base = base + ".html"
        return f"[{label}]({base}{frag})"
    return MD_LINK_RE.sub(repl, markdown_text)


def page_shell(*, title: str, topbar_href: str, meta_html: str, body_html: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n"
        "<style>\n" + CSS_BLOCK + "</style>\n"
        "</head>\n"
        "<body>\n"
        f'<div class="topbar"><a href="{html.escape(topbar_href)}">← Documentation index</a></div>\n'
        '<div class="wrap">\n'
        f"{meta_html}\n"
        '<article class="markdown-body">\n'
        f"{body_html}\n"
        '</article>\n'
        '</div>\n\n'
        "</body>\n"
        "</html>\n"
    )


def index_shell(*, generated_utc: str, body_html: str, title: str = "CARES Documentation Index") -> str:
    meta = build_meta_block(source=None, generated_utc=generated_utc, extra="<strong>Total exported documents:</strong> 64")
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n"
        "<style>\n" + CSS_BLOCK + "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="wrap">\n'
        f"<h1>{html.escape(title)}</h1>\n"
        f"{meta}\n"
        '<article class="markdown-body">\n'
        f"{body_html}\n"
        '</article>\n'
        '</div>\n\n'
        "</body>\n"
        "</html>\n"
    )


def render_markdown_page(md_path: Path, repo_root: Path, generated_utc: str) -> str:
    source_rel = md_path.relative_to(repo_root).as_posix()
    md_text = md_path.read_text(encoding="utf-8")
    md_text = rewrite_md_links(md_text)
    md = make_md()
    body = md.render(md_text)
    # title from first h1 if present
    m = re.search(r'^#\s+(.+)$', md_path.read_text(encoding='utf-8'), re.M)
    title = m.group(1).strip() if m else Path(source_rel).name
    out_rel = ("README.html" if source_rel == "README.md" else source_rel + ".html")
    depth = len(Path(out_rel).parts) - 1
    topbar = "../" * depth + "index.html" if depth > 0 else "index.html"
    meta = build_meta_block(source=source_rel, generated_utc=generated_utc)
    return page_shell(title=title, topbar_href=topbar, meta_html=meta, body_html=body.rstrip())


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_zip(export_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    files = []
    for p in sorted(export_dir.rglob('*')):
        if not p.is_file():
            continue
        # Never include nested archives or the target zip itself.
        if p.suffix.lower() == '.zip' or p.name == ZIP_NAME:
            continue
        files.append(p)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            arc = (export_dir.parent.name + '/' + p.relative_to(export_dir).as_posix())
            # normalize to expected top-level folder name
            arc = EXPORT_DIR_NAME + '/' + p.relative_to(export_dir).as_posix()
            z.write(p, arc)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--export-dir', default=None)
    ap.add_argument('--zip-path', default=None)
    ap.add_argument('--generated-utc', default=None, help='Override UTC timestamp (testing only).')
    ap.add_argument('--regenerate-available-sources', action='store_true', default=True)
    args = ap.parse_args(argv)
    repo = Path(args.repo_root).resolve()
    export_dir = Path(args.export_dir).resolve() if args.export_dir else (repo / 'dist' / EXPORT_DIR_NAME)
    zip_path = Path(args.zip_path).resolve() if args.zip_path else (repo / 'dist' / ZIP_NAME)
    gen = args.generated_utc or now_utc_iso()
    export_dir.mkdir(parents=True, exist_ok=True)

    # Determine mapping from existing manifest if present; otherwise derive.
    manifest_path = export_dir / 'EXPORT_MANIFEST.json'
    mapping = []
    if manifest_path.exists():
        try:
            m = json.loads(manifest_path.read_text(encoding='utf-8'))
            mapping = m.get('source_to_output_mapping') or []
        except Exception:
            mapping = []
    if not mapping:
        # derive from existing export htmls + sources
        if (export_dir / 'README.html').exists():
            mapping.append({'source': 'README.md', 'output': 'README.html', 'status': 'converted'})
        for p in sorted(export_dir.rglob('*.md.html')):
            rel = p.relative_to(export_dir).as_posix()
            src = rel[:-5]  # strip .html -> .md
            mapping.append({'source': src, 'output': rel, 'status': 'converted'})

    regenerated = []
    carried = []
    failed = []
    for item in mapping:
        src = item['source']
        out_rel = item['output']
        src_path = repo / src
        out_path = export_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.exists():
            try:
                html_text = render_markdown_page(src_path, repo, gen)
                out_path.write_text(html_text, encoding='utf-8')
                regenerated.append(out_rel)
            except Exception as e:
                failed.append({'source': src, 'output': out_rel, 'error': str(e)})
        else:
            # preserve carried-forward artifact as-is if present
            if out_path.exists():
                carried.append(out_rel)
            else:
                failed.append({'source': src, 'output': out_rel, 'error': 'missing source and missing carried-forward export'})

    # Update index and manifest metadata to actual runtime export timestamp so package artifacts are consistent.
    try:
        from update_export_metadata_artifacts import update_index_timestamp, update_manifests
    except Exception:
        update_index_timestamp = None
        update_manifests = None
    index_path = export_dir / 'index.html'
    if update_index_timestamp and index_path.exists():
        update_index_timestamp(index_path, gen)
    if update_manifests:
        note = f"Round 3.2.2.2: export regenerated via corrected normal pipeline (actual runtime UTC {gen}); metadata emission fixed to prevent regex-backreference corruption; ZIP rebuilt without nested archives."
        update_manifests(export_dir, gen, note)

    # Ensure copilot.txt is present in export dir if convention requires (copy from repo root if exists)
    root_copilot = repo / 'copilot.txt'
    if root_copilot.exists():
        shutil.copy2(root_copilot, export_dir / 'copilot.txt')

    # Rebuild ZIP (never inside export dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    build_zip(export_dir, zip_path)

    # Minimal run report to stdout (machine-readable)
    result = {
        'generated_utc': gen,
        'regenerated_count': len(regenerated),
        'carried_forward_count': len(carried),
        'failed': failed,
        'zip_path': str(zip_path),
        'zip_exists': zip_path.exists(),
    }
    print(json.dumps(result, indent=2))
    return 1 if failed else 0

if __name__ == '__main__':
    raise SystemExit(main())

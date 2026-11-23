import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import export_cares_documentation_html as exporter  # noqa: E402


class MetadataFormattingTests(unittest.TestCase):
    def assert_valid_generated_meta(self, html_text: str, ts: str):
        self.assertIn('<strong>Generated (UTC):</strong> ' + ts, html_text)
        self.assertNotIn('P26-', html_text)
        self.assertNotRegex(html_text, r'<br>\s*P\d{2}-')

    def test_format_generated_meta_preserves_label_and_separates_digits(self):
        # If someone incorrectly used re.sub(r'(label)', r'\1'+ts), a digit-leading
        # timestamp could be interpreted as part of the backreference (\12, etc.).
        for ts in [
            '2026-11-23T11:30:53Z',  # begins with 2026 (would trigger \12 in naive code)
            '1999-01-02T03:04:05Z',  # another valid year
            '2024-02-29T00:00:00Z',  # expected UTC ISO-8601 format
            '2099-12-31T23:59:59Z',
        ]:
            meta = exporter.format_generated_meta(ts)
            self.assertEqual(meta, f'<strong>Generated (UTC):</strong> {ts}')
            self.assertTrue(meta.startswith('<strong>Generated (UTC):</strong> '))
            self.assertNotIn('P26', meta)

    def test_build_meta_block_source_and_label(self):
        block = exporter.build_meta_block(source='docs/X.md', generated_utc='2026-11-23T11:30:53Z')
        self.assertIn('<div class="meta">', block)
        self.assertIn('<strong>Source:</strong> <code>docs/X.md</code><br>', block)
        self.assertIn('<strong>Generated (UTC):</strong> 2026-11-23T11:30:53Z</div>', block)
        self.assertNotIn('P26-', block)

    def test_page_shell_no_unintended_modification(self):
        body = '<p>Hello <em>world</em> &amp; <code>x</code></p>\n<pre><code>keep me</code></pre>'
        meta = exporter.build_meta_block(source='README.md', generated_utc='2026-11-23T11:30:53Z')
        page = exporter.page_shell(title='T', topbar_href='index.html', meta_html=meta, body_html=body)
        self.assertIn(body, page)
        self.assert_valid_generated_meta(page, '2026-11-23T11:30:53Z')
        self.assertIn('href="index.html"', page)


class ExporterPathTests(unittest.TestCase):
    def test_render_markdown_page_uses_runtime_timestamp_and_safe_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = root / 'docs'
            docs.mkdir()
            md = docs / 'SAMPLE.md'
            md.write_text('# Title\n\nParagraph with [link](OTHER.md).\n', encoding='utf-8')
            ts = '2026-11-23T13:05:48Z'
            html_text = exporter.render_markdown_page(md, root, ts)
            self.assertIn('<title>Title</title>', html_text)
            self.assertIn('<strong>Source:</strong> <code>docs/SAMPLE.md</code><br><strong>Generated (UTC):</strong> 2026-11-23T13:05:48Z</div>', html_text)
            self.assertIn('href="OTHER.md.html"', html_text)
            self.assertNotIn('P26-', html_text)
            self.assertIn('<p>Paragraph with <a href="OTHER.md.html">link</a>.</p>', html_text)

    def test_full_exporter_run_generates_correct_metadata_and_no_nested_zip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'dist').mkdir()
            export_dir = root / 'dist' / 'cares-documentation-html'
            export_dir.mkdir()
            # seed minimal prior export with carried-forward asset and mapping
            (export_dir / 'assets').mkdir()
            (export_dir / 'assets' / 'mermaid.min.js').write_text('/*m*/', encoding='utf-8')
            (root / 'README.md').write_text('# R\n\nHi\n', encoding='utf-8')
            mapping = [{'source': 'README.md', 'output': 'README.html', 'status': 'converted'}]
            (export_dir / 'EXPORT_MANIFEST.json').write_text(json.dumps({
                'export_timestamp_utc': '2020-01-01T00:00:00Z',
                'source_to_output_mapping': mapping,
                'source_markdown_files_discovered': 1,
                'html_files_successfully_generated': 1,
                'failed_conversions': [],
                'missing_referenced_assets': [],
                'broken_internal_links': [],
                'files_not_converted_faithfully': [],
                'copied_assets': [],
                'notes': []
            }), encoding='utf-8')
            (export_dir / 'EXPORT_MANIFEST.md').write_text('# CARES Documentation HTML Export Manifest\n\n- Export timestamp (UTC): `2020-01-01T00:00:00Z` (old)\n\n## Broken internal links\n- None\n', encoding='utf-8')
            (export_dir / 'index.html').write_text('<div class="meta"><strong>Generated (UTC):</strong> 2020-01-01T00:00:00Z<br><strong>Total exported documents:</strong> 64</div>', encoding='utf-8')
            (root / 'copilot.txt').write_text('report', encoding='utf-8')
            ts = '2026-11-23T13:05:48Z'
            rc = exporter.main(['--repo-root', str(root), '--export-dir', str(export_dir), '--zip-path', str(root/'dist'/'CARES_DOCUMENTATION_HTML.zip'), '--generated-utc', ts])
            self.assertEqual(rc, 0)
            readme = (export_dir / 'README.html').read_text(encoding='utf-8')
            self.assertIn('<strong>Generated (UTC):</strong> 2026-11-23T13:05:48Z', readme)
            self.assertNotIn('P26-', readme)
            # no nested zip inside export dir
            self.assertFalse((export_dir / 'CARES_DOCUMENTATION_HTML.zip').exists())
            self.assertTrue((root / 'dist' / 'CARES_DOCUMENTATION_HTML.zip').exists())
            # index and manifests updated to runtime timestamp
            index_txt = (export_dir / 'index.html').read_text(encoding='utf-8')
            self.assertIn('2026-11-23T13:05:48Z', index_txt)
            man = json.loads((export_dir / 'EXPORT_MANIFEST.json').read_text(encoding='utf-8'))
            self.assertEqual(man['export_timestamp_utc'], '2026-11-23T13:05:48Z')

    def test_now_utc_iso_format(self):
        ts = exporter.now_utc_iso()
        self.assertRegex(ts, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')


if __name__ == '__main__':
    unittest.main()

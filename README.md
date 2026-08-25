# Document Smart Reader

Local-first, page-aware document reading for Codex. It converts PDF and DOCX files into a reusable Markdown cache, retrieves only the chunks relevant to the current question, and asks Codex to visually verify pages where layout can change meaning.

[![test](https://github.com/chr061208-code/document-smart-reader/actions/workflows/test.yml/badge.svg)](https://github.com/chr061208-code/document-smart-reader/actions/workflows/test.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[简体中文](README.zh-CN.md)

## Why

Converting a document to Markdown does not save context by itself. The saving comes from keeping the full conversion local and loading only the evidence needed for each question.

Document Smart Reader combines:

- local PDF/DOCX preprocessing;
- SHA-256 keyed cache reuse;
- source-page anchors in Markdown;
- Chinese and Latin search tokenization;
- ranked chunk retrieval without printing full document text;
- extraction-quality flags for scanned or complex pages;
- visual verification rules for tables, figures, formulas, forms, and multi-column layouts.

No document content is uploaded by the included script, and it makes no network requests.

## Supported formats

- Searchable PDF
- DOCX, preferably through LibreOffice-to-PDF conversion for stable page numbers

Scanned PDFs are detected as low/no-text pages but OCR is not bundled in this release. Legacy `.doc` files should first be converted to `.docx` or PDF.

## Install as a Codex plugin

Clone this repository, then add its repo-local marketplace and install the plugin:

```text
codex plugin marketplace add <absolute-path-to-this-repository>
codex plugin add document-smart-reader@document-smart-reader
```

Start a new Codex task after installation so the skill is discovered.

## Install only the skill

Copy this directory into your Codex skills directory:

```text
plugins/document-smart-reader/skills/document-smart-reader
```

Typical destination:

```text
~/.codex/skills/document-smart-reader
```

## Direct CLI use

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Prepare a document:

```bash
python plugins/document-smart-reader/skills/document-smart-reader/scripts/smart_read.py prepare report.pdf
```

The command prints the cache directory and compact manifest. Search it without printing the whole document:

```bash
python plugins/document-smart-reader/skills/document-smart-reader/scripts/smart_read.py query \
  "/path/to/reader-dir" "What are the main risk controls?" --limit 3
```

Set `CODEX_DOCUMENT_READER_CACHE` to override the cache location. Use `--output` for a one-off cache root and `--force` to rebuild.

## How Codex uses it

1. Build or reuse the local cache.
2. Read `manifest.json`, not the whole document.
3. Rank chunks for the user's question.
4. Load the smallest sufficient evidence set.
5. Cite original page anchors.
6. Render only relevant pages when layout or extraction quality requires it.

## Privacy and security

- Processing is local.
- The script has no telemetry and no network code.
- Cache files may contain document text. Store and delete them according to the sensitivity of the source document.
- The source file is never modified.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT

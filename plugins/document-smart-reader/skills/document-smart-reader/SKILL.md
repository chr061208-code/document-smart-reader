---
name: document-smart-reader
description: "Read, search, summarize, compare, or answer questions about local PDF and Word documents efficiently. Use for long PDFs/DOCX files, repeated questions about the same document, page-specific evidence, or when minimizing context and token use matters. Build a local page-aware Markdown cache, retrieve only relevant chunks, and visually verify complex or uncertain pages. Do not use for creating or editing documents."
---

# Document Smart Reader

Use local preprocessing to reduce model context without sacrificing source fidelity.

## Workflow

1. Run `scripts/smart_read.py prepare <file>` before reading a PDF or Word file. Do not read the whole generated Markdown by default.
2. Read the returned `manifest.json`. It contains page count, chunk paths, extraction warnings, and visual-review candidates.
3. For a user question, run `scripts/smart_read.py query <reader-dir> "<question>"`. Open only the ranked chunk files needed to answer, starting with the top results.
4. Expand to neighboring chunks only when a selected passage starts or ends mid-topic, evidence conflicts, or the answer is incomplete.
5. Cite the original document's page numbers from `<!-- source-page: N -->` anchors, not Markdown line numbers.
6. Visually inspect only the relevant original pages when layout can affect meaning. Use the installed PDF skill for rendering and page inspection.

## Reading modes

Choose automatically:

- **Quick**: prose-heavy lookup or summary. Use retrieved Markdown and spot-check only if extraction is suspicious.
- **Precise**: default for factual answers. Retrieve Markdown, inspect adjacent context, and render pages containing tables, figures, formulas, footnotes, or extraction warnings.
- **Layout**: formatting, signatures, annotations, pagination, or visual comparison. Render the requested pages; Markdown is only an index.

## Token rules

- Conversion and indexing happen locally; only content shown to the model consumes context.
- Load `manifest.json` and ranked chunks, never the full `document.md`, unless the user explicitly requests a complete close reading and the document is short.
- Begin with the smallest evidence set. Prefer 3 relevant chunks; raise the query limit only when needed.
- Reuse an existing cache when the source hash matches. Do not reconvert or rerender unchanged files.
- Do not OCR or render every page preemptively. Restrict expensive processing to relevant pages.
- For broad summaries, process one section at a time and keep a compact running synthesis rather than accumulating all source text.

## Accuracy gates

Render the original page before relying on extracted text when any of these apply:

- the manifest marks a page as `no_text`, `low_text`, or `possible_complex_layout`;
- the answer depends on a table, chart, equation, image, checkbox, signature, header/footer, footnote, or multi-column order;
- OCR may be involved, characters look corrupted, or values/units are ambiguous;
- neighboring chunks disagree or a sentence crosses a chunk boundary.

State uncertainty when source extraction remains ambiguous. Never invent missing text.

## Word handling

For DOCX, the script prefers LibreOffice conversion to cached PDF so page anchors match rendered pages. If conversion is unavailable, it falls back to structural DOCX extraction and uses paragraph/section anchors; disclose that page numbers are unavailable and render the original document before making layout claims.

## Outputs

`prepare` creates a hash-keyed reader directory containing:

- `manifest.json`: compact metadata, warnings, page/chunk map, and cached-source location;
- `document.md`: complete page-aware extraction for local reference only;
- `chunks/*.md`: retrieval units intended for selective reading;
- `index.json`: lightweight search metadata.

See `references/quality-rules.md` only when deciding whether extracted evidence requires visual review or when benchmarking the skill.

# Contributing

Contributions are welcome. Keep the project local-first and preserve the central invariant: full document conversion stays on disk while Codex loads only the minimum evidence needed.

Before submitting a change:

1. Do not add telemetry, uploads, or network calls to the reader script.
2. Preserve source-page anchors and never overwrite source documents.
3. Add or update tests for deterministic behavior.
4. Run `python -m unittest discover -s tests -v`.
5. Test layout-sensitive changes against at least one real PDF or DOCX and visually inspect affected pages.

Please avoid committing source documents, extracted caches, rendered pages, personal paths, credentials, or proprietary test data.

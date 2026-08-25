# Quality and Benchmark Rules

## Visual review triggers

Treat extraction as navigation rather than final evidence for tables, charts, equations, forms, signatures, handwriting, comments, tracked changes, footnotes, headers/footers, or multi-column layouts. Render the relevant source page and compare values, labels, reading order, and units.

`no_text` means no meaningful text was extracted. `low_text` means the page may be scanned, image-heavy, or otherwise poorly extracted. `possible_complex_layout` is a heuristic flag, not proof of a problem.

## Answer checks

Before answering:

1. Confirm every important claim is supported by a retrieved passage.
2. Check adjacent context for qualifications, exceptions, negation, and units.
3. Use original page anchors in citations.
4. Visually verify layout-sensitive evidence.
5. Say what could not be verified.

## Suggested benchmark set

Test at least one of each:

- searchable text PDF;
- scanned Chinese PDF;
- PDF with tables or two-column layout;
- ordinary DOCX;
- DOCX with tables, comments, or tracked changes;
- document longer than 100 pages.

Compare answer correctness, page-citation accuracy, number of chunks opened, pages rendered, preprocessing reuse, and total source characters loaded. Do not promise a fixed token-saving percentage without measurements on the user's own documents.

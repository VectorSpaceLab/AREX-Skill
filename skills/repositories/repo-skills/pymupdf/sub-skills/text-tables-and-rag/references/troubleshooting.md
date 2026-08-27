# Text/Table/RAG Troubleshooting

- Empty text on visible pages: likely scanned/image-only page, simulated vector text, clip/flag issue, or OCR needed.
- Garbled text: font encoding/obfuscation; try dict/rawdict and compare viewer behavior.
- Bad reading order: try `sort=True`, words/blocks, table extraction, or PyMuPDF4LLM if installed.
- Table misses: switch strategies, add explicit lines/boxes, clip to the table area, and verify `use_layout` behavior.
- Pandas error: use `Table.extract()` or `Table.to_markdown()` unless pandas is installed.
- OCR error: verify Tesseract binary, tessdata, and language packs.

# knowledge-rag Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The KB cannot be constructed | The vector DB or embedding provider is missing. | Install the matching extras and verify the backend import first. |
| Document ingestion skips a file type | The right loader extra is not installed or the source is unsupported. | Add the loader extra or convert the source to a format the current loader understands. |
| OCR on PDFs does nothing useful | OCR support is missing or the document is not image-based. | Install the OCR extra and test with a tiny image-only fixture. |
| Search results look empty or irrelevant | The splitter, embedding, or vector DB configuration is mismatched. | Re-check chunking, embedding, and vector settings one layer at a time. |
| Retrieval crosses project boundaries | Search isolation was disabled or the same storage was reused. | Turn on isolation or give each KB its own storage namespace. |

## Smoke check

```bash
python sub-skills/knowledge-rag/scripts/check_rag_optional_imports.py
```

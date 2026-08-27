# Data and CLI Utilities Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Downloader hangs or fails | Network unavailable, cache missing, or remote resource inaccessible. | Use `api.info` first; check cache; set `GENSIM_DATA_DIR`; avoid required downloads unless approved. |
| Unexpected disk usage | Large gensim-data model or full Wikipedia output. | Inspect metadata/size first and choose a cache/output directory with enough space. |
| Cache checksum or load failure | Corrupt partial download or stale cache. | Remove only the affected resource directory and re-download when network is available. |
| GloVe conversion fails | Non-numeric vector value or inconsistent dimensions. | Validate the first lines and ensure every row has token plus equal-length floats. |
| word2vec load/export fails | Wrong text/binary flag, missing header, or encoding mismatch. | Confirm file format; use `binary=True` only for binary files; handle `no_header` deliberately. |
| Tensor TSV files misalign | Metadata/vector rows were edited separately. | Regenerate both files from the same source vector file and keep them together. |
| `segment_wiki` output is empty | Article length/namespace filters removed all pages or fixture is malformed. | Lower `min_article_character`, verify XML namespace/pages, and test on a known tiny fixture. |
| Full Wiki conversion is too slow | Large dump, high worker count, or disk/compression bottleneck. | Run sample first, reduce workers if memory-bound, and schedule full jobs explicitly. |
| Optional lemmatization unavailable | `pattern` or related optional tooling not installed. | Treat lemmatization as optional; use default tokenization unless explicitly needed. |
| Package-info output exposes local paths | Raw diagnostic includes install location. | Use the root privacy-safe environment checker for reports. |

## Safe conversion checklist

1. Work in a scratch output directory.
2. Run `--help` on bundled wrappers.
3. Start with two or three vector rows.
4. Verify output loads with `KeyedVectors.load_word2vec_format`.
5. Scale to full files only after the tiny fixture passes.

# Corpora and Vector Spaces Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError` from `doc2bow` when passing text | A raw string was passed instead of a token list. | Tokenize first: `dictionary.doc2bow(simple_preprocess(doc))`. |
| Query vector is empty | All query tokens are out-of-vocabulary or preprocessing removed them. | Print tokens, check `dictionary.token2id`, and confirm training/query preprocessing match. |
| Model/index results look wrong after dictionary filtering | Feature ids changed or a different dictionary was used. | Save/load the dictionary used for training; re-vectorize corpus and query after filtering. |
| Corpus loader fails with parse errors | Wrong corpus class for the file format or corrupt/truncated file. | Match loader to format; test on first few lines; confirm compression extension. |
| Random access/indexing fails | Missing or stale sidecar index file. | Recreate serialization/index or use sequential iteration. Keep index sidecars with the corpus. |
| Unicode decode errors | Incorrect input encoding. | Open text with the correct encoding or normalize upstream; for `TextDirectoryCorpus`, pass `encoding`. |
| `WikiCorpus` uses too much CPU/time/disk | Full MediaWiki dumps are huge and multiprocessing can be heavy. | Run a tiny sample first; tune filters; route full dump command planning to `data-and-cli-utilities`. |
| Memory exhaustion | Corpus was converted to a list or dense matrix. | Keep data as iterators/sparse vectors; only call `list(corpus)` on tiny fixtures. |

## Diagnostic checklist

1. `print(len(dictionary), dictionary.num_docs)`.
2. Inspect a tokenized document before vectorization.
3. Inspect `dictionary.doc2bow(tokens, return_missing=True)` on a failing query.
4. Confirm the same dictionary object or saved dictionary is used across training
   and querying.
5. Run `scripts/corpus_io_smoke.py` to isolate environment/package problems from
   data-specific issues.

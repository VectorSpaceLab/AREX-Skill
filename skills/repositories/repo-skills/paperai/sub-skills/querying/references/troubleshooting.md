# Querying troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TypeError` from `os.path.join` | No model path was supplied. | Pass the model directory as the third positional argument to `python -m paperai.query`, or configure the shell path. |
| `sqlite3.OperationalError: no such table` | The database is not paperetl-compatible or the wrong directory was selected. | Inspect `articles.sqlite` and required tables before changing query parameters. |
| `embeddings` is `None` or a query returns no results | Saved txtai config/model files are missing, or the index was not built for this database. | Build an index via the indexing route, then ensure `config`/`config.json` is beside the database. |
| Empty result for `*` | Direct `Query.search` intentionally treats `*` as no vector query. | Use a report task's `query: "*"` for all-article reports, or submit a real query for search. |
| Too many/few results | `topn`, `threshold`, duplicate sections, or model score scale. | Change one parameter at a time; inspect raw scores and use a bounded topn. |
| Required/prohibited filter surprises | `+` and `-` tests are literal token-presence checks on section text. | Check spelling/tokenization and inspect matching section text; do not assume Boolean ranking semantics. |
| API returns `None` or 422/500 | API model is unconfigured or `limit`/`threshold` is malformed. | Load a saved model, validate numeric query params, and check the API config/class path. |
| Shell appears hung | It is waiting for interactive input by design. | Send a query or exit; use import/one-shot query checks in automation. |
| Streamlit app import fails | Optional UI dependencies are absent or incompatible. | Keep the core CLI/API path; install UI dependencies only for the UI workflow. |

If a downloaded model needs CUDA or another accelerator, verify that backend and
model separately. paperai's query logic itself has no required accelerator gate.

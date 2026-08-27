# Cross-cutting troubleshooting

Read this before changing a working retrieval pipeline. First identify which
sub-skill owns the failing surface; do not fix an optional failure by silently
switching scoring, vocabulary, corpus, or remote source.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'bm25s'` | The package is not installed in the interpreter running the command | Run `python -m pip install bm25s` in that interpreter, then `python -c "import bm25s"`; avoid relying on a different shell's activation |
| `bm25s.hf` raises an import error for `huggingface_hub` | The Hub extra is absent | Install `bm25s[hf]` only for Hub work; ordinary local indexing does not need it |
| `bm25s.mcp` fails at `mcp.server.fastmcp` | MCP API/version mismatch | Run the bundled import diagnosis under [hub-mcp-and-evaluation](../sub-skills/hub-mcp-and-evaluation/SKILL.md); this revision was verified with a compatible `mcp<2` line, not the latest package by assumption |
| Numba, SciPy, JAX, Rich, or `pytrec_eval` is unavailable | An optional route was selected without its extra | Either install the route-specific extra or use the documented CPU/base fallback; keep the dependency choice in the experiment record |
| A first Numba/JAX call is slow or emits a CPU fallback warning | JIT compilation/cache or CPU JAX selection | Run a tiny local warm-up, record the first-call cost, and do not claim CUDA acceleration from a CPU wheel or warning |

Use [scripts/check_environment.py](../scripts/check_environment.py) to report
base and optional imports without performing network calls or writing indexes.

## Vocabulary and corpus alignment

- Token IDs from separate calls to the module-level `bm25s.tokenize` do not
  share a vocabulary. Tokenize corpus and queries with one `Tokenizer`, or pass
  the corpus `Tokenized` vocabulary through the low-level route.
- A retrieved document ID is a position. Before passing `corpus=` to
  `BM25.retrieve`, assert that its length and order match the indexed corpus;
  the current low-level API does not perform this check.
- If a query produces no known tokens, decide whether zero-score top-k results
  or an empty high-level result is intended. Do not “fix” it by updating a
  production vocabulary during query time.
- A missing `vocab.index.json`, a missing BM25L/BM25+ non-occurrence array, or
  a stale JSONL memory-map companion is an artifact-integrity failure. Stop and
  repair/reload with the exact saved filenames; do not fabricate placeholders.

See [core-indexing-retrieval](../sub-skills/core-indexing-retrieval/SKILL.md),
[tokenization-and-stopwords](../sub-skills/tokenization-and-stopwords/SKILL.md),
and [persistence-and-corpus-io](../sub-skills/persistence-and-corpus-io/SKILL.md)
for the owning contracts.

## CLI and file data

- `bm25 index` accepts `.csv`, `.txt`, `.json`, and `.jsonl` through the
  high-level loader. Use `--column` for the actual text field; missing fields
  should be corrected, not skipped.
- `bm25 search` needs `--index PATH` unless `--user` is selected. A user index
  name resolves below `~/.bm25s/indices`; this is a filesystem side effect for
  indexing, not for ordinary search.
- An oversized positive `k` is clamped by the high-level/CLI path but rejected
  by low-level `BM25.retrieve` when it exceeds the indexed document count.
  Record which route produced the result before comparing behavior.
- Use a temporary local fixture and the bundled high-level helper before
  introducing a network dataset or user-directory write.

## Remote and service boundaries

- Hub upload is a remote mutation. Stage locally, inspect the index, confirm
  the destination/repository/revision/privacy choice, and obtain explicit
  authorization before calling `save_to_hub`.
- Hub reads still require network and may require a token for private models;
  `revision`, `local_dir`, `load_corpus`, and `mmap` are reproducibility choices.
- MCP fixture checks are in-process and bounded. A successful local tool call
  does not verify transport, authentication, port binding, or deployment
  security. Inspect `bm25 mcp launch --help` and the installed MCP API before
  starting a service.
- BEIR acquisition/evaluation can download large data and requires compatible
  qrels/result IDs plus optional `pytrec_eval`. Use local tiny qrels for a
  smoke check and keep full benchmarks outside routine operation.

If the failure crosses routes, hand off the exact symptom, dependency/version,
index directory state, corpus/vocabulary contract, and whether network or
credentials are allowed. Do not reopen excluded benchmark or CI artifacts as a
first response.

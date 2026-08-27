---
name: bm25s
description: "Use bm25s for sparse lexical retrieval: tokenize text, build and
  query BM25 indexes, persist or memory-map them, run the high-level or bm25 CLI
  workflows, and diagnose optional acceleration and integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---
# bm25s

`bm25s` is a NumPy-backed, eager sparse BM25 implementation for lexical search.
Use this root as the routing map; keep detailed signatures, file contracts, CLI
flags, and troubleshooting in the linked sub-skills.

## Install and verify

Start with the smallest dependency set that matches the route:

```bash
pip install bm25s
python -c "import bm25s; print(bm25s.__version__)"
```

Optional extras are independent choices: `bm25s[core]` adds progress/JSON,
PyStemmer, and Numba; `bm25s[indexing]` adds SciPy CSC construction;
`bm25s[selection]` adds CPU JAX top-k; `bm25s[hf]` adds Hugging Face Hub;
`bm25s[mcp]` adds MCP; `bm25s[cli]` adds Rich; and
`bm25s[evaluation]` adds `pytrec_eval`. The `full` extra combines the package
extras but is not required for ordinary CPU retrieval. Check optional imports
with [scripts/check_environment.py](scripts/check_environment.py).

The required operating path is CPU/NumPy. Numba, SciPy, and JAX are optional
CPU choices, not CUDA claims. Hub operations require network/credentials and
MCP is a local or separately deployed service; do not perform remote writes or
start a listener without explicit user intent.

## Choose a route

- **Construct or query a low-level BM25 index, score variants, return IDs or
  metadata, or apply a mask:** read
  [core-indexing-retrieval](sub-skills/core-indexing-retrieval/SKILL.md).
- **Tokenize corpus and queries, configure stopwords/stemming, share a
  vocabulary, stream text, or persist tokenizer state:** read
  [tokenization-and-stopwords](sub-skills/tokenization-and-stopwords/SKILL.md).
- **Save/load an index, restore a JSONL corpus, use `mmap`, inspect files, or
  plan a large-index workflow:** read
  [persistence-and-corpus-io](sub-skills/persistence-and-corpus-io/SKILL.md).
- **Load CSV/TXT/JSON/JSONL, use `BM25Search`, or run `bm25 index/search`:**
  read [high-level-and-cli](sub-skills/high-level-and-cli/SKILL.md).
- **Choose Numba, SciPy, NumPy/JAX top-k, compile JIT code, or diagnose an
  optional backend:** read
  [acceleration-and-selection](sub-skills/acceleration-and-selection/SKILL.md).
- **Exchange indexes with Hugging Face, expose a local index through MCP, or
  compute bounded BEIR-style metrics:** read
  [hub-mcp-and-evaluation](sub-skills/hub-mcp-and-evaluation/SKILL.md).

## Common low-level contract

A normal low-level flow is: produce one corpus vocabulary with
`bm25s.tokenize(...)` or `Tokenizer`, call `BM25.index(...)`, tokenize queries
with the same vocabulary strategy, and call `retrieve(..., k=...)`. The default
result is a `Results` named tuple with two-dimensional `.documents` and
`.scores` arrays. Without a display corpus, document values are positional
indices; a supplied corpus must have exactly the indexed document count and
order.

Use `show_progress=False` for bounded automation. Keep `k` no larger than the
number of documents in low-level retrieval; the high-level wrapper instead
clamps oversized positive `k`. Use `return_as="documents"` only when scores
are not needed. Record the model method, vocabulary strategy, result shape, and
optional backend in experiment metadata.

## Handoff and safety

Route across sub-skills rather than reopening the original package checkout.
For a saved index, record the exact directory, filenames, corpus count,
`mmap`, and vocabulary state. For a CLI or Hub task, record the input format,
column/key, resolved paths, revision, token/authorization boundary, and result
artifact. Keep `allow_pickle=False` for untrusted indexes, validate corpus
alignment before document-returning retrieval, and stop on missing or
incompatible optional dependencies instead of silently changing the experiment.

Read [references/troubleshooting.md](references/troubleshooting.md) for
cross-cutting install/import, data alignment, optional dependency, CLI, and
integration failures. Read [references/repo-provenance.md](references/repo-provenance.md)
before deciding whether this skill matches a changed repository; refresh the
skill when the recorded commit, package entry points, or major evidence paths
no longer match.

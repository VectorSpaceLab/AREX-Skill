---
name: hub-mcp-and-evaluation
description: "Route Hugging Face Hub exchange, local MCP serving, and bounded
  BEIR-style evaluation for bm25s without hiding network, credential, or
  optional-dependency boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hub, MCP, and evaluation

Use this route when a task needs to exchange a bm25s index through the
Hugging Face Hub, expose a **local** saved index through MCP, or turn retrieval
outputs into BEIR/`pytrec_eval` metrics. Keep ordinary local indexing,
retrieval, persistence, and tokenization in their sibling routes.

## Safety boundary

- Do not upload, create, update, or overwrite a Hub repository unless the user
  has explicitly authorized that exact remote mutation and supplied an
  appropriate token or authenticated environment.
- Treat `BM25HF.load_from_hub` and all Hub snapshot operations as network and
  possibly credential dependent. A local fixture check is not evidence of Hub
  access.
- Do not download BEIR data by default. Dataset acquisition can be large and
  network-bound; use an already available local dataset or request explicit
  permission and a bounded destination.
- MCP fixture checks load only a user-selected local index. They do not start a
  daemon, bind a port, or expose documents to a network client.
- The inspected compatible MCP line is `mcp<2` (the verified environment used
  1.29.0). Treat this as version-sensitive, not as a claim that every latest
  release works.

## Choose the workflow

| Need | Route | Required observation |
| --- | --- | --- |
| Share or consume an index remotely | `BM25HF` in [huggingface.md](references/huggingface.md) | Explicit Hub authorization, dependency, network, and access result |
| Share/recover tokenizer vocabulary or stopwords | `TokenizerHF` in [huggingface.md](references/huggingface.md) | Same authorization boundary; preserve tokenizer configuration |
| Check tools without a server | `create_mcp_server` plus the bundled fixtures | Local index has a corpus; `get_info` and bounded `retrieve` calls return |
| Launch the package entry point | `bm25 mcp launch` | Help/parser and dependency checks first; current factory runs MCP's default transport |
| Score a retrieval result set | [evaluation.md](references/evaluation.md) | Query/document IDs, qrels, result order, and non-empty evaluation inputs align |
| Time or inspect memory only | `bm25s.utils.benchmark` | Small, reproducible local run; do not call it a full comparison benchmark |

## Operating procedure

1. **Classify the boundary.** Decide whether the requested operation is local,
   remote-read, or remote-write. Refuse to infer upload authorization from a
   token merely existing in the environment. Keep `private=True` unless the
   user explicitly requests a public repository.
2. **Check optional imports.** `bm25s.hf` imports `huggingface_hub` at module
   import time; MCP imports `mcp` and `mcp.server.fastmcp`; evaluation imports
   `pytrec_eval` only when `evaluate` is called. Use the package extra or the
   individual dependency and record unavailable optional routes.
3. **For Hub writes, stage locally first.** Build and inspect a tiny local
   index, choose an empty `local_dir` or explicitly allow local overwrite, and
   only then call `save_to_hub`. `overwrite_local` controls the staging folder,
   not remote history or permission. `include_readme`, `corpus`, and
   `allow_pickle` are deliberate choices.
4. **For Hub reads, specify reproducibility.** Pass `revision` when a branch,
   tag, or commit is required; use `local_dir` for the download destination;
   choose `load_corpus=True` only when MCP or document-returning retrieval
   needs it; choose `mmap=True` for a memory-constrained local load.
5. **For MCP, prepare a saved local index with corpus data.** Run
   [create_mcp_fixture.py](scripts/create_mcp_fixture.py), then run
   [verify_mcp_fixture.py](scripts/verify_mcp_fixture.py). The verifier uses
   direct in-process tool calls and bounded inputs; it is not a transport or
   security test.
6. **For CLI launch, inspect help before running.** The supported shape is
   `bm25 mcp launch --index-dir DIR [--port PORT]`. In this revision the
   factory accepts `port` but does not pass it to `FastMCP`; `main` calls
   `mcp.run()` with its default transport. Do not promise an HTTP endpoint from
   the `--port` flag without separately verifying the installed MCP API.
7. **For evaluation, normalize once.** Retrieve with document IDs, call
   `postprocess_results_for_eval(results, scores, query_ids)`, load compatible
   qrels, and call `evaluate(qrels, results_dict, [k...])`. Use local tiny
   qrels for a smoke check and report metrics with their exact keys.
8. **Stop on alignment failures.** A missing corpus, mismatched document IDs,
   absent qrels split, incompatible MCP import, or missing `pytrec_eval` is a
   diagnosis—not a reason to silently substitute a remote download or a
   different metric implementation.

## Public API map

- `bm25s.hf.BM25HF.save_to_hub(repo_id, token=None, local_dir=None, corpus=None,
  private=True, overwrite_local=False, include_readme=True, allow_pickle=False,
  ...)`
- `bm25s.hf.BM25HF.load_from_hub(repo_name, revision=None, token=None,
  local_dir=None, load_corpus=False, mmap=False, allow_pickle=False, ...)`
- `bm25s.hf.TokenizerHF.save_vocab_to_hub`, `load_vocab_from_hub`,
  `save_stopwords_to_hub`, and `load_stopwords_from_hub`; these reuse the
  tokenizer's local JSON vocabulary/stopword formats.
- `bm25s.mcp.server.create_mcp_server(index_dir, port=8000)` returns a
  `FastMCP` instance with `retrieve(query, k=10)` and `get_info()` tools.
- `bm25s.utils.beir.clean_results_keys`,
  `postprocess_results_for_eval`, `download_dataset`, `load_corpus`,
  `load_queries`, `load_qrels`, and `evaluate` provide adapters, not a
  guarantee that a BEIR dataset is present.

See [mcp.md](references/mcp.md) for the import detail and version gate,
[huggingface.md](references/huggingface.md) for remote/local semantics, and
[evaluation.md](references/evaluation.md) for data contracts and metrics.
Use [troubleshooting.md](references/troubleshooting.md) when a route fails.

## Bundled checks

```bash
python scripts/create_mcp_fixture.py --output-dir ./bm25s-mcp-fixture
python scripts/verify_mcp_fixture.py --index-dir ./bm25s-mcp-fixture
python scripts/verify_mcp_fixture.py --diagnose-import
```

These commands are intentionally local and bounded. The first command refuses
an existing non-empty destination unless `--overwrite` is explicit. The second
requires a saved corpus and reports tool results without opening a listener.
The diagnostic mode is safe when MCP is unavailable or its API is incompatible.

## Non-goals and handoff

This route does not manage Hub credentials, upload policy, BEIR data licenses,
large benchmark runs, MCP authentication, transport deployment, or a full
comparison against other rankers. Hand those concerns to the operator with the
exact failure, dependency/version, requested permission, and local artifact
state; never hide them behind a fallback that changes the experiment.

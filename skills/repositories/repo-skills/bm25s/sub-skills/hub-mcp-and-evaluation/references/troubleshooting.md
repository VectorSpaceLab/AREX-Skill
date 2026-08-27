# Troubleshooting Hub, MCP, and evaluation routes

Diagnose the smallest boundary first. Do not respond to a local failure by
silently downloading a dataset, retrying an upload, changing repository
visibility, or switching metric implementations.

## Install and import

### `No module named huggingface_hub` or the `bm25s.hf` import error

The Hub adapter imports `huggingface_hub` when `bm25s.hf` is imported. Install
the `hf` extra or the individual package in the active environment, then retry
only the import diagnostic. Base local bm25s indexing does not require this
adapter. Keep the route marked unavailable if optional installation is not
approved.

### `No module named mcp.server.fastmcp`

Install the package's MCP extra or a compatible MCP release. Confirm both
imports, not just `import mcp`:

```bash
python -c "import mcp; print(getattr(mcp, '__version__', 'unknown'))"
python -c "from mcp.server.fastmcp import FastMCP; print(FastMCP)"
```

For this source revision, constrain the dependency to `mcp<2` when needed. An
MCP 2.x import failure is a version-compatibility block, not an index problem.
Do not start a long-running process while this import is unresolved.

### `pytrec_eval` import failure

Install the `evaluation` extra or `pytrec_eval` only when metrics are required.
The adapter and local JSONL parsing can still be inspected without it, but no
metric result may be claimed. Record the exact missing dependency in the
handoff.

### Wrong MCP import path

Use:

```python
from bm25s.mcp.server import create_mcp_server
```

The package initializer exposes the `server` module but not the factory name.
If a third-party example uses `from bm25s.mcp import create_mcp_server`, adapt
that import rather than changing package files.

## Optional dependency and environment failures

- `huggingface_hub` availability does not grant credentials or network access.
- `mcp` availability does not prove that a client, transport, or server
  protocol is compatible.
- `pytrec_eval` availability does not prove qrels/results are semantically
  aligned.
- A working CPU install is sufficient for the local fixture. This route has no
  required CUDA workflow; do not turn an optional failure into a GPU claim.
- Record package versions and the failing import/operation. Avoid broad
  upgrades that change the tested compatibility line without rechecking the
  API.

## Hub data and configuration failures

### Authentication, private repository, or 401/403 errors

Stop and report the repository ID, requested read/write operation, and whether
an explicit token/permission was supplied. Do not print the token or retry
writes automatically. For a public read, still confirm the user authorized
network access. For a private read or any write, request valid user-provided
authorization.

### Repository not found / `Model ... not found`

Confirm the exact `user/name`, repository type, visibility, token scope, and
`revision`. A missing or inaccessible repository is not repaired by setting
`private=False`; that flag affects saves and requires explicit authorization.

### `local_dir` unexpectedly contains no files

For loads, `local_dir` is passed to `snapshot_download`; check the returned
snapshot and the expected BM25 files before loading. For saves, a non-empty
`local_dir` with `overwrite_local=False` causes the implementation to stage in
a temporary directory, which is deleted after upload. `overwrite_local=True`
allows local writes but does not erase unrelated files or grant remote rights.

### `load_corpus=True` fails with a missing corpus

The Hub snapshot or local MCP fixture lacks the corpus JSONL expected by the
normal BM25 loader. Rebuild/re-export the index with `corpus=...`, or use a
score-only local load for retrieval that does not return documents. Do not
claim MCP document retrieval until the corpus is present and position/ID
alignment has been checked.

### Index loads but retrieval is nonsensical

Check that query tokenization matches index tokenization, the saved vocabulary
was not confused with a tokenizer vocabulary, and the corpus order/IDs remain
aligned with the index. Pin the Hub `revision` and compare the local manifest
before investigating ranking parameters.

## MCP API and CLI failures

### Fixture verifier cannot call tools

Run `--diagnose-import`, capture the MCP version, and inspect `FastMCP.call_tool`
and `list_tools` in the active environment. The bundled verifier intentionally
uses only direct in-process calls. If the installed API changed, use its
`--help`/import diagnostics and leave the direct-call check unverified rather
than launching a listener as a fallback.

### `create_mcp_server` raises while loading

Check that `--index-dir` names a directory made by the BM25 save API and that
it contains the score arrays, `vocab.index.json`, `params.index.json`, and a
corpus file. The factory always requests `load_corpus=True`. Missing files,
malformed JSON, incompatible NumPy artifacts, and absent vocabulary are index
repair issues.

### `bm25 mcp launch` exits immediately or `--port` has no effect

Run `bm25 mcp --help` and `bm25 mcp launch --help` first. The current CLI
forwards `--port` to a factory whose implementation accepts but does not use
it, then calls `mcp.run()` with its default transport. Therefore this revision
should not be described as a configured HTTP service. Verify the installed MCP
transport separately before changing launch guidance.

### Server seems to hang

A foreground MCP process may be waiting for stdio protocol input. This is
expected for a stdio transport, not proof that retrieval is broken. Stop it
rather than leaving a background process, and use the bounded in-process
verifier for local behavior.

## Evaluation data and API failures

### `FileNotFoundError` from a loader

The expected local layout is `<save_dir>/<dataset>/corpus.jsonl`,
`queries.jsonl`, and `qrels/<split>.tsv`. Check the dataset name, `save_dir`,
filename, and split (`train`, `dev`, or `test`). Do not invoke a downloader
unless explicit network/data permission exists.

### Empty or zero metrics / division errors

Confirm that at least one query has both qrels and scored results, qrels and
results use the same string IDs, and `k_values` is a non-empty list. Check that
retrieval results were converted with `postprocess_results_for_eval` in the
same query order. A zero-query result is not a meaningful zero score.

### Metrics differ after repeated calls

The default `ignore_identical_ids=True` removes query/document ID collisions by
mutating the nested `results` mappings. Pass a deep copy before evaluation,
or set the flag explicitly and record the policy. Also confirm that the same
cutoffs, qrels split, tokenizer, and Hub revision were used.

### `qrels` or result IDs do not match

Stop before interpreting metrics. Inspect a few query IDs, document IDs, and
relevance values; normalize IDs at the data boundary, not inside a metric
report. `clean_results_keys` is for metric labels containing `@`, not for qrels
or document identifiers.

## Workflow-specific stop conditions

- **Credential-free Hub request:** refuse the upload or private read. Offer a
  local save/load smoke test and a dry, non-network plan; do not mock a remote
  success as if it were verified.
- **Missing MCP corpus:** refuse to claim `retrieve` works, because the
  factory explicitly loads the corpus. Recreate a tiny local index with the
  corpus or route to score-only retrieval.
- **Incompatible MCP dependency:** retain the `mcp<2` compatibility note,
  report the import error, and stop direct tool verification. Do not install a
  major upgrade silently.
- **Missing corpus/qrels or incompatible IDs:** repair the fixture or ask for
  the correct local data. Do not download BEIR data or fabricate relevance.
- **Long server, remote upload/download, or full benchmark:** require explicit
  operator intent, destination, budget, and stop condition before proceeding.

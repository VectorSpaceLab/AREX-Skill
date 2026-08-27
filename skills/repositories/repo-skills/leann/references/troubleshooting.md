# Cross-cutting troubleshooting

Classify the failure before changing an environment or index. Preserve the
first exception, selected backend, package versions, index metadata, and the
smallest reproducer. Never paste secrets or private passage text into a report.

## Fast triage

1. **Import/install**: run `python -m pip check`, then the bundled install probe.
2. **Backend**: require the exact registry name; import that backend module
   separately and use the backend sub-skill.
3. **Index/artifact**: run the read-only index inspector before rebuilding.
4. **Embedding/model**: compare stored model/mode/dimensions with query-time
   settings before restarting a daemon or downloading another model.
5. **CLI/API shape**: compare the command or signature with the owning
   reference; distinguish an index base path from an artifact filename.
6. **Service/provider**: separate local process/port/protocol failures from
   credentials, network, quotas, or model availability.

## Decision table

| Symptom | Likely cause | Safe next step | Owner |
|---|---|---|---|
| `No module named leann` or missing public class | wrong interpreter, core absent, mixed editable/wheel install | run the same Python's `pip check` and install probe; inspect component versions without exposing install paths | root installation; development for a checkout |
| Backend requested but not registered | distribution absent or backend import raised an optional/native error | run `check_leann_install.py --require-backend NAME`; import its module alone; do not silently switch algorithms | backends and storage |
| Native symbol, ZeroMQ, BLAS, FAISS, CUDA, or ABI error | incompatible wheel/runtime/compiler libraries or incomplete source build | preserve loader/CMake error and verify one coherent backend stack | backends and storage; development for source builds |
| Index name/path cannot be found | wrong project, duplicate registry name, or artifact filename passed where a base path is expected | use `leann list`, inspect the project-local index directory, and pass the base path | CLI operations; API and indexing |
| Missing `.meta.json`, passages, offset map, or backend file | partial copy/build/update or mixed artifact families | run the read-only index inspector; restore a complete same-build family or rebuild | backends and storage |
| Dimension/metric mismatch or irrelevant vector results | build/query embedding contract changed, vectors not normalized as expected, or wrong backend metadata | compare model, mode, dimensions, templates, normalization, and metric before any rebuild | embeddings and chat; backends and storage |
| Metadata filter yields no rows | unsupported operator, missing field, type mismatch, or post-retrieval candidate pool too small | validate filter shape and stored metadata; raise retrieval depth before assuming no match | API and indexing |
| BM25/grep fails or returns no text | no passage JSONL/FTS5 support, bad regex, or wrong retrieval mode | validate artifacts and use the API retrieval-mode reference; do not invent CLI flags | API and indexing |
| Incremental update duplicates or loses passages | backend update capability misunderstood or passage/offset/ID maps diverged | stop mutation, inspect IDs/artifacts, then use IVF remove-then-add or a supported full rebuild | API and indexing; backends and storage |
| CLI rejects command/filter | positional query or flag spelling wrong, malformed JSON, unsupported CLI capability | use the non-executing command planner and exact CLI reference | CLI operations |
| Watch/daemon/warmup hangs or wrong process responds | stale process record, model signature mismatch, occupied/incorrect port, or checkpoint scope issue | inspect status/logging, stop only the identified process, and recover without deleting the index | CLI operations; embeddings and chat |
| Model download/cache/device failure | offline cache miss, unsupported device, optional package absent, or model trust requirement | state network/cache/hardware requirements; validate config offline; download only with authorization | embeddings and chat |
| Provider returns auth/network/quota/model error | key/base URL/model/service mismatch or external availability | validate non-secret fields, probe the approved endpoint separately, and preserve provider response without keys | embeddings and chat |
| RAG loader produces zero chunks | unsupported/corrupt/ignored input, permissions, export/platform mismatch, or chunk settings | preflight a bounded sample and inspect count/text/metadata before building | RAG applications |
| MCP emits malformed JSON or client cannot launch | stdout logging, wrong command/module/cwd, invalid config, or schema mismatch | generate parseable config offline; reserve stdout for JSON-RPC and send logs to stderr | MCP and services |
| HTTP bind/search failure | server extra missing, wrong project/index, occupied port, or unsafe host bind | install server extra, use loopback, check health/index list, then one tiny search | MCP and services |
| Tests collect optional apps/backends unexpectedly | broad environment or test selection does not match the change | select the smallest evidence-bearing suite and record optional skips | development and testing |
| Component versions disagree | monorepo package metadata/pins are not release-aligned | run the read-only version checker; do not bump or publish without authorization | development and testing |

## Stop conditions

Stop and ask for explicit authorization before:

- downloading large models or datasets;
- opening private mail/chat/browser/calendar databases or exports;
- contacting credentialed providers or live MCP sources;
- installing host-level drivers/toolchains or replacing an existing CUDA/ROCm
  framework stack;
- exposing the unauthenticated HTTP service beyond loopback;
- deleting/replacing an index, migrating IDs without a backup, or forcing an
  irreplaceable rebuild;
- bumping versions, committing, tagging, pushing, releasing, or uploading.

## Diagnostic record

Record package/component versions, operating system and architecture, selected
backend, registry output, index metadata fields (without private paths), command
shape with secrets removed, first error, safe checks attempted, and optional
backends deliberately not verified. Keep local environment prefixes and user
paths out of public reports and reusable skill content.

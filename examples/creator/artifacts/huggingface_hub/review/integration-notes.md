# Whole-skill integration notes

## Accepted candidate graph

- Root: `huggingface-hub` — package/CLI router, install/version gate, safety contract, and cross-route ownership.
- `hub-operations` — Hub API resources, repository lifecycle, commits/refs, collaboration metadata, and webhook registration.
- `downloads-and-storage` — downloads, snapshots, cache/offline/Xet, HfFileSystem/URI, buckets, and movement planning.
- `inference-and-endpoints` — hosted inference clients/providers/tasks, async/streaming/tools/schema/MCP, and Inference Endpoint lifecycle.
- `cli-and-automation` — `hf` commands, output/stream semantics, shell automation, extensions, and target-side CLI skill generation.
- `hosted-compute-and-integrations` — Jobs/Sandboxes/Spaces, server integrations, model/card integration, serialization, and TensorBoard.

The graph is task-agnostic: it distills public package operation, not one downstream research task. Links are root → focused sub-skill → nearest references/scripts; sibling overlap is resolved by operation owner rather than source-module location.

## Integration decisions

- The root remains router-like and does not duplicate API catalogs from sub-skills.
- Repository mutations belong to `hub-operations`; CLI syntax/output belongs to `cli-and-automation`; downloads/cache/read-only filesystem behavior belongs to `downloads-and-storage`; inference requests and Endpoint lifecycle belong to `inference-and-endpoints`; paid/stateful cloud and local model integrations belong to `hosted-compute-and-integrations`.
- The `hub-operations` route owns Hub-managed webhook resource registration, while `hosted-compute-and-integrations` owns receiving webhook payloads through `WebhooksServer` and OAuth/server integration.
- Buckets and copy/sync are storage-owned for planning/read behavior, with remote mutations classified and routed to the Hub/CLI owners as appropriate.
- Maintainer generation notes are bundled only when they prevent version drift or explain generated surfaces; source generators are not runtime dependencies.
- No original source docs, tests, scripts, checkout paths, temporary environment paths, or review artifact paths are runtime links.

## Grounding and evidence

The accepted content was grounded in the source snapshot at commit `4237d95c603db491cb1070898c74c97e4d7c2582` / tag `v1.29.0`, `setup.py` metadata and entry points, English guides and package references, source modules, and targeted unit/mock/offline tests. Live inspection used an isolated Python 3.11 environment and verified package imports, optional modules, signatures, CLI help, and the selected optional CUDA smoke; private setup evidence is omitted from the public bundle and is not runtime content.

## Repairs before verification

- Recovered all five drafting lanes after the first workflow returned prose rows without success wrappers; no successful files were silently integrated until the recovery workflow completed with stable IDs.
- Reconciled temporary draft licenses to the single resolved GitHub value `Apache-2.0`.
- Added a root safety/troubleshooting reference and provenance baseline.
- Added candidate v2 routing metadata and external classification decision artifacts.
- Removed generated Python cache debris from the runtime tree after script checks.

## Remaining integration limits

No live credentialed mutation, production inference, model download, endpoint/Job/Sandbox/Space launch, webhook registration, card upload, or destructive operation was run. Optional TensorBoard runtime behavior lacks an installed tensorboard dependency and remains explicitly unverified. These are intentional verification limits, not hidden coverage claims.

# Final Skill Report

## Source Snapshot

- Repository: public `huggingface/huggingface_hub`
- Source commit/tag: `4237d95c603db491cb1070898c74c97e4d7c2582` / `v1.29.0`
- Working tree at source snapshot: clean before generated output was written
- Package/import facts: `huggingface_hub==1.29.0`, import name `huggingface_hub`, Python 3.11.14 inspection runtime; `hf`, `huggingface-cli`, and `tiny-agents` entry points
- Evidence categories: README and quick start; English guides and package references; source roots under `src/huggingface_hub`; CLI, inference, serialization, and utility modules; selected unit/mock/offline tests; setup metadata; AGENTS/CONTRIBUTING; installed-package signatures/imports/CLI help; no standalone examples directory was found
- Exclusions: generated/cache/VCS debris, translations, cassettes, release/installer tooling, broad maintainer infrastructure, and live credentialed/paid/destructive/network-heavy operations

## Generated Skill Summary

- Runtime skill: `skills/huggingface-hub/`
- Root purpose: progressive router for the Python client and `hf` CLI, safe setup, operation ownership, and cross-cutting troubleshooting
- Sub-skills:
  - `hub-operations`: Hub repository/API lifecycle, search, refs, commits, files, cards, collections, discussions/PRs, and webhook resources with read-before-mutate and bounded conflict recovery.
  - `downloads-and-storage`: file/snapshot download, dry-run/filtering, cache/offline/Xet, HfFileSystem/HF URIs, buckets, copy/sync plans, and path safety.
  - `inference-and-endpoints`: sync/async hosted inference, provider/task routing, streaming, chat/tools/JSON schema, MCP, and Inference Endpoint lifecycle.
  - `cli-and-automation`: `hf` groups, flags/help, output formats and streams, auth hygiene, shell automation, plan/apply gates, extensions, and generated CLI skills.
  - `hosted-compute-and-integrations`: Jobs/Sandboxes/Spaces, OAuth/WebhooksServer, model/card integration, DDUF, torch/safetensors sharding, and TensorBoard boundaries.
- Bundled scripts: read-only download environment diagnostic; allowlisted bounded CLI help checker; offline mocked inference recovery; local model/card/serialization/config smoke.
- Runtime tree digest: `sha256:df4a87b7472a120689c081f3f17e1f8540bf2c452406fd808b08b64bb01014df`

## Coverage Matrix

| Repo capability | Evidence | Required backend | Skill location | Coverage | Synthetic validation | Native validation | Notes |
|---|---|---|---|---|---|---|---|
| Install, imports, optional extras, auth boundary | README/setup/installation/auth | any | root + root troubleshooting | covered | root routing case | pip check/import/CLI version pass | Optional TensorBoard remains unverified. |
| Hub repository/API resources and commits | HfApi/repository/upload guides/tests | any | `hub-operations` | covered | private PR conflict + ambiguous timeout cases | auth/core unit passes; live writes skipped | Bounded 409/412 recovery documented. |
| Cards/collections/discussions/webhook resources | card/community/collection/webhook docs/tests | any | `hub-operations` | covered | card/discussion triage | local card/webhook tests pass; remote card run excluded | Resource registration separated from server receiving. |
| File/snapshot downloads | download sources/docs/tests | any | `downloads-and-storage` | covered | offline filtered recovery | URI/core tests pass; broad staging selection unsafe | Network/large download not claimed. |
| Cache/offline/symlink/Xet | cache/Xet sources/docs/tests | any; CUDA optional only | storage refs/diagnostic | covered | offline/cache case | diagnostic and core/cache subsets pass | Optional Xet service integration deferred. |
| Filesystem/URI/buckets/copy/sync | filesystem/URI/bucket docs/tests | any | storage refs | covered | prefix/traversal and plan integrity | URI/cache/CLI volume tests pass | Remote bucket mutations skipped. |
| Hosted inference/providers/tasks | client/provider/generated types/docs/tests | any | `inference-and-endpoints` | covered | mocked chat/provider fallback | provider mappings 176 pass; type tests pass | Dynamic service capabilities require fresh help/mapping. |
| Async/stream/tools/schema/MCP | async/client/MCP docs/source/tests | any | inference refs/script | covered | mock tools/schema/cancellation | mock script pass; live calls skipped | MCP is optional and not all behavior has native tests. |
| Inference Endpoint lifecycle | endpoint source/docs/tests | any | inference refs | covered | endpoint state gate | endpoint tests 28 pass | No paid deployment. |
| CLI command/output/automation | CLI source/docs/tests/live help | any | `cli-and-automation` | covered | stdout/stderr/delete and version-skew cases | 67 focused tests + 8/8 helper probes pass | Live help is version authority. |
| CLI extensions and agent skills | extension/skills docs/source/tests | any | CLI refs | covered | trust/version-skew case | skill-generation tests pass | No third-party installation. |
| Jobs/Sandboxes | source/docs/tests | any | hosted compute refs | covered | status/config lifecycle case | 59 unit/mocked tests pass | No cloud launch/billing. |
| Spaces/OAuth/WebhooksServer | source/docs/tests | any; optional extras | hosted refs/script | covered | mocked config/route recovery | local webhook 25 pass | Live callback/deployment skipped. |
| ModelHubMixin/cards/TensorBoard | integration/card/source/docs/tests | cpu; TensorBoard optional | hosted refs | covered with explicit optional limit | local artifact case | DDUF/serialization/local smoke pass | TensorBoard package not installed. |
| DDUF/torch/safetensors/sharding | serialization source/docs/tests | cpu; torch optional | hosted serialization/script | covered | malformed index/path case | DDUF 26 + serialization 51 pass | No untrusted pickle loading. |
| Maintainer generated surfaces | AGENTS/CONTRIBUTING/utils | any | CLI/inference development refs | bounded | version-drift assertions | static/link checks | Release/installer tools excluded. |

## Long-Tail Gaps

See `reports/integration/long-tail-gap-register.md`. Main gaps are dynamic
provider/CLI catalogs, live credentials/services/paid resources, Xet and bucket
service integration, TensorBoard execution, Windows/macOS-specific behavior,
Git LFS, and maintainer release/translation/CI automation. They are explicit
limits rather than hidden failures.

## Usability Validation

- Case count: 15 directories, each with `user_request.txt`, `README.md`, and
  `assertions.json`.
- Distribution: one root novice case; two Hub cases; three storage cases; two
  inference cases; two CLI cases; two hosted-compute cases; two integrated cases.
- Per-sub-skill difficult synthetic coverage: Hub conflict and ambiguous outcome;
  storage offline recovery and bucket/path/plan safety; inference chat/schema
  fallback and Endpoint state gating; CLI stdout/stderr/delete gate and
  version-skew/extension trust; hosted local artifact recovery and cloud
  config/lifecycle safety.
- Integrated cases: `hub-download-inference-cli` and
  `model-card-upload-serialization`, both synthetic compositions because native
  tests cover components separately and not these hermetic cross-route plans.
- Assertion coverage: 15/15 cases have machine-readable assertions; all major
  selected routes have source docs and native-test evidence anchors. Synthetic
  only: exact cross-route composition and no-network multi-stage orchestration.
- Self-refine: iteration 1 passed route, breadth, depth, privacy, link, script,
  and frontmatter review. It repaired source-path leakage in maintainer refs,
  reconciled licenses, added root integration artifacts, and corrected the
  case index. No unresolved actionable assertion failure remains.

## Native Ground-Truth Verification

- Environment: isolated venv, Python 3.11.14, package 1.29.0; no required
  accelerator backends. Optional torch CUDA smoke passed on eight A100 devices,
  but no local GPU capability is claimed.
- Safe native passes: 720 focused unit/mocked tests across URI/parsing/CLI,
  auth/offline/runtime, DDUF, filtered serialization, inference types/endpoints,
  provider mappings, and Jobs/Sandboxes. An additional 25 local card/webhook
  tests passed but their setup emits telemetry warnings, so they are reported
  separately rather than included in the conservative 720 total.
- Additional selected results: CLI 67 focused tests, provider 176, DDUF 26,
  serialization 51, inference 28, hosted models 59, auth/runtime 45, core 268,
  local cards/webhooks 25, and bundled scripts all pass; the verification logs
  preserve each command and its scope.
- Non-pass statuses: two `NATIVE_FAIL` environment/external-service outcomes
  (root privilege-specific cache deletion expectation; remote card validation
  SSL failure), and three `SKIP_UNSAFE` broad staging/network selections. No
  `SKILL_GAP` and no `BLOCKED_REQUIRED_BACKEND`.
- The broad download/card selections showed that unmarked repository fixtures
  can still contact staging/remote services; they were aborted or excluded from
  acceptance and documented in native reports. This did not contradict the
  generated skill, which explicitly requires mocks/local fixtures first.

## Import Readiness

- Status: ready with warnings; not imported by user request.
- Environment handoff: `ok`; the private environment report is omitted from
  the public example bundle.
- Backend gate eligible for auto-import: technically yes (no required backend
  block), but no auto-import was authorized because the user explicitly said
  “not import”.
- Blocking issues: none for the selected graph. Remaining warnings are live
  service/credential/paid/platform limits and TensorBoard optional coverage.
- Final informed acceptance of required-backend limitations: none required.
- Recommended follow-up: after a future package upgrade, re-run live signatures,
  `hf --help`, provider mapping checks, and a focused refresh; if import is
  later desired, use the dedicated locked repo-skill importer with the external
  routing handoff at `skills/disco/routing_decision/classification.json`.

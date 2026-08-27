# Repo Development Troubleshooting

Use symptom -> cause -> check -> recovery. Do not convert a prerequisite-bound lane into a false pass; explicitly skip lanes that need Go, Node, Docker, Kind, kubectl, Ginkgo, a KFP endpoint, credentials, or GPU hardware when those prerequisites are absent.

## Generated-File Staleness or Drift

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| CI says generated files are out of date. | Source proto/swagger/CRD/template changed without committing regenerated outputs. | `git status --porcelain`, `git diff`, and the regeneration map in `generated-code.md`. | Run the narrow generator, then `make check-diff`; commit expected generated outputs. |
| `make check-diff` fails after running generators. | Generation produced expected files, used stale tools, or left unrelated build artifacts. | Inspect `git status` and generated directories; check prebuilt vs source generator mode. | Keep intentional generated diffs; remove temp artifacts; rerun with `USE_PREBUILT_IMAGE=false` when generator images may be stale. |
| Frontend clients changed in CI but not locally. | Docker/OpenAPI generator version, Node/npm pin, or lockfile drift differs. | `cd frontend && npm --version`, `node --version`, `npm ci`, Docker availability, `git diff -- src/apis src/apisv2beta1 server/src/generated/apis server/src/generated/apisv2beta1`. | Install pinned npm, run `npm ci`, ensure Docker is running, run `npm run apis:all`, commit generated clients if source API changed. |
| Backend Python client or Swagger missing updates. | Only `make generate` or only `generate-kfp-server-api-package` was run. | Check `backend/api/<version>/swagger/` and `backend/api/<version>/python_http_client/`. | Run both commands for each changed `API_VERSION`; repeat for `v1beta1` and `v2beta1` when both schemas are affected. |

Never hand-edit generated output to satisfy a diff. If source ownership is unclear, stop and identify the generator first.

## Missing Tooling

| Symptom | Likely missing prerequisite | Check | Recovery |
| --- | --- | --- | --- |
| `go: command not found`, backend tests cannot list packages. | Go toolchain missing. | `go version`. | Install Go or skip Go/backend lane with an explicit prerequisite gap. |
| `ginkgo: command not found`. | Ginkgo runner absent from PATH. | `ginkgo version` and `echo "$PATH"`. | `make ginkgo && export PATH="$PWD/bin:$PATH"`. |
| `golangci-lint: command not found`. | Go linter missing. | `golangci-lint version`. | Install the project-compatible version or run only tests; do not claim lint passed. |
| `node: command not found`, `npm ci` fails immediately. | Node/npm missing or wrong version. | `node --version`, `cat frontend/.nvmrc`, `npm --version`. | Install/switch to `frontend/.nvmrc`, then install pinned npm from `frontend/package.json`. |
| `npm ci` refuses because lockfile/package metadata mismatch. | `package-lock.json` not updated or package manager version drift. | `git diff -- frontend/package.json frontend/package-lock.json`; frontend lockfile-drift script if available. | Use pinned npm and run intentional `npm install --save`/`--save-dev` for dependency changes; otherwise revert unintended package metadata. |
| `docker`/`podman` unavailable or daemon not running. | Container engine missing/stopped. | `docker info` or `podman info`. | Start/install the engine before Kind, images, frontend OpenAPI generation, or UI smoke `--compare`; otherwise skip those lanes. |
| `kind: command not found` or cluster creation fails. | Kind missing or container engine/resources unavailable. | `kind version`, `docker info`, available ports. | Install Kind/start Docker; verify ports; do not run cluster tests without a safe kube context. |
| `kubectl` points at the wrong cluster/namespace. | Current context not a local KFP test cluster. | `kubectl config current-context`, `kubectl config view --minify --output 'jsonpath={..namespace}'`. | Ask before switching context or mutating resources. Use local Kind names when reproducing CI. |
| `pip-compile: command not found`. | pip-tools missing. | `pip-compile --version`. | Install `pip-tools` in the active venv, then rerun the package-specific lock regeneration. |
| `protoc` or `protoc-gen-grpc-web` missing for frontend protos. | Protobuf compiler/plugin absent. | `protoc --version`, `which protoc-gen-grpc-web`. | Install pinned/compatible protoc tooling before `npm run build:protos`; skip if frontend proto generation is not in scope. |

## Backend, API, and E2E Cluster Failures

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| API or E2E Ginkgo tests fail before test logic starts. | No running KFP cluster, wrong namespace, port-forward failure, or deployment not ready. | `kubectl -n kubeflow get pods`, `kubectl -n kubeflow get deploy`, port-forward logs, namespace argument. | Use `make -C backend kind-cluster-agnostic` or CI deploy action equivalent; wait for `mysql`, `metadata-grpc-deployment`, and `ml-pipeline` availability. |
| `LOCAL_API_SERVER=true` tests cannot connect. | Local API-server dev mode expected but server/ports/env not configured. | Environment vars for MySQL, MinIO/object store, MLMD, visualization server, `POD_NAMESPACE`, `V2_DRIVER_IMAGE`, `V2_LAUNCHER_IMAGE`. | Start the local API server with the dev Kind cluster settings; verify ports 3000, 3306, 8080, 9000, and 8889 or configured alternatives. |
| E2E pipeline checks are flaky around artifact storage. | MinIO/SeaweedFS/object-store transient instability. | Pod logs, events, artifact-store service endpoints; failed step timing. | Retry transient `PutObject` timeouts before weakening assertions or increasing pipeline timeouts. |
| CI Kind job reports checksum mismatch after cache restore. | Kind cache restored corrupt or incompatible artifact. | CI logs before cluster creation/deploy. | Retry the job; no test/deployment signal was produced. |
| Registry or base image pulls fail in Kind/BuildKit/Python/Alpine setup. | External registry/network transient. | Pull error messages and retry history. | Retry before changing code. Only update image references when failure is reproducible and source-owned. |
| Proxy/cache lane fails. | Tinyproxy/proxy namespace or cache deployment problem. | Inspect `tinyproxy` namespace pods, events, services, endpoints, and endpoint slices. | Fix proxy/cache config if source change caused it; otherwise retry transient infra failure. |
| Multi-user namespace behavior differs locally. | Missing namespace/header setup. | `VITE_NAMESPACE`, frontend server namespace, profile/namespace resources, auth headers. | For frontend multi-user local work, build with `VITE_NAMESPACE` and use the expected `kubeflow-userid` header; unset and rebuild for single-user. |

## Frontend Lockfile, API Client, and UI Smoke Failures

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| `frontend.yml` fails lockfile drift check. | `package-lock.json` changed independently from base or npm pin mismatch. | Run current `frontend/scripts/check-lockfile-drift.mjs --base-ref origin/<base>` when available; check Node/npm versions. | Re-run dependency update with pinned npm and commit lockfile, or rebase/refresh lockfile against base. |
| `npm run apis:all` fails with Docker/OpenAPI errors. | Docker daemon unavailable, OpenAPI Generator image pull failure, or invalid Swagger. | `docker info`, generator logs, changed backend Swagger. | Start Docker/retry image pull; if Swagger invalid, fix backend API generation source first. |
| Vitest failures after React effect changes. | Derived state moved into `useEffect`, Strict Mode duplicate callbacks, missing dependency invariant. | Focused UI tests for duplicate mutation success, refresh-preserved selections, retry recovery, or mount-time callbacks. | Move derived state to render, event outcomes to handlers/mutation callbacks, document any exhaustive-deps suppression, and add regression coverage. |
| UI smoke screenshots capture loading/error pages. | Existing dev server lacks backend/proxy/data, wait selector sees skeleton rows, seed data missing. | Smoke runner logs, route URL, data seeding step, API requests. | Use `--current-only --use-existing` only for pages the server can render; use `--compare` with live backend for data pages; seed data when needed. |
| UI smoke leaves ports/worktrees after interruption. | Cleanup interrupted. | `lsof -i :3001`, `.ui-smoke-test/` worktrees, `git worktree list`. | Remove stale worktrees and prune; restore `ml-pipeline-ui` replicas only after confirming this is the intended local Kind cluster. |

## GPU Scheduling and Runtime Resource Mismatches

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| E2E label `gpu-scheduling-check` fails on a CPU-only cluster. | Test requires GPU scheduling support or CI fake GPU operator lane. | Ginkgo label, node allocatable resources, `kubectl describe nodes | grep nvidia.com/gpu`. | Skip or deselect GPU label on CPU-only local clusters; use the CI fake GPU operator lane or a real GPU node pool for runtime proof. |
| Pipeline compiles with GPU resources but runtime pod stays pending. | Cluster lacks GPU nodes, NVIDIA device plugin, node labels, or tolerations/selectors match. | Pod events, node labels, device plugin pods, requested resource keys (`nvidia.com/gpu`). | Fix cluster/GPU scheduling config; compilation only proves IR/platform spec, not runtime availability. |
| User confuses `set_gpu_limit`/resource modifiers with `kfp-kubernetes` node selectors. | Public DSL and Kubernetes platform config are separate layers. | Compiled YAML/resource requests and platform config. | Route public authoring to `pipeline-authoring` and node/toleration config to `kubernetes-platform`; repo-development only owns source tests/generation. |

## `_KFP_RUNTIME=true` Import Behavior

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| SDK imports fail unexpectedly in a development shell. | `_KFP_RUNTIME=true` is set, disabling most SDK imports. | `echo "${_KFP_RUNTIME-}"`; import traceback. | `unset _KFP_RUNTIME` before SDK authoring/testing. |
| Component code works locally but fails inside runtime image importing SDK modules. | Runtime containers install `kfp --no-deps`; `_KFP_RUNTIME=true` intentionally avoids heavy SDK imports. | Inspect component base image deps and the import path used inside task code. | Add needed runtime dependencies to the component image or move compile-only SDK imports out of task code. Do not treat local SDK env as runtime proof. |
| Executor changes break compilation tests. | Confused runtime executor path with compiler path. | Changed files under `sdk/python/kfp/dsl/executor_main.py` versus compiler code. | Test executor/runtime behavior separately from `Compiler().compile`; route public authoring fixes to `pipeline-authoring` if examples need updating. |

## Dependency and Formatting Failures

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| `go mod tidy` changes `go.mod`/`go.sum` in backend presubmit. | Module graph not tidy after Go dependency edits. | `git diff -- go.mod go.sum`. | Commit intentional tidy changes or revert unintended dependency edits. |
| Python requirement pin diff appears without `requirements.in` change. | Regeneration used different pip-tools/Python index or transitive version drift. | Compare `requirements.in`, pip-tools version, generated header. | Re-run with project-pinned tools and intended indexes; include source change or explain forced repin. |
| YAPF/isort/docformatter/pycln fail in SDK. | Formatting/import/docstring style drift. | Run the exact check command from development-testing. | Run mutating formatter only if edits are allowed, then rerun check-only command. |
| Frontend Prettier/ESLint/typecheck fails. | Style, lint, type, generated client, or React peer mismatch. | `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm run check:react-peers`. | Use `npm run format` for style; fix types/lint rules in source; do not update snapshots or suppress lint without a focused justification. |
| Backend `golangci-lint run --new-from-rev HEAD --fix` changes files unexpectedly. | Lint target mutates with `--fix`. | `git diff` after target. | Prefer check-only `golangci-lint run` for diagnosis; commit intentional fixes if user asked to format/lint. |

## Excluded or Approval-Bound Actions

Do not run or recommend as routine repo-development helpers:

- release publishing scripts, package upload scripts, or commands requiring cloud/package-registry credentials;
- project or cloud resource cleaners such as test resource cleanup tools;
- destructive cluster deletion or namespace cleanup unless the user explicitly asks and the target context is confirmed;
- broad dependency installation (`kfp[all]`, all dev extras, frontend install, Go tool downloads) when a narrower lane suffices.

If the only way to verify a task requires one of these actions, state the prerequisite and ask for authorization instead of silently running it.

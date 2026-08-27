# Development and Testing Reference

Use the narrowest command family that matches the user's checkout-maintenance change. Commands here are relative to a Kubeflow Pipelines checkout unless a `cd` is shown. Verify prerequisites before running dependency-heavy, cluster, Docker, or browser workflows.

## Tooling Prerequisites by Lane

| Tool | Required for | Quick check | Notes |
| --- | --- | --- | --- |
| Python 3 and `pip` | SDK, compiler, `kfp-kubernetes`, many scripts | `python3 --version && python3 -m pip --version` | Use a venv for repo development. |
| `pytest`, `pytest-xdist`, SDK dev requirements | SDK and platform tests | `python -m pytest --version` | Install from `sdk/python/requirements-dev.txt` or `kubernetes_platform/python/requirements-dev.txt`. |
| `pip-tools` / `pip-compile` | Regenerating Python lock requirements | `pip-compile --version` | Requirement source files usually document their exact `pip-compile --no-emit-index-url` command. |
| Go | backend, generated Go, controller-gen, Ginkgo | `go version` | Backend presubmits also run `go mod tidy` checks. |
| `ginkgo` | backend compiler/API/E2E suites | `ginkgo version` | Install into `./bin` with `make ginkgo`; then `export PATH="$PWD/bin:$PATH"`. |
| `golangci-lint` | Go lint/format | `golangci-lint version` | Backend `make -C backend lint` may run with `--new-from-rev HEAD --fix`. |
| Node.js and npm | frontend build/test/generation | `node --version && npm --version` | Use `frontend/.nvmrc`; install pinned npm with `npm install --global "$(node -p 'require("./package.json").packageManager')"` from `frontend/`. |
| Docker or Podman | backend images, Kind, frontend OpenAPI generation | `docker info` or `podman info` | Frontend `npm run apis:all` uses OpenAPI Generator via Docker. |
| Kind | local KFP clusters and cluster CI reproduction | `kind version` | Requires container engine. |
| kubectl | cluster deploy/test/debug | `kubectl version --client` | Confirm current context/namespace before running mutating commands. |
| kustomize | manifest generation/tests | `kustomize version` | Some Makefiles install a local version under `bin/`. |
| Java | backend OpenAPI/Python client generation without container image | `java -version` | Docker-based generator normally carries Java. |
| `protoc` and plugins | frontend MLMD/PipelineSpec TypeScript protos | `protoc --version` | MLMD frontend generation also needs `protoc-gen-grpc-web`. |
| GitHub CLI `gh` | issue/PR triage and UI smoke PR mode | `gh --version` | Avoid credential-bound operations unless requested. |

## Python Package Development Setup

For SDK/API/platform source work, use a virtual environment and install the local packages in editable mode. The documented checkout setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
make -C api python-dev
make -C kubernetes_platform python-dev
pip install -e api/v2alpha1/python --config-settings editable_mode=strict
pip install -e sdk/python --config-settings editable_mode=strict
pip install -e kubernetes_platform/python --config-settings editable_mode=strict
```

Notes:

- Keep `kfp`, `kfp-pipeline-spec`, and `kfp-kubernetes` versions aligned when editing package metadata or generated protobufs.
- Do not install broad extras such as `kfp[all]` unless the task explicitly needs those optional dependencies.
- If `_KFP_RUNTIME=true` is set in the shell, unset it before SDK development checks unless you are intentionally testing runtime-import behavior.

## Targeted Test Commands

### SDK and Compiler Python

```bash
pip install -r sdk/python/requirements-dev.txt
pytest -v sdk/python/kfp
```

More CI-like SDK commands:

```bash
./test/presubmit-tests-sdk-unit.sh        # unit tests under sdk/python/kfp; may create venv when SETUP_ENV=true
./test/presubmit-tests-sdk.sh             # regression tests under sdk/python/test; installs broader deps if SETUP_ENV=true
pytest -q sdk/python/kfp/compiler/compiler_test.py
pytest -q sdk/python/kfp/cli/compile_test.py
```

CI sets `SETUP_ENV=false` after actions install dependencies, and sets `PYTEST_PARALLEL_WORKERS` for xdist. For local debugging, set `PYTEST_PARALLEL_WORKERS=0` or run a direct `pytest -q path::test_name` target.

### `kfp-kubernetes`

```bash
pytest -v kubernetes_platform/python/test
pytest -q kubernetes_platform/python/test/unit/test_secret.py
pytest -q kubernetes_platform/python/test/unit/test_config_map.py
pytest -q kubernetes_platform/python/test/unit/test_volume.py
```

Snapshot tests validate generated platform YAML. They are CPU-safe but can be broad; prefer focused unit tests first unless the change touches serialization, generated executor config, or platform spec output.

### Backend Go Unit Tests

The project guide's targeted backend command excludes cluster-bound and slow/e2e packages:

```bash
go test -v $(go list ./backend/... | \
  grep -v backend/test/v2/api | \
  grep -v backend/test/integration | \
  grep -v backend/test/v2/integration | \
  grep -v backend/test/initialization | \
  grep -v backend/test/v2/initialization | \
  grep -v backend/test/compiler | \
  grep -v backend/test/end2end)
```

The backend presubmit script also checks cache-deployer shell helpers, downloads modules, runs `go mod tidy`, and fails on `go.mod`/`go.sum` drift:

```bash
./test/presubmit-backend-test.sh
```

For backend v2 engine work, the optional `just` wrapper is:

```bash
just backend-test      # wraps make -C backend/src/v2 test
```

That target may require MLMD server setup, so inspect the current Makefile before using it as a broad smoke.

### Ginkgo Compiler, API, and E2E Suites

Install Ginkgo once per checkout:

```bash
make ginkgo
export PATH="$PWD/bin:$PATH"
```

Representative commands:

```bash
ginkgo -v ./backend/test/compiler
ginkgo -v --label-filter="Smoke" ./backend/test/v2/api
ginkgo -v --label-filter="Smoke" ./backend/test/end2end -- -namespace=kubeflow
```

Compiler Ginkgo tests are source-only. API and E2E suites require a KFP deployment and Kubernetes namespace. Use label filters on CPU-only clusters because `gpu-scheduling-check` expects `nvidia.com/gpu` scheduling support or the CI fake GPU operator lane.

### Frontend Build, Tests, and Formatting

```bash
cd frontend
npm install --global "$(node -p 'require("./package.json").packageManager')"
npm ci
npm run build
npm run test:ui
npm run lint
npm run typecheck
npm run format:check
```

`npm run test:ci` is the bundled CI gate and runs format, lint, typecheck, mock-backend typecheck, React peer checks, and coverage tests. Use narrower commands for small changes.

Development servers:

```bash
npm run mock:api                    # fixture-backed backend on localhost; no cluster
npm start                           # Vite client dev server
npm run start:proxy-and-server      # local frontend server proxying to a KFP cluster
npm run start:proxy-and-server-inspect
npm run storybook
```

Use `VITE_NAMESPACE` when targeting a multi-user cluster from a local frontend build, and unset/rebuild when returning to single-user mode.

### UI Smoke Tests

The UI smoke-test tool lives under `frontend/scripts/ui-smoke-test/` and is reference-only for this sub-skill because it creates worktrees, may create or reuse Kind clusters, starts servers, captures screenshots, and may post PR summaries.

Fast current-server screenshots:

```bash
cd frontend
node scripts/ui-smoke-test/smoke-test-runner.js --current-only --use-existing --url http://localhost:3000
```

Full branch comparison against a live Kind backend:

```bash
cd frontend
node scripts/ui-smoke-test/smoke-test-runner.js --compare master
node scripts/ui-smoke-test/smoke-test-runner.js --compare master --skip-backend  # frontend-only override
```

Prerequisites include Node, git, Docker, Kind, kubectl, and for `--pr`, `gh`. Output is saved under `.ui-smoke-test/` in the checkout and is gitignored.

### Manifests and Deployment

```bash
./manifests/kustomize/hack/presubmit.sh
make -C backend kind-cluster-agnostic      # standalone local KFP deployment
make -C backend dev-kind-cluster           # API-server development cluster
```

Cluster commands mutate local Kubernetes state. Confirm the user wants deployment/test work, the current kube context is safe, and the required ports are available before running them.

### Build Commands

Backend image family:

```bash
make -C backend image_apiserver
make -C backend image_driver
make -C backend all            # all backend images; heavy
```

API server binary:

```bash
go build -o /tmp/apiserver backend/src/apiserver/*.go
```

Frontend production bundle/image:

```bash
cd frontend
npm run build
npm run docker                 # requires Docker and passes Node version build args
```

## Formatting and Linting

Go/backend:

```bash
golangci-lint run
make -C backend lint
make -C backend format
make -C backend lint-and-format
```

SDK Python:

```bash
pycln --check sdk/python
isort --check --profile google sdk/python
yapf --recursive --diff sdk/python/
docformatter --check --recursive sdk/python/ --exclude "compiler_test.py"
python3 -m pre_commit_hooks.string_fixer $(find sdk/python/kfp -name '*.py' -type f)
```

Presubmit wrapper scripts install exact tool pins from `sdk/python/requirements-dev.txt`:

```bash
./test/presubmit-isort-sdk.sh
./test/presubmit-yapf-sdk.sh
./test/presubmit-docformatter-sdk.sh
```

Frontend:

```bash
cd frontend
npm run format
npm run format:check
npm run lint
npm run typecheck
```

Formatting commands may mutate the checkout. Run check-only variants first when the user asked only for diagnosis.

## Dependency Files

- Python requirement source files usually use `pip-compile --no-emit-index-url requirements.in` to regenerate `requirements.txt`.
- Backend Python dependencies are managed with pip-tools; edit `backend/requirements.in` and run `backend/update_requirements.sh` when that area changes.
- SDK and platform requirement files have their own `requirements.in`/`requirements-dev.txt`; keep pins scoped to the package that needs them.
- Frontend dependencies should be changed through npm so `package.json` and `package-lock.json` stay synchronized. Use `npm ci` for reproducible installs and `npm install --save` or `npm install --save-dev` for intentional dependency changes.

## CI Lanes to Mention in Handoffs

| Change area | Likely CI coverage |
| --- | --- |
| Generated backend/API/CRD outputs | `validate-generated-files.yml` and `make check-diff` |
| Frontend APIs/UI | `frontend.yml`, `e2e-test-frontend.yml`, optional UI smoke tool |
| SDK unit/regression | `kfp-sdk-unit-tests.yml`, `kfp-sdk-tests.yml`, SDK format workflows |
| Client against live KFP | `kfp-sdk-client-tests.yml` |
| Backend Go unit | `presubmit-backend.yml`, `pre-commit.yml` |
| Compiler Ginkgo | `compiler-tests.yml` |
| API server matrix | `api-server-tests.yml` |
| E2E runtime, cache, proxy, GPU, MLflow, multi-user | `e2e-test.yml` |
| Manifests | `kubeflow-pipelines-manifests.yml` |

CI matrices cover multiple Kubernetes/Argo versions, database and Kubernetes pipeline stores, proxy/cache variants, pod-to-pod TLS, multi-user lanes, artifact stores, and GPU scheduling. Do not weaken local guidance merely because one lane is hard to run locally.

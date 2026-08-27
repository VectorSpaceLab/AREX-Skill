# Generated Code Reference

Rule: never hand-edit generated outputs. Change the source schema/template/input, run the correct generator in a prepared checkout, then validate that only expected generated files changed.

## Regeneration Map

| Generated output | Source of truth | Command family | Tooling/prereqs | Validation notes |
| --- | --- | --- | --- | --- |
| PipelineSpec Python package (`kfp-pipeline-spec`) | `api/v2alpha1/pipeline_spec.proto` plus fetched Google protos | `make -C api python` or `make -C api all` | Python, Go/Docker generator path depending Make target | `api/v2alpha1/python/kfp/pipeline_spec/pipeline_spec_pb2.py` is generated but not committed in the inspected snapshot; install local package after generation for SDK tests. |
| PipelineSpec Go bindings | `api/` protos | `make -C api golang` or `make -C api all` | Go, generator image/toolchain | Schema changes usually require both Python and Go generation. |
| Kubernetes executor config Python package | `kubernetes_platform/proto/kubernetes_executor_config.proto` | `make -C kubernetes_platform python` or `make -C kubernetes_platform all` | Python, Go/Docker generator path depending Make target | `kfp-kubernetes` rewrites generated pipeline-spec imports through `kubernetes_platform/python/generate_proto.py`; version skew can break `from kfp import kubernetes`. |
| Kubernetes executor config Go bindings | `kubernetes_platform/proto/kubernetes_executor_config.proto` | `make -C kubernetes_platform golang` or `make -C kubernetes_platform all` | Go/generator | Run when Go consumers or protobuf schema changed. |
| Backend API Go clients, HTTP clients, and Swagger | `backend/api/{v1beta1,v2beta1}/*.proto` | `make -C backend/api API_VERSION=v2beta1 generate`; repeat for `v1beta1` as needed | Docker by default; Make; prebuilt or source generator image | `pipeline.upload.swagger.json` is manually maintained; do not overwrite it blindly. |
| Backend Python `kfp-server-api` client | `backend/api/{v1beta1,v2beta1}/swagger/kfp_api_single_file.swagger.json` and templates | `make -C backend/api API_VERSION=v2beta1 generate-kfp-server-api-package`; repeat for `v1beta1` if needed | Docker by default; Java/Python if running script directly | Generated package lands under `backend/api/<version>/python_http_client`. |
| Frontend OpenAPI clients | Backend API swagger JSON under `backend/api/**/swagger/*.json` | `cd frontend && npm run apis:all` | Node/npm, Docker running for OpenAPI Generator | CI diffs `src/apis`, `src/apisv2beta1`, `server/src/generated/apis`, and `server/src/generated/apisv2beta1`. |
| Frontend MLMD protobuf JS/TS | `third_party/ml-metadata/ml_metadata/proto/*.proto` | `cd frontend && npm run build:protos` | Node/npm, `protoc`, `protoc-gen-grpc-web` | The current generated frontend MLMD code is committed so the build does not require `protoc` during normal installs. |
| Frontend PipelineSpec TypeScript | `api/v2alpha1/pipeline_spec.proto` | `cd frontend && npm run build:pipeline-spec` | Node/npm, `protoc`, ts-proto tooling | Needed when frontend code reads or displays PipelineSpec payloads. |
| Frontend Kubernetes platform spec TypeScript | `kubernetes_platform/proto/kubernetes_executor_config.proto` | `cd frontend && npm run build:platform-spec:kubernetes-platform` | Node/npm, `protoc` | Pair with platform proto changes if frontend consumes the platform spec. |
| K8s native API DeepCopy/CRDs/manifests | Go types under `backend/src/crd/kubernetes/` | `cd backend/src/crd/kubernetes && make generate manifests` | Go; local `controller-gen`; kustomize for install/uninstall | `validate-generated-files.yml` runs both `make generate` and `make manifests` from this directory. |
| Python requirement pins | Package-specific `requirements.in` files | usually `pip-compile --no-emit-index-url requirements.in`; backend: `backend/update_requirements.sh` | pip-tools | Regenerated `requirements.txt` must be committed with source `requirements.in` changes. |

## Source-Build Mode for Generators

Many API-generation Make targets use prebuilt generator images for speed. Use source-build mode when generator code, Dockerfiles, dependencies, or tool versions changed, or when prebuilt images may be stale:

```bash
USE_PREBUILT_IMAGE=false make -C backend/api API_VERSION=v2beta1 generate
USE_PREBUILT_IMAGE=false make -C backend/api API_VERSION=v2beta1 generate-kfp-server-api-package
```

The backend API README also exposes legacy `generate-from-scratch` and source-specific targets. Prefer the documented Make targets unless the current checkout changed target names.

## Validation Commands

Run the narrow generator first, then a drift check:

```bash
make check-diff
```

`make check-diff` fails if `git status --porcelain` is non-empty and prints `git status` plus `git diff`. It is used as a generated-file drift gate; it is not a substitute for semantic tests.

CI drift gates:

- `validate-generated-files.yml` sets `USE_PREBUILT_IMAGE=false`, installs Go/Python/protobuf dependencies, generates K8s native API CRDs, backend proto code for `v2beta1` and `v1beta1`, backend Python clients for both versions, then runs `make check-diff`.
- `frontend.yml` installs the pinned npm version, checks frontend lockfile drift against the PR base, runs `npm ci`, runs `npm run apis:all`, and fails if frontend/server generated API clients differ from git.

## Common Regeneration Workflows

### PipelineSpec schema change

1. Edit `api/v2alpha1/pipeline_spec.proto`.
2. Regenerate Python and Go outputs:

   ```bash
   make -C api python
   make -C api golang
   ```

3. If frontend reads the changed schema, regenerate frontend PipelineSpec TS:

   ```bash
   cd frontend && npm run build:pipeline-spec
   ```

4. Reinstall local editable packages if tests import generated package changes.
5. Run targeted compiler/API tests, then `make check-diff`.

### Kubernetes platform spec change

1. Edit `kubernetes_platform/proto/kubernetes_executor_config.proto` or helper serialization code.
2. Regenerate platform outputs:

   ```bash
   make -C kubernetes_platform python
   make -C kubernetes_platform golang
   ```

3. If frontend consumes the platform spec:

   ```bash
   cd frontend && npm run build:platform-spec:kubernetes-platform
   ```

4. Run `kubernetes_platform/python/test/unit/` and representative snapshot tests.

### Backend API proto change

1. Edit the relevant `backend/api/<version>/*.proto` source.
2. Generate clients and Swagger for the changed API version:

   ```bash
   make -C backend/api API_VERSION=v2beta1 generate
   make -C backend/api API_VERSION=v2beta1 generate-kfp-server-api-package
   ```

3. If frontend clients depend on the changed Swagger:

   ```bash
   cd frontend && npm run apis:all
   ```

4. Run backend/client tests appropriate to the changed endpoint, then `make check-diff`.

### Frontend API client drift without backend schema changes

1. Ensure Docker is running and Node/npm match frontend pins.
2. Run:

   ```bash
   cd frontend
   npm ci
   npm run apis:all
   git diff -- src/apis src/apisv2beta1 server/src/generated/apis server/src/generated/apisv2beta1
   ```

3. Commit intentional generated client changes with the source Swagger/proto changes. If the generated diff is unexpected, inspect OpenAPI Generator version, Docker availability, and lockfile drift.

### Requirement pin changes

1. Edit only the relevant `requirements.in` or package metadata source.
2. Run the package-specific pip-tools command. Examples in source files commonly use:

   ```bash
   pip-compile --no-emit-index-url requirements.in
   ```

3. Run install/import and targeted tests for that package.
4. Include both source and regenerated lock outputs in the same change.

## Generated-Code Troubleshooting Checklist

- Did the user edit a generated file directly? Revert the generated edit, change the source schema/template, and rerun the generator.
- Did generation change unrelated files? Check tool version, source-build/prebuilt mode, Docker image freshness, Node/npm version, and lockfiles.
- Did `make check-diff` fail after generation? Inspect `git status` and decide whether each changed file is expected generated output or a stale side effect.
- Did frontend API clients drift in CI? Run `npm run apis:all` locally with Docker and compare only the generated API directories CI checks.
- Did backend generated clients fail backwards compatibility? Review the proto change against API compatibility expectations; do not regenerate to hide an incompatible schema change.
- Did SELinux block protoc/container generation? On SELinux hosts, protoc/container generation may require temporarily permissive settings; get user approval before changing host security policy.

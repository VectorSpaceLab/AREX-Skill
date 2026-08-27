# Architecture and Layout Reference

This reference is for maintainers editing a Kubeflow Pipelines checkout. It distills repository structure and runtime architecture so future agents can choose the right owner, tests, and generated-code path without relying on the original evidence checkout.

## Scope Boundary

Use this reference for source edits, not for public package usage. If the task is to author, compile, run, or connect to KFP from user code, route to the public-use sub-skills. Use repo-development only when the user is modifying or diagnosing this repository's source tree, tests, generated artifacts, frontend/backend code, manifests, CI, or development setup.

## High-Level Runtime Flow

- The Python SDK (`kfp`) compiles Python DSL pipelines into the PipelineSpec IR.
- The backend API server consumes PipelineSpec IR and compiles or translates it for execution on Kubernetes/Argo Workflows or the Kubernetes-native APIs supported by the checkout.
- The **driver** resolves inputs, conditions, caching decisions, MLMD execution records, and runtime pod patches for tasks.
- The **launcher** transfers artifacts and invokes the Python executor inside runtime containers.
- The executor entrypoint is `sdk/python/kfp/dsl/executor_main.py`; it participates in task execution, not compilation.
- Local execution (`kfp.local.SubprocessRunner` or `DockerRunner`) bypasses the launcher path and has different dependency and isolation behavior.
- Runtime containers commonly install `kfp` with `--no-deps`. `_KFP_RUNTIME=true` disables most SDK imports to keep runtime images lightweight; task code must not rely on SDK-only modules unless the base image explicitly includes their dependencies.

## Package Relationships

Installed inspection for the source snapshot showed these synchronized distributions:

| Distribution | Package role | Snapshot version | Notes |
| --- | --- | --- | --- |
| `kfp` | Main SDK, DSL, compiler, client, local execution, CLI | `2.15.2` | Console scripts include `kfp` and `dsl-compile`. |
| `kfp-pipeline-spec` | Generated PipelineSpec protobuf Python package under the shared `kfp` namespace | `2.15.2` | Local source is `api/v2alpha1/python/`; generation is owned by `api/v2alpha1/pipeline_spec.proto`. |
| `kfp-kubernetes` | Kubernetes task-configuration addon under `from kfp import kubernetes` | `2.15.2` | Uses generated Kubernetes executor config protobufs and import rewriting during generation. |

When editing package metadata, install order, namespace packages, or generated protobufs, verify all three packages remain compatible. Version skew can surface as import failures, missing `kfp.kubernetes`, compiler schema mismatches, or generated YAML that lacks platform config.

## Monorepo Area Map

| Area | Typical owner questions | Key paths |
| --- | --- | --- |
| SDK DSL and components | public component/pipeline authoring, task modifiers, local execution | `sdk/python/kfp/dsl/`, `sdk/python/kfp/components/`, `sdk/python/kfp/local/`, `sdk/python/test/` |
| Compiler and CLI | PipelineSpec generation, type checking, CLI compile flags, component build behavior | `sdk/python/kfp/compiler/`, `sdk/python/kfp/cli/`, `api/v2alpha1/`, `test_data/` |
| PipelineSpec APIs | protobuf schema and generated Python/Go outputs | `api/v2alpha1/pipeline_spec.proto`, `api/v2alpha1/python/`, `api/v2alpha1/go/` |
| Kubernetes platform addon | Kubernetes task config helpers and platform spec protobufs | `kubernetes_platform/python/kfp/kubernetes/`, `kubernetes_platform/proto/`, `kubernetes_platform/python/test/` |
| Backend services | API server, persistence agent, cache, controllers, visualization, driver, launcher | `backend/src/`, `backend/api/`, `backend/metadata_writer/`, `backend/test/` |
| Frontend | React/TypeScript UI, frontend server, generated OpenAPI and MLMD clients | `frontend/src/`, `frontend/server/`, `frontend/src/apis*`, `frontend/src/generated/`, `frontend/scripts/` |
| Deployment manifests | Kustomize overlays, CRDs, install modes | `manifests/`, `backend/src/crd/kubernetes/` |
| Samples and fixtures | examples, compiler goldens, workflow test inputs | `samples/`, `test_data/pipeline_files/valid/`, `test_data/compiled-workflows/` |
| CI and developer tooling | GitHub Actions, composite actions, presubmit scripts | `.github/workflows/`, `.github/actions/`, `test/`, `Makefile`, `justfile` |

## Backend Component and Image Map

The backend `Makefile` builds separate linux/amd64 images from the repository root. Use these targets when a change affects a specific service image, and avoid a full image build unless necessary.

| Target | Component image | Dockerfile |
| --- | --- | --- |
| `make -C backend image_apiserver` | API server | `backend/Dockerfile` |
| `make -C backend image_persistence_agent` | persistence agent | `backend/Dockerfile.persistenceagent` |
| `make -C backend image_cache` | cache server | `backend/Dockerfile.cacheserver` |
| `make -C backend image_swf` | scheduled workflow controller | `backend/Dockerfile.scheduledworkflow` |
| `make -C backend image_viewer` | viewer controller | `backend/Dockerfile.viewercontroller` |
| `make -C backend image_visualization` | visualization server | `backend/Dockerfile.visualization` |
| `make -C backend image_driver` | v2 driver runtime image | `backend/Dockerfile.driver` |
| `make -C backend image_launcher` | v2 launcher runtime image | `backend/Dockerfile.launcher` |
| `make -C backend all` | all backend images | all of the above |

For local API-server development, `make -C backend dev-kind-cluster` creates a Kind cluster whose `ml-pipeline` deployment is scaled so a locally launched API server can replace it. For standalone UI/service exploration, `make -C backend kind-cluster-agnostic` deploys KFP in a local Kind cluster. Both require Docker or Podman, Kind, and kubectl.

## Frontend Stack

The frontend stack in the inspected checkout is React 19, TypeScript, Vite, MUI/Emotion, TanStack Query, React Router, Vitest, Testing Library, Storybook, Prettier, and ESLint. Use the Node version from `frontend/.nvmrc` and the npm package manager pinned by `frontend/package.json`.

Frontend development modes:

- `npm run mock:api` plus `npm start` for fixture-backed UI work that does not need a cluster.
- `npm run start:proxy-and-server` against a real KFP deployment when validating MLMD, pod logs, runtime artifacts, auth, backend behavior, or multi-user namespace handling.
- `npm run storybook` for component-driven UI development.
- UI smoke tests can compare a branch against a base with a live Kind backend; see development-testing for commands and prerequisites.

React review convention: use `useEffect` only for external synchronization. Derived UI state belongs in rendering, user actions in handlers, and mutation outcomes in mutation callbacks. Do not suppress `react-hooks/exhaustive-deps` unless an invariant is documented and tested.

## Contribution and Style Conventions

- Search for existing helpers before adding new code; refactor to avoid duplication.
- Keep `ResourceManager` focused on run/job persistence and lifecycle coordination.
- Keep execution-engine-specific behavior behind compiler or execution abstractions. Shared layers should remain engine-neutral.
- Put reusable interfaces in neutral packages with natural domain types and preserve documented field-wise override behavior.
- Add unit tests for non-trivial functions, methods, exported APIs, and changed behavior.
- Error messages should state the problem and corrective action.
- Go exported APIs need concise GoDoc. Python public SDK docstrings are Sphinx-facing user documentation.
- Sign commits with DCO (`git commit -s`) and do not add AI agents as co-authors.
- PR titles follow Conventional Commits with optional scopes such as `frontend`, `backend`, `sdk`, `sdk/client`, `components`, `deployment`, `metadata`, `cache`, `swf`, and `viewer`.

## Routing by Change Type

| Change description | First owner | Follow-up |
| --- | --- | --- |
| Public DSL/API behavior | `pipeline-authoring` + SDK tests | Compiler tests if output changes. |
| CLI compile behavior or PipelineSpec output | `compiler-and-cli` + compiler/CLI tests | Generated-code reference if proto/source output changes. |
| Client service behavior, auth, registry | `client-and-registry` + mocked client tests | Cluster/client tests only with endpoint prerequisites. |
| Kubernetes task config helper | `kubernetes-platform` + unit/snapshot tests | PipelineSpec/Kubernetes platform generation if proto changes. |
| Backend API proto/swagger | `repo-development` generated-code path | Backend API generation, frontend API clients, client package tests. |
| Frontend UI/server | `repo-development` frontend commands | UI smoke or e2e frontend only when Node/cluster/browser prerequisites are present. |
| Manifests/CRDs | `repo-development` manifests/generated-code path | Kustomize presubmit and cluster tests as applicable. |

Keep runtime answers explicit about which lanes were verified and which were only identified as required by CI.

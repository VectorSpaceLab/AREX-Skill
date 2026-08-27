# ZenML Integration Development

Use this reference before changing or adding ZenML integrations, component flavors, orchestrators, step operators, container registries, artifact stores, image builders, service connectors, and materializers.

## Integration Package Shape

A typical integration package follows this shape:

```text
zenml/integrations/<integration>/
  __init__.py
  constants.py
  flavors/
    __init__.py
    *_flavor.py
  orchestrators/ or step_operators/ or artifact_stores/ or image_builders/
  service_connectors/
  materializers/
  steps/ or utils/ when needed
```

Keep flavor files lightweight. Runtime implementation modules can import optional SDKs because they are loaded only when the component is actually used.

## Flavor Import Safety

- Never import optional integration SDKs at flavor module top level. This is the highest-risk integration mistake because flavor modules are imported for stack discovery on client and server paths.
- Avoid top-level imports from the integration implementation module in flavor files if that module imports optional SDKs. Instead, import the implementation inside `implementation_class`.
- Use `if TYPE_CHECKING:` imports for implementation class type hints and string annotations for property return types when necessary.
- Flavor config classes should use standard library, Pydantic, and ZenML core types. Do not type config fields with SDK classes such as cloud clients, Kubernetes objects, or SDK enum classes.
- If a flavor needs service connector compatibility, implement `service_connector_requirements` using ZenML models/constants, not SDK objects.
- Run `scripts/check_optional_imports.py` from this sub-skill to flag suspicious flavor imports before handing off a PR or generated change.

## Integration Registration and Activation

- The integration registry discovers integration packages by importing `zenml.integrations.<name>` packages that contain `__init__.py`.
- Integration classes register themselves with the registry and expose `NAME`, requirement metadata, `flavors()`, and optional `activate()` behavior.
- Activation should be best effort: if metadata says an integration is installed but a native library or transitive SDK import fails, ZenML should log and continue activating unrelated integrations.
- Do not make one broken optional integration block core ZenML imports, stack flavor listing, or unrelated pipeline compilation.

## Orchestrators

- Implement `submit_pipeline(...)` for static DAG submission and `submit_dynamic_pipeline(...)` when the backend supports dynamic pipelines.
- Containerized orchestrators should use ZenML helpers for step entrypoint commands and `self.get_image(deployment, step_name)` for built images.
- `get_orchestrator_run_id()` is the critical method: return a backend-provided ID that is stable for every step in a pipeline run and unique across separate runs.
- Static pipeline backends often expose a job/run ARN, ID, or environment variable. Do not use per-step IDs or fixed constants.
- Dynamic pipeline backends should use the orchestration environment ID. If the backend retries the orchestration container/pod, prefer a parent job/workload ID over a pod/container hostname so retries find the same ZenML run.
- If schedule support is added, keep update/delete hooks, models, CLI/client behavior, and docs aligned.
- Remote orchestrators should validate remote artifact stores, container registries, image builders, and remote ZenML server requirements before submission.

## Step Operators

- New step operators should implement the async lifecycle: `submit(info, entrypoint_command, environment)`, `get_status(step_run)`, `wait(step_run)`, and `cancel(step_run)`.
- `submit()` must return after backend submission and should persist the backend job/workload ID in step-run metadata immediately, so status, wait, cancellation, and recovery paths can find it.
- `wait()` may poll `get_status()` with backoff and fall back to server-side step status when backend status checks fail.
- `cancel()` should translate ZenML step-run metadata into a backend cancellation call and handle already-finished/not-found states idempotently when possible.
- Step-operator validators should require remote artifact stores, remote container registries, and image builders when the backend runs outside the client process.
- Per-step settings should be represented as ZenML settings classes so users can select the step operator and resources in pipeline/step configuration.

## Artifact Stores, Container Registries, and Image Builders

- Artifact stores must implement file operations through the base artifact store contract and mark `config.is_local` accurately. Remote execution depends on this flag.
- Container registries must expose image URI handling and credentials in a way image builders and orchestrators can consume without leaking secrets in logs.
- Image builders implement a `build(...)` contract using a build context and optional container registry. If a registry is provided, the resulting image must be pushed where remote components can pull it.
- Local image building depends on a working Docker or Podman engine. Cloud image builders depend on cloud project/region resources and permissions. Kubernetes/Kaniko-style builders depend on namespace, service account, registry auth, and artifact-store access when the build context is stored remotely.
- Keep `DockerSettings` interactions in the pipeline-authoring sub-skill, but validate component-side expectations here: parent image access, required integrations, build args, target repository, and registry credentials.

## Service Connectors

- Connector types declare supported auth methods and resource types; connector instances store a selected auth method, resource type, optional resource ID, expiration, and Pydantic auth config.
- `ServiceConnectorMeta` registers connector types automatically when implementation classes import. Integration activation can be needed for connector discovery.
- `_connect_to_resource()` returns an authenticated SDK/client/session for the configured resource and should raise authorization errors with user-safe messages.
- Resource ID canonicalization and default resource IDs are part of the connector contract. Bugs here show up as stack components saying no compatible connector or wrong resource type was found.
- Avoid implicit auth unless the implementation explicitly supports it and the environment setting allows it.

## Materializers in Integrations

- Integration materializers can register themselves on import through the base materializer metaclass. Activation should import them only when the integration is installed or fail gracefully if optional SDK imports are broken.
- `ASSOCIATED_TYPES` must contain classes, not strings or SDK objects unavailable at import time. If the associated type is optional, keep the materializer module behind installation checks or localize the import where feasible.
- Implement small, deterministic save/load behavior and test type compatibility. Prefer storing metadata/visualizations in files under the materializer URI through the active artifact store.

## Test and Review Checklist

- Import `zenml` and list integration names without installing the optional SDK being changed.
- Run the bundled optional-import checker against integration flavor files.
- Add or update narrow unit tests near the integration, stack, or materializer unit-test areas when the behavior is pure-Python and safe.
- Use integration tests only when the target backend, credentials, Docker/Kubernetes, or cloud service are explicitly available.
- Cross-read the maintenance sub-skill for format/lint/test command selection before running broad checks.

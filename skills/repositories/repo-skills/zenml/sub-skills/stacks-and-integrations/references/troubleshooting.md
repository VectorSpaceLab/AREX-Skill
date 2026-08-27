# ZenML Stack and Integration Troubleshooting

Use this reference when stack registration, component validation, integration imports, service connectors, materializers, orchestrators, step operators, Docker, container registries, or image builders fail.

## Missing Extras and Optional SDKs

Symptoms:
- `ModuleNotFoundError` or `ImportError` for a cloud SDK, ML framework, Kubernetes package, Docker helper, or integration-specific library.
- `zenml integration list` shows an integration unavailable, or activation logs say registration side effects were skipped.
- A stack component fails to hydrate from a stored model and suggests exporting stack requirements.

Actions:
- Install the narrow extra or integration dependency needed for the active component; avoid recommending broad dev/all extras unless the task is repository maintenance.
- If the failure happens while importing `zenml` or listing flavors, inspect integration flavor files for top-level optional SDK imports. Flavor files must remain importable without optional SDKs.
- If activation fails but core ZenML still imports, distinguish missing optional functionality from a core breakage. The integration may need lazy imports or activation error handling rather than broader dependency installation.
- For custom flavors, verify the dot-path source is importable from the active Python path and that implementation dependencies are installed only where the component is actually used.

## Optional SDK Import Breakage in Flavor Files

Symptoms:
- Importing a flavor module fails before the component is selected.
- Server/client flavor registration warns that an integration failed to register flavors.
- Base ZenML operations fail after adding an integration dependency import.

Actions:
- Move optional SDK imports out of integration flavor modules.
- Replace top-level implementation imports with method-local imports inside `implementation_class`.
- Guard type-only implementation imports with `if TYPE_CHECKING:` and quote annotations.
- Replace SDK-typed config fields with primitive/Pydantic/ZenML-core types and translate to SDK objects in the implementation module.
- Run the bundled optional-import checker against the integration package root from an active checkout to find suspicious imports.

## Service Connector Auth and Resource Types

Symptoms:
- A component cannot find a compatible connector.
- Connector verification succeeds but component registration or connection fails.
- Resource discovery lists a resource under a different type or ID than the component expects.
- Credentials expire, implicit auth is rejected, or a connector silently clears an invalid resource ID.

Actions:
- Compare the flavor's `service_connector_requirements` with the connector type/resource type/resource ID configured on the connector.
- Verify auth method-specific config fields and whether short-lived credentials have expired.
- Check canonical resource ID behavior for single-resource connector types; ensure the default resource ID is implemented when the type does not support multiple instances.
- Confirm implicit auth is allowed only when the connector type supports it and the environment permits implicit methods.
- Prefer connector-linked components or secret references over plaintext credentials in component config.

## Orchestrator Run ID Stability

Symptoms:
- Duplicate pipeline runs appear after retry/resume.
- Downstream steps cannot find the run created by the first step.
- Dynamic child pipelines rerun instead of resolving the existing child run.
- Run IDs differ between steps in the same backend pipeline.

Actions:
- Audit `get_orchestrator_run_id()` first. It must return the same ID for all steps in one pipeline run and a different ID for different backend runs.
- For static pipelines, use a backend pipeline/job/run ID or environment variable common to every step, not a per-step job ID or a generated timestamp.
- For dynamic pipelines, use the orchestration environment's stable parent job/workload ID. Avoid pod/container hostnames if a retry creates a new pod for the same orchestration job.
- Keep the returned ID short enough for database storage and avoid embedding mutable retry counters.
- When dynamic child pipelines are involved, cross-read pipeline-authoring guidance and test child-key/root-run/parent-run behavior.

## Step Operator Async Lifecycle

Symptoms:
- A step submits successfully but `wait()` or `cancel()` cannot find the backend job.
- Step status remains running after backend completion.
- Cancellation works only before metadata is persisted.
- `StepLauncher` falls back to legacy `launch()` unexpectedly.

Actions:
- Implement `submit()`, `get_status()`, `wait()`, and `cancel()` for new step operators.
- Persist backend job/workload identifiers to step-run metadata immediately after submission.
- Map backend statuses to ZenML `ExecutionStatus` values and treat not-found/already-completed states carefully.
- Ensure `wait()` polls `get_status()` and returns on finished or retrying statuses; use server-side status as a fallback when backend status checks fail.
- Validate remote artifact store, remote container registry, and image builder requirements before submission so failures happen at stack validation time.

## Docker, Container Registry, and Image Builder Failures

Symptoms:
- Docker daemon or Podman socket cannot be reached.
- Image build succeeds locally but remote backend cannot pull the image.
- Registry push fails with unauthorized, not found, or rate-limit errors.
- Kaniko/cloud build cannot read the build context or push final images.
- `DockerSettings` options are ignored or unsupported by the selected image builder.

Actions:
- Check which container engine the ZenML client is configured to use and whether the engine is installed, running, and authenticated to the target registry.
- If the backend is remote, require a non-local container registry and confirm the image builder pushes to a URI the backend can pull.
- Verify registry credentials through the container registry component or a service connector; do not print credentials in logs or generated code.
- For cloud image builders, check cloud project/region, build service role permissions, artifact-store read permissions, parent image access, and registry push permissions.
- For Kubernetes/Kaniko builders, check namespace, service account, image pull secrets, registry config, and whether the build context is transferred through the Kubernetes API or artifact store.
- If a build option depends on Docker BuildKit or subprocess mode, verify the selected local image-builder settings support it.

## Stack Validation Failures

Symptoms:
- `StackValidationError`, missing component errors, or remote component/local store mismatch.
- Remote step operator reports local artifact store or local registry.
- Component registration accepts config but pipeline submission fails later.

Actions:
- Run stack validation before submission and inspect each component's `validator`, `config.is_local`, and `config.is_remote` behavior.
- Attach required components declared by validators, especially `CONTAINER_REGISTRY` and `IMAGE_BUILDER` for remote execution.
- Ensure artifact store and registry flavors match the execution location: local for local-only workflows, remote for cloud/Kubernetes/step-operator workflows.
- If a stack uses a local ZenML store with remote components, switch to a remote ZenML server or local-only stack components.

## Materializer Failures

Symptoms:
- Custom materializer class definition raises `MaterializerInterfaceError`.
- Save/load works locally but fails in a remote stack.
- Visualization or metadata files are missing.

Actions:
- Ensure `ASSOCIATED_TYPES` is a tuple of classes and `ASSOCIATED_ARTIFACT_TYPE` is a valid ZenML artifact type.
- Read/write through `self.artifact_store` and paths below `self.uri`; avoid assuming a local filesystem for remote stacks.
- Keep optional SDK imports scoped to materializer modules that are loaded only when the integration is installed/used.
- Add type compatibility tests for parent/child classes when registering a custom materializer.

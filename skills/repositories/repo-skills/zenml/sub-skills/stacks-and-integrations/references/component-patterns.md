# ZenML Component Patterns

This reference summarizes stack/component patterns future agents need without reopening the ZenML source tree.

## Stack Composition

- A ZenML `Stack` combines required `orchestrator` and `artifact_store` components with optional `container_registry`, `image_builder`, `step_operator`, `experiment_tracker`, `alerter`, `annotator`, `data_validator`, `feature_store`, `model_deployer`, `model_registry`, `deployer`, `log_store`, and `sandbox` components.
- Step operators, experiment trackers, alerters, and sandboxes can be repeatable. The first attached component is the default; non-default components can be selected by name in step or pipeline configuration.
- Stack validation should fail early when required components are missing, when a component object has the wrong base class for its declared `StackComponentType`, or when a remote component would run against a local ZenML store.
- A stack that uses a remote orchestrator or remote step operator generally needs a remote ZenML server, a remote artifact store, a remote container registry, and an image builder capable of building/pushing the step image.

## Flavor and Component Abstractions

- A stack component flavor binds a `name`, `StackComponentType`, `config_class`, and `implementation_class`.
- `StackComponentConfig` is Pydantic v2 based and must remain importable without heavy optional SDKs so ZenML can validate component configuration on client and server paths.
- Sensitive config values should use ZenML secret field patterns or secret references. Do not attach Pydantic validators to fields that users should be able to fill with secret references because validators run before secret resolution.
- Implementation classes inherit from the relevant base component class and expose config via `self.config`; optional SDK clients should be created lazily on the implementation side, not in flavor/config module import paths.
- Component-level `requirements` should include only packages needed to use that component, while integration package dependency metadata should keep optional extras narrow.

## Registering and Managing Stacks

- Register a custom flavor by dot path through the component-specific CLI command, for example `zenml artifact-store flavor register package.module.MyFlavor`.
- Register a component with its flavor-specific fields, then attach it to a stack by component type. For unknown fields, inspect the command help after passing `-f` or `--flavor` so the flavor-specific configuration section is shown.
- Python API stack operations should go through `Client` resource methods; avoid importing server/store internals from integration code.
- When a task mixes CLI usage and component implementation, split concerns: use the CLI/client sub-skill for command syntax and this sub-skill for the implementation invariants.

## Service Connectors

- Service connectors store authentication configuration, validate auth methods, discover compatible resources, and provide short-lived or scoped credentials to stack components.
- Connector compatibility is expressed through connector type, resource type, resource ID, and optional resource ID attribute requirements on flavors.
- A service connector validates/canonicalizes resource IDs during initialization. If a resource type does not support multiple instances, the connector implementation must provide a default resource ID.
- When a stack component cannot authenticate, check the connector `auth_method`, resource type, resource ID, expiration, implicit-auth policy, and whether the flavor advertises the expected connector requirements.
- Prefer connectors or secret references over hard-coded credentials in component config. Never suggest embedding credentials in pipeline code.

## Materializers

- A `BaseMaterializer` subclass must set `ASSOCIATED_TYPES` to one or more Python classes; ZenML rejects non-class entries during class creation.
- If `ASSOCIATED_ARTIFACT_TYPE` is set, it must be a valid `ArtifactType` value.
- Implement `save(self, data)` and `load(self, data_type)` as the primary artifact IO contract; optional methods include visualization saving, metadata extraction, content hashing, item counts, and item loading.
- Materializers read and write through `self.artifact_store`, which defaults to the active stack artifact store unless explicitly injected.
- Integration materializers may import their optional SDKs in the materializer module because they are used on demand, but their integration package activation should tolerate missing/broken SDKs where possible.

## Remote Execution and Image Requirements

- Remote orchestrators and step operators usually need `StackValidator(required_components={CONTAINER_REGISTRY, IMAGE_BUILDER}, custom_validation_function=...)` or equivalent checks.
- If the active artifact store is local, remote backends cannot reliably exchange files with the ZenML client/server; produce a direct validation message telling the user to use a remote artifact store.
- If the active container registry is local or missing, remote backends cannot pull built images; tell the user to attach a remote registry and authenticate it, often through a service connector.
- The local image builder builds with Docker or Podman on the client machine and pushes to the stack container registry. Failures commonly come from a missing container engine, daemon/socket access, registry login, BuildKit-only options, or incompatible build context settings.
- Some image builders need additional cloud/Kubernetes resources and permissions. Validate service-account/IAM permissions to read artifact build context, pull parent images, and push final images.

## Native Test Anchors

- Stack behavior is covered by tests that initialize stacks from components, validate required components, validate remote-server requirements, and assert orchestrator submission delegation.
- Stack component behavior is covered by tests for config serialization, secret references, immutable public fields, JSON-string conversion, and custom flavor registration.
- Materializer behavior is covered by tests for associated types, artifact type validation, load/save type compatibility, and registry behavior.
- Use these as native verification candidates after the full runtime skill is integrated; do not run broad integration test suites unless explicitly authorized and the required backends are available.

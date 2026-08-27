# Component and domain API

This reference is for agents changing Viseron's backend extension surface: components, domains, entities, events, and shared core APIs. For reload-specific behavior, pair it with [Reload and lifecycle](reload-and-lifecycle.md).

## Component shape

A component is a package imported as `viseron.components.<component_name>`. Keep the component directory name lowercase and define stable constants in `const.py`, including at least `COMPONENT = "<component_name>"` and schema description constants such as `DESC_COMPONENT`.

A component can be stateless or stateful:

- **Stateless component**: exposes `setup_domains(vis, config) -> None` only. Use this when the component does not need shared resources before registering domains. Examples in Viseron follow this pattern for components whose work is domain-driven.
- **Stateful component**: exposes `setup(vis, config) -> bool` and often `setup_domains(vis, config) -> None`. Use `setup()` for expensive/shared resources such as clients, model handles, subprocess managers, caches, or background workers, and use `setup_domains()` only to register domains.

Lifecycle rules enforced by the component loader:

1. `CONFIG_SCHEMA`, when present, is applied before setup.
2. `setup()` is called before `setup_domains()` unless the reload path explicitly asks for `domains_only=True`.
3. `setup()` must return `True` or `False`; non-boolean returns are treated as failure.
4. If there is no `setup()` but there is `setup_domains()`, setup is considered successful before domain registration.
5. A component with neither `setup()` nor `setup_domains()` fails.
6. `ComponentNotReady` means transient component setup failure and schedules a retry. Use it only when a future retry is expected to help.
7. `unload(vis)` is optional but required for stateful resources that must stop threads, close clients, remove `vis.data` entries, or unsubscribe callbacks.

### Hot-reload-safe `setup_domains()`

`setup_domains()` may be called repeatedly during config reload. It must be idempotent and side-effect-light:

- Do register pending domains with `setup_domain(...)`.
- Do prune per-identifier domain config when the domain setup expects `{identifier: config}` rather than the full component config.
- Do declare dependencies with `RequireDomain` and `OptionalDomain` at registration time.
- Do not start threads, open sockets, load models, allocate hardware resources, mutate shared state, or publish events here.
- Do not assume duplicate calls will re-run a loaded domain; the registry prevents duplicate domain/identifier registration.

## Configuration schemas

Viseron uses `voluptuous` schemas. A component-level schema normally looks like:

```python
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(COMPONENT, description=DESC_COMPONENT): vol.Schema(
            {
                vol.Optional(
                    CONFIG_OPTION,
                    default=DEFAULT_OPTION,
                    description=DESC_OPTION,
                ): str,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
```

Guidelines:

- Put every option key/default/description in constants so code, tests, and docs stay aligned.
- Put useful text in `description=`; schema descriptions are used to generate component configuration docs.
- Use `extra=vol.ALLOW_EXTRA` at the component root so Viseron's global config can contain other components.
- Use domain base schemas when implementing an existing domain, then extend with component-specific options.
- Use `Deprecated` for old options so validation can warn while docs can explain the replacement.
- Validate at the component or domain level before opening live resources. Validation failure should block reload before mutating existing loaded components.

## Domain registration

A domain is an interface type such as `camera`, `object_detector`, `motion_detector`, `nvr`, `face_recognition`, `image_classification`, or `license_plate_recognition`. Components provide implementations by placing a domain module under their package and registering instances from `setup_domains()`.

Registration pattern:

```python
from viseron.domains import RequireDomain, OptionalDomain, setup_domain


def setup_domains(vis: Viseron, config: dict[str, Any]) -> None:
    component_config = config[COMPONENT]
    for camera_identifier in component_config[CONFIG_OBJECT_DETECTOR][CONFIG_CAMERAS]:
        setup_domain(
            vis,
            COMPONENT,
            "object_detector",
            component_config,
            identifier=camera_identifier,
            require_domains=[RequireDomain(domain="camera", identifier=camera_identifier)],
            optional_domains=[OptionalDomain(domain="motion_detector", identifier=camera_identifier)],
        )
```

`setup_domain()` registers a `DomainEntry` in `PENDING` state. The component must already be in Viseron's `LOADING` or `LOADED` component store; calling it from arbitrary module import time or a background thread can fail.

### Required versus optional dependencies

- `RequireDomain(domain, identifier)` means the target domain/identifier must be configured and loaded before setup starts. Missing required dependencies fail validation of pending domains.
- `OptionalDomain(domain, identifier)` means wait for that dependency only if it is configured. This is the right choice for behavior that improves with another domain but can run without it.
- Dependencies are identifier-specific. If a camera id changes, dependent NVR/detector domains for that identifier must unload and re-register under the new id.

## Domain modules and setup

A domain implementation module is imported as `viseron.components.<component>.<domain>`. It should expose:

```python
def setup(vis: Viseron, config: dict[str, Any], identifier: str, attempt: int = 1) -> bool:
    ...
    DomainImplementation(vis, COMPONENT, config, identifier)
    return True
```

The `attempt` parameter is optional. If it is present, Viseron passes the current retry attempt. Raise `DomainNotReady` for transient startup conditions such as a camera/service/model not being ready yet; Viseron retries with backoff unless reload/shutdown cancels the retry. Let permanent coding/config/import errors fail fast instead of retrying forever.

Domain classes should extend the appropriate abstract base class. The base-domain metaclass calls `__post_init__()` after `__init__()`. Existing abstract bases register themselves with `vis.register_domain(domain, identifier, self)` in that hook, so a successful constructor normally makes the instance discoverable through `vis.get_registered_domain(...)` and `vis.get_registered_identifiers(...)`.

## Viseron core APIs for extensions

Use the `vis` object rather than ad-hoc global state:

- `vis.data`: shared process registry for component resources. If a component writes a new key, add the matching typed field to `ViseronData` under a type-checking import to avoid early circular imports.
- `vis.domain_registry`: inspect domain entries, state, dependencies, futures, and dependents when diagnosing lifecycle issues.
- `vis.get_registered_domain(domain, identifier)`: retrieve a loaded dependency domain instance; raises if missing or not loaded.
- `vis.get_registered_identifiers(domain)`: retrieve all loaded instances for a domain type.
- `vis.add_entity(component, entity, domain=None, identifier=None)`: register entities in the state registry and associate them with a component/domain/identifier for unload cleanup.
- `vis.listen_event(event_name, callback_or_queue, ioloop=None)`: subscribe to an event topic; store and call the returned unsubscribe callable in cleanup.
- `vis.dispatch_event(event_name, EventDataSubclass(...), store=True)`: publish an event and optionally persist it.
- `vis.register_signal_handler(signal, callback)`: subscribe to lifecycle signals such as shutdown; store the unsubscribe callable.
- `vis.background_scheduler`: schedule periodic work. Remove jobs in `unload()` or entity cleanup when the job should not survive reload.

`listen_event()` and `register_signal_handler()` require the data stream component to be loaded. If a component may initialize early, guard that dependency or delay subscription until setup time.

## Events and data stream

Events are dataclasses derived from `EventData`. Override `as_dict()` when payloads need custom JSON-safe shape, and set `json_serializable = False` for frame objects, queues, domain instances, or other non-serializable payloads. Viseron publishes events through the data stream under `event/<event_name>`.

For low-level data stream topics, publish/subscribe through the data stream component. Wildcard subscriptions are supported, and callbacks can be normal callables, standard queues, or Tornado queues with an `IOLoop`.

## Entity classes

Entities expose state to the state registry and integrations such as MQTT/Home Assistant.

Base behavior:

- Subclass `Entity`, `BinarySensorEntity`, `SensorEntity`, `ToggleEntity`, or `ImageEntity`.
- Provide a stable `name`; optionally provide `object_id` if the generated id should not be based on `name`.
- Do not override `attributes`; override `extra_attributes` instead.
- Use `set_state()` after internal state changes. `vis.states.set_state()` dispatches state-change events.
- Store event unsubscribe callables in `_event_listeners` and call them from `unload()`; the base `Entity.unload()` already iterates that list.
- If an entity has setup work, implement `setup()` and also implement `unload()` to avoid development warnings and stale callbacks.

When adding entities from a domain implementation, pass the domain and identifier to `vis.add_entity(component, entity, domain, identifier)`. That association lets reload unload only the affected identifier's entities.

## Adding a detector component: checklist

For a new detector component that implements an existing detector domain:

1. Create component constants and schema descriptions.
2. Extend the target domain's base config schema and add component-level options such as model path, device, thresholds, service URL, or credentials.
3. If the detector has shared state, load it in `setup()` and store it in `vis.data[COMPONENT]`; otherwise omit `setup()`.
4. In `setup_domains()`, iterate configured camera identifiers and call `setup_domain()` for the target detector domain.
5. Use `RequireDomain(domain="camera", identifier=camera_identifier)` for camera-bound detectors.
6. Add optional dependencies only when the detector can run without them.
7. Keep `setup_domains()` registration-only so identifier-level camera reloads can safely call it again.
8. In the domain module, validate domain config, instantiate the abstract-domain subclass, and return `True`.
9. Raise `DomainNotReady` only for transient dependency readiness; use normal exceptions or `False` for permanent setup failures.
10. Add `unload()` methods for any threads, queues, events, model handles, sockets, or scheduler jobs.
11. Add focused tests for schema validation, domain registration dependencies, setup success/failure, retry, and reload behavior.
12. Use [Docs, tests, and packaging](docs-tests-and-packaging.md) before updating generated docs or running broad test suites.

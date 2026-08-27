# Troubleshooting developer-extension failures

Use this reference for component/domain/reload/entity/docs/import failures owned by this sub-skill. For lifecycle background, see [Reload and lifecycle](reload-and-lifecycle.md); for API contracts, see [Component and domain API](component-domain-api.md).

## Component setup and schema failures

| Symptom | Likely cause | Action |
|---|---|---|
| Component goes to `FAILED` before setup logic runs. | `CONFIG_SCHEMA` rejected the config or raised an unexpected exception. | Reproduce with the component's schema only. Check `vol.Required`/`vol.Optional` nesting, defaults, `description=`, and custom validators. Validation should not open live resources. |
| `Setup of component <name> did not return boolean`. | `setup()` returned `None`, an object, or another truthy value instead of `True`/`False`. | Return `True` after successful setup and `False` only for permanent setup failure. Store resources in `vis.data[COMPONENT]` instead of returning them. |
| Component reports it has neither `setup()` nor `setup_domains()`. | New component package lacks both hooks or the hook names are misspelled. | Add `setup()` for stateful resources, `setup_domains()` for domain registration, or both. |
| Component remains `RETRYING`. | `ComponentNotReady` was raised and retry timer is active. | Confirm the failure is transient. If the condition is permanent (bad config, missing module, unsupported hardware), fail clearly instead of retrying. Reload/shutdown cancels retry timers. |
| `setup_domains()` failure after successful `setup()`. | Domain registration code raised, often due bad config key, wrong component constant, or calling live side effects. | Keep `setup_domains()` registration-only. Validate config before setup, and use the validated config shape passed into the hook. |
| Duplicate domain/identifier warning. | Two components or repeated registration attempted the same domain and identifier. | Confirm the identifier is correct and unique per domain. If hot reload called `setup_domains()` again, the warning may be benign only for already pending entries; do not rely on duplicate registration for updates. |

## Domain setup and dependency failures

| Symptom | Likely cause | Action |
|---|---|---|
| `Component <name> not found for setting up domain <domain>`. | `setup_domain()` was called when the owning component was not in `LOADING` or `LOADED`. | Call `setup_domain()` from the component's `setup_domains()` hook, not at module import time or from unrelated background code. |
| Domain fails with `Required domain <domain> with identifier <id> not configured`. | A `RequireDomain` dependency was declared but no matching domain/identifier is configured. | Fix the config or change to `OptionalDomain` only if the domain can genuinely run without that dependency. Check identifier spelling. |
| Domain waits indefinitely or logs slow dependency warnings. | Dependency future is still running, retrying, or failed. | Inspect domain registry states for the required and optional dependencies. If a dependency is optional but absent, it should not block; if it is configured and failing, fix that dependency first. |
| Domain setup returns `False` or non-boolean. | Domain module `setup()` did not return the required boolean. | Instantiate the domain class, let its post-init register the instance, and return `True`. Return `False` only for permanent failure. |
| Domain enters `RETRYING`. | Domain module raised `DomainNotReady`. | Use `DomainNotReady` only for transient readiness. If setup accepts an `attempt` argument, log or branch on retry count as needed. Reload/unload cancels retries. |
| Domain module import fails. | Wrong module name, missing optional package imported at module import time, or packaging/source-root issue. | Confirm the module path is `viseron.components.<component>.<domain>`. Move optional hardware/service imports deeper when possible so schema and registration can be inspected without optional runtime packages. Check the `manager.py` caveat below. |

## Reload failures

| Symptom | Likely cause | Action |
|---|---|---|
| Reload aborts but old setup remains active. | New config failed validation. | This is expected. Fix `CONFIG_SCHEMA` or config values; validation runs before unload/setup to preserve the loaded system. |
| Reload says restart is required for a default component. | Default component changed and was removed from hot-reload application. | Do not force hot reload for default/core behavior unless the reload code explicitly supports it. Surface restart requirement. |
| Identifier-level camera change did not reload NVR/object detector. | Dependent domains were not registered with `RequireDomain`/`OptionalDomain` using the same camera identifier. | Inspect domain registry entries and dependency lists. Add dependency declarations in the dependent component's `setup_domains()`. |
| Identifier-level change reloads too much. | Change was classified as component-level or domain-level, or shared state lives in the component instead of identifier domain instances. | Revisit config nesting and diff classification. Move per-camera state into domain instances when targeted reload is desired. |
| Stale entity remains after reload. | Entity was added without domain/identifier ownership or lacks unload cleanup. | Add entities with `vis.add_entity(component, entity, domain, identifier)` for domain-owned entities. Implement `unload()` for event listeners/jobs. |
| Stale callback fires after reload. | Event/data-stream unsubscribe callable was not stored or called. | Store every unsubscribe callable from `vis.listen_event()` and `vis.register_signal_handler()` and call it in component/domain/entity unload. |
| Reload hangs around retrying domains. | A domain retry was active and not cancelled/cleared as expected. | Confirm `domain_registry.cancel_all_retries()` runs before reload and that domain setup responds to `entry.cancel_event`. Avoid long uninterruptible sleeps in setup. |

## Entity, event, and data-stream failures

| Symptom | Likely cause | Action |
|---|---|---|
| `ValueError: Entity name is required`. | Entity subclass did not define `name`. | Define a stable `name`; define `object_id` when the generated id should be stable across name changes. |
| Entity ids get suffixes like `_1`. | Multiple entities generate the same `domain.object_id`. | Assign unique `object_id` values or include camera/component context in the name/object id. |
| `RuntimeError: Attribute vis has not been set`. | `entity.set_state()` was called before `vis.add_entity()` registered the entity. | Only call `set_state()` after the entity has been added to Viseron's state registry. |
| `DataStreamNotLoaded` when listening for events or signals. | Component subscribed before the data stream component was loaded. | Subscribe during normal component setup after default/core components are available, or declare/guard the dependency. |
| Event persistence fails or logs JSON errors. | Event payload is not JSON serializable but `json_serializable` remains `True`. | Set `json_serializable = False` for frames, queues, domain instances, and other non-JSON objects, or implement a safe `as_dict()`. |

## Docs and schema inspection failures

| Symptom | Likely cause | Action |
|---|---|---|
| Generated docs omit option descriptions. | Schema markers lack `description=` or descriptions are not constants used in the schema. | Add `DESC_*` constants and pass them to `vol.Required`/`vol.Optional`/`Deprecated`. |
| Docs metadata has unsupported tags. | Component/domain tags include a name outside the supported set. | Use only supported domain names or `system`. |
| Safe schema helper fails to import a component. | Optional dependency, hardware vendor package, service client, or top-level `manager.py` is unavailable. | Treat as import evidence. Try a simpler component, inspect with optional domain imports disabled, or use a source-root/package setup that exposes required top-level modules. Do not install heavy optional stacks unless needed for the task. |
| Maintainer docs generator would write Docusaurus files. | The original generator is a writer, not a read-only inspector. | Use the bundled read-only helper first. Only run docs generation when the task explicitly includes docs updates. |

## Source-root and subprocess import failures

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: No module named 'manager'`. | Subprocess-related modules import top-level `manager.py`, but the source root or packaged top-level module is not importable. | Run from a source root with top-level `manager.py` on `sys.path`, or verify the installed distribution includes it. Do not leak local environment paths into docs or generated runtime content. |
| Storage or detector subprocess imports fail during schema inspection. | Component import pulls subprocess support at module import time. | Keep schema/doc helpers narrow. For new code, avoid importing heavy subprocess modules at top level when schema inspection should be lightweight. |
| A subprocess worker works in-source but not installed. | Worker command, current working directory, or package data differs between source and installation. | Verify packaging includes required top-level support files and that subprocess commands execute with a predictable import path. |

## Optional hardware/service/container caveats

This sub-skill may describe CUDA, VA-API, EdgeTPU, Hailo, live cameras, MQTT brokers, notification services, databases, and containers as requirements or troubleshooting context. Unless a task explicitly verifies those resources, treat them as unverified optional behavior. Do not claim local verification for hardware/service/container paths based only on schema import or mocked unit tests.

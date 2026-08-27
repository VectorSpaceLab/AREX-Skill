# Reload and lifecycle

This reference explains how component/domain state, unload order, retries, and config reload interact. Use it with [Component and domain API](component-domain-api.md) when changing extension code.

## State model

Component state values:

- `LOADING`: setup is in progress or a retry is active.
- `LOADED`: setup returned `True` and any component-owned domains were registered.
- `FAILED`: validation, import, setup, `setup_domains()`, or owned domain setup failed permanently.
- `RETRYING`: setup raised `ComponentNotReady` and a retry timer is scheduled.

Domain state values:

- `PENDING`: registered by a component and waiting for setup.
- `LOADING`: dependencies resolved and setup is running.
- `LOADED`: setup returned `True` and the domain instance was registered.
- `FAILED`: dependency, import, validation, setup, or unload-related state transition failed.
- `RETRYING`: setup raised `DomainNotReady` and will retry unless cancelled.

Component errors include the source (`validation`, `setup`, `setup_domains`, `domain`, `import`) plus component/domain/identifier context where available. Status events are dispatched when state or validation error changes.

## Initial setup order

On startup, Viseron loads config, sets `vis.config`, sets up components, then sets up all pending domains, then marks initialization complete.

Component setup order is intentionally staged:

1. Core components.
2. Logging components.
3. Default components.
4. Non-core, non-default configured components in parallel.
5. Pending domains after components have registered them.

If a critical component fails during startup, Viseron activates safe mode and sets up only the core/logging/default subset from the last known good critical configuration when available.

## Component unload behavior

`unload_component(vis, component_name)`:

1. Cancels any `ComponentNotReady` retry timer for that component.
2. Finds the loaded component instance.
3. Unloads every domain type previously registered by that component.
4. Unloads component-level entities tracked in the state registry.
5. Calls the component module's optional `unload(vis)` function.
6. Removes the component from the loaded store.
7. Returns names of other components affected by dependent-domain unloads.

Component `unload(vis)` should be defensive: stop threads/processes, close clients, remove `vis.data[COMPONENT]`, remove scheduler jobs, and tolerate partial setup.

## Domain unload behavior

`unload_domain_chain(vis, domain, identifier)` unloads a domain and every loaded dependent in dependents-first order. Required and optional dependencies both count when finding dependents. The root domain's component is intentionally not returned in the affected component set; only dependent components are returned.

`unload_domain_identifier(...)`:

1. Cancels any retry for that domain/identifier.
2. Unloads entities owned by the component/domain/identifier.
3. Calls the domain instance's optional `unload()` method.
4. Unregisters the domain entry.

`unload_domain(vis, component, domain)` unloads all identifiers for that component/domain and then calls the domain module's optional `unload(vis)` hook.

## Config reload flow

`reload_config(vis)` cancels all retrying domains, waits until initial setup has completed, and then applies `_reload_config(...)` under `vis.reload_lock`.

The reload algorithm:

1. Clear stale validation errors from loaded/loading/failed component instances.
2. Load new config and diff it against `vis.config`.
3. Classify changes into component-level, domain-level, and identifier-level reload actions.
4. Mark default-component changes as `restart_required`; default component changes are removed from hot-reload application.
5. Validate every changed component against the new config before mutating loaded components.
6. Abort without unload/setup if validation fails.
7. Unload removed components and collect affected dependent components.
8. Mark added components for full setup.
9. Unload modified components and mark them for full setup.
10. Unload modified domains and mark their owner components for domain-only setup.
11. Unload modified identifiers and dependent chains, then mark owner components for domain-only setup.
12. Unload cancelled retry domains and collect affected dependent components.
13. Apply the setup plan, unload dependents of newly pending optional dependencies, set up pending domain registrations, and update `vis.config`.

## Change classification

A component-level change reloads the whole component. Use this for options outside domain/identifier maps or for shared resources that cannot be changed per identifier.

A domain-level change reloads all identifiers for that component/domain. Use this when an option under a domain affects all identifiers, shared detector behavior, or schema grouping.

An identifier-level change reloads one domain/identifier and its dependents. Use this when a change is contained to one camera id or detector id. The reload path:

- Adds the owner component to `plan.domain_components`.
- If an existing domain entry is present, calls `unload_domain_chain()` for that entry.
- If the identifier is newly added, also calls `unload_domain_chain()` for that new domain/identifier so existing loaded dependents that reference it can be revisited.

## Applying the setup plan

`_apply_setup_plan()` runs full component setup first, then domain-only setup for affected dependent components not already set up fully, then `setup_domains(vis)` for every pending domain. After full component setup registers new pending domains, Viseron unloads loaded or failed dependents of those pending domains so optional dependencies can take effect.

The domain-only setup path calls component `setup_domains()` without re-running `setup()`. This is why `setup_domains()` must not allocate stateful resources.

## Retry behavior

Component retries:

- Raise `ComponentNotReady` only when retrying setup later is correct.
- Retry wait grows with attempt count up to a maximum.
- Reload or shutdown cancels pending retry timers.
- Retried setup clears failed/loading state and component errors.

Domain retries:

- Raise `DomainNotReady` for transient domain readiness.
- If the domain setup function accepts an `attempt` argument, Viseron passes the current retry count.
- Retry waits with backoff and is cancelled by shutdown, domain unload, or reload.
- On retry, previous errors for that domain/identifier are cleared from the owning component before setup runs again.

Do not use retry exceptions for malformed config, missing Python modules, unsupported hardware selected by config, or programming errors. Those should fail clearly.

## Diagnosing identifier-level camera reloads

Difficult case: only one camera identifier's config changed, but dependent NVR/object detector domains must unload and re-setup.

Expected behavior:

1. The config diff reports an `IdentifierChange` for the camera domain and identifier.
2. Reload adds the camera component to the domain-only setup plan.
3. Reload finds the current `DomainEntry` for `camera/<identifier>` and calls `unload_domain_chain()`.
4. `unload_domain_chain()` traverses dependents registered with `RequireDomain("camera", identifier)` or `OptionalDomain("camera", identifier)`.
5. Dependents such as `nvr/<identifier>` and `object_detector/<identifier>` unload before the camera.
6. The returned dependent component names are added to `plan.domain_components`.
7. Domain-only setup calls `setup_domains()` for those components and then `setup_domains(vis)` loads the newly pending camera/detector/NVR entries.

If a dependent is not reloaded:

- Check that the dependent called `setup_domain()` with the same identifier string used by the camera.
- Check that the dependent declared the camera as `RequireDomain` or `OptionalDomain` rather than fetching it later with no registry dependency.
- Check that the domain class registered itself through `vis.register_domain()` during construction.
- Check that the component tracks its registered domains through `Component.add_domain_to_setup()`; this happens automatically when using `setup_domain()` from component `setup_domains()`.
- Check whether the changed option was classified as component-level or domain-level instead of identifier-level.

## Hot reload design rules

- Keep expensive shared resources in `setup()` and reuse them for `domains_only=True` reloads.
- Keep domain registration in `setup_domains()` and make it safe to call multiple times.
- Keep per-identifier resources in the domain instance so identifier reload can unload only that chain.
- Put cleanup in both component `unload(vis)` and domain/entity `unload()` where ownership differs.
- Store event unsubscribe callbacks and remove them in unload paths.
- Associate entities with domain and identifier via `vis.add_entity(component, entity, domain, identifier)` so targeted unload removes the right state entries.
- Validate new config before stopping old resources; validation errors should leave the currently loaded setup untouched.

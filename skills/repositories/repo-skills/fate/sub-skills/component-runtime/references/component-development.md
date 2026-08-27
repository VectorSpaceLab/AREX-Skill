# Component Development

This reference collects the developer-facing parts of the FATE component runtime that matter when you are authoring or diagnosing components.

## Authoring shape

A built-in component is declared with `@cpn.component(...)`, and the callback must start with `ctx` and `role`.

```python
@cpn.component(roles=[GUEST, HOST], provider="fate")
def my_component(ctx, role):
    ...

@my_component.train()
def train(ctx, role, train_data: cpn.dataframe_input(roles=[GUEST, HOST])):
    ...

@my_component.predict()
def predict(ctx, role, test_data: cpn.dataframe_input(roles=[GUEST, HOST])):
    ...
```

### Authoring rules backed by the runtime

- Use `cpn.parameter(...)` for scalar or structured parameters.
- Use `cpn.dataframe_input`, `cpn.dataframe_output`, `cpn.json_model_input`, `cpn.json_model_output`, `cpn.model_directory_input`, `cpn.model_directory_output`, `cpn.data_directory_input`, and `cpn.data_directory_output` for artifacts.
- Use plural artifact helpers such as `dataframe_inputs` or `json_model_outputs` when the component emits multiple artifacts.
- For non-stage components, put the inputs and outputs directly on the root function and let the runtime use the `default` stage.
- For stage-specific components, define `train`, `predict`, and/or `cross_validation` methods with the matching decorators.
- The runtime filters active artifacts by role and stage when it builds the execution I/O contract.

## Discovery and registration

- Built-ins are loaded lazily by `LazyBuildInComponentsLoader` in the built-in component registry.
- Third-party descriptors are discovered through the `fate.ext.component_desc` entry-point group.
- `load_component(name, stage)` checks the built-in catalog first and then iterates entry points.
- `list_components()` returns `buildin` and `thirdparty` lists and skips broken entry points after logging a warning.

## Stage support

- Valid stage names are `default`, `train`, `predict`, and `cross_validation`.
- `load_component(name, stage)` selects a matching stage component by stage name.
- If a stage is unsupported, the runtime raises a `ValueError` that lists the supported stage names.
- `reader` and other default-stage components do not need a separate `train()` or `predict()` body.

## Guide points worth keeping in mind

- The developer guide treats components as scheduler entry points and keeps the computational logic in ML modules.
- If a component needs a different runtime I/O view per role or stage, inspect it with `artifact-type` rather than guessing from the merged descriptor.
- Components that use directory-based neural-network runners are not the same as the JSON-model learners; keep those artifact kinds distinct.
- If a new built-in component should be visible to `list`, add it to the lazy loader map and keep the name exact.
- If you are authoring a third-party component, make sure the entry-point distribution imports cleanly in a minimal environment before relying on discovery.
- If the component is meant to be consumed by the service-backed pipeline client, the developer guide also points to moving the descriptor into the FATE-Client component definition area and adding the matching pipeline component file there.

## When to use the CLI probes

- `desc` for the merged descriptor and parameter list.
- `artifact-type` for the stage/role-specific runtime I/O view.
- `task-schema` for task-config validation, not component discovery.
- `list` when you want to check whether a name exists before debugging a missing-component error.

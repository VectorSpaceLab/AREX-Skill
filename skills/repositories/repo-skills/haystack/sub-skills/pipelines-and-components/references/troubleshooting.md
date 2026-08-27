# Troubleshooting: Pipelines and Components

Use this guide to diagnose Haystack pipeline, component, serialization, async, loop, and SuperComponent failures.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'haystack'`
- `ImportError` for `Pipeline`, `AsyncPipeline`, `SuperComponent`, or `component`
- Installed package is the legacy `farm-haystack` package instead of modern `haystack-ai`

Fixes:

- Install the distribution named `haystack-ai` in the active Python environment.
- Use public imports: `from haystack import Pipeline, AsyncPipeline, SuperComponent, component`.
- Confirm the modern package version with:
  ```python
  import haystack
  print(haystack.__version__)
  ```
- Do not depend on source-checkout paths or repository-local modules in user code.

## Optional Dependency and Backend Failures

Pipeline orchestration itself is lightweight, but many components rely on optional integrations.

Symptoms:

- Import failures for provider components or document stores.
- Runtime errors from missing model SDKs, databases, or vector backends.
- Credential errors from generator, embedder, retriever, or service components.

Fixes:

- Keep this sub-skill focused on graph construction and sockets; route component selection and provider configuration to `../generation-and-model-components/SKILL.md` or `../retrieval-and-rag/SKILL.md`.
- Install the optional integration package required by the component being added.
- Use environment-variable-backed secrets for serializable provider components.
- Smoke-test the graph first with deterministic custom components before introducing external services.

## Component Contract Errors

Symptoms:

- `ComponentError` saying a class must have `run()`.
- `PipelineValidationError` saying an instance is not a component.
- Output socket missing during `connect()`.
- Errors about `run` and `run_async` signatures or output types not matching.

Fixes:

- Add `@component` above the class, not just above `run()`.
- Define `run(self, ...) -> dict[...]`.
- Add `@component.output_types(name=type)` to `run()` or call `component.set_output_types(self, name=type)` in `__init__`.
- Ensure returned dictionary keys match declared output names exactly.
- If `run_async()` exists, make it `async def` and keep the same parameters and output sockets as `run()`.
- Use `component.set_input_type()` only for components whose `run()` accepts `**kwargs`.

## Add Component Failures

Symptoms:

- Duplicate component name error.
- Name with `.` rejected.
- `_debug` rejected as reserved.
- Component already added to another pipeline.

Fixes:

- Choose stable unique names such as `query_embedder`, `retriever`, `prompt_builder`, `llm`.
- Avoid dots in component names because dots separate component and socket names.
- Instantiate a fresh component object for each pipeline; do not share one component instance across pipelines.
- If refactoring, call `remove_component(name)` before re-adding a replacement.

## Connection and Socket Validation Failures

Symptoms:

- `PipelineConnectError: no matching connections available`.
- `PipelineConnectError: more than one connection is possible`.
- `... does not have any output connections`.
- Sender or receiver socket name does not exist.
- Declared input and output types do not match.

Fixes:

1. Inspect sockets:
   ```python
   print(pipe.get_component("sender"))
   print(pipe.get_component("receiver"))
   print(pipe.inputs(include_components_with_connected_inputs=True))
   print(pipe.outputs(include_components_with_connected_outputs=True))
   ```
2. Use explicit paths: `pipe.connect("sender.output", "receiver.input")`.
3. Add missing `@component.output_types(...)` to sender components.
4. Rename `run()` parameters or update the connection to match actual receiver socket names.
5. Fix type annotations before disabling `connection_type_validation`.
6. For list receivers with multiple senders, remember sync ordering is alphabetical by sender component name, while async branch order is not guaranteed.

## Input Data and Runtime Validation Failures

Symptoms:

- `ValueError` for malformed `data`.
- Mandatory input missing.
- Pipeline appears blocked or produces no leaf output.
- A component returns a non-dictionary value or unsupported output type.

Fixes:

- Pass `data={"component_name": {"input_name": value}}` unless all input names are globally unique.
- Check `pipe.inputs()` for externally required inputs.
- Add defaults to optional `run()` parameters.
- Ensure every component returns `dict[str, Any]` keyed by output socket names.
- Use `include_outputs_from` to inspect intermediate builders, routers, validators, and joiners.
- Check for disconnected mandatory inputs after graph edits.

## Async Execution Failures

Symptoms:

- `RuntimeError: Cannot call run() from within an async context`.
- `TypeError` from `SuperComponent.run_async()` wrapping a sync `Pipeline`.
- Component `run_async` is not a coroutine.
- Non-deterministic output order from parallel branches.

Fixes:

- In async applications, call `await async_pipe.run_async(...)` or iterate `run_async_generator(...)`.
- Use `AsyncPipeline.run()` only from synchronous code.
- Wrap an `AsyncPipeline` if the `SuperComponent` must support `run_async()`.
- Declare `async def run_async(...)`, not a synchronous function.
- Do not rely on branch ordering in async variadic sockets; sort downstream if order matters.

## Loop and Max Run Failures

Symptoms:

- `PipelineMaxComponentRuns`.
- Loop never reaches an exit route.
- Intermediate loop state is missing from final results.

Fixes:

- Lower `max_runs_per_component` while developing and raise it only after proving termination.
- Inspect router and validator outputs with `include_outputs_from={"router", "validator"}`.
- Add a `Breakpoint(component_name="...", visit_count=...)` at the loop component to inspect a specific iteration.
- Confirm the loop has an exit branch that stops sending data back.
- Confirm initial inputs are not repeatedly re-consumed in a way that retriggers the loop forever.

## Serialization and Deserialization Failures

Symptoms:

- `DeserializationError` while loading YAML.
- `PipelineError` saying a component type is not imported or not in the registry.
- Secret/token serialization error.
- Loaded pipeline differs from the original.

Fixes:

- Ensure custom component classes are importable from their module path before calling `Pipeline.loads()` or `Pipeline.load()`.
- Implement `to_dict()` and `from_dict()` for components with non-trivial constructor state.
- Use `Pipeline.from_dict(data, components={"name": existing_instance})` when a component cannot or should not be reconstructed automatically.
- Store credentials with environment-variable-backed secrets rather than raw tokens.
- Compare `pipe.to_dict()`, `pipe.inputs()`, and deterministic run outputs before and after loading.

## Breakpoint and Snapshot Issues

Symptoms:

- Breakpoint never triggers.
- Snapshot file is not written.
- Resuming from snapshot raises invalid snapshot errors.

Fixes:

- Verify the breakpoint `component_name` is on the actual execution path.
- Remember `visit_count=0` means the first visit.
- Use `snapshot_callback` for deterministic in-memory handling.
- File saving requires `HAYSTACK_PIPELINE_SNAPSHOT_SAVE_ENABLED=true` and a writable snapshot path.
- Do not pass both `break_point` and `pipeline_snapshot` to `Pipeline.run()`.
- Resume against the same pipeline graph; snapshots are validated against component names and graph state.

## SuperComponent Mapping Failures

Symptoms:

- Invalid mapping type or value errors.
- Public wrapper input/output names are not what you expected.
- Async wrapper fails.

Fixes:

- Use `input_mapping={"public_input": ["component.input", "other.input"]}`.
- Use `output_mapping={"component.output": "public_output"}`.
- Include non-leaf internal outputs explicitly in `output_mapping` when needed.
- Print `repr(wrapper)` to inspect wrapper sockets.
- Use an `AsyncPipeline` for `await wrapper.run_async(...)`.

## Drawing Failures

Symptoms:

- `PipelineDrawingError` outside notebooks from `show()`.
- Network or timeout errors from Mermaid rendering.
- SuperComponent internals hidden in diagrams.

Fixes:

- Use `pipe.draw(path=Path("pipeline.png"))` outside notebooks.
- Use `pipe.show()` only in Jupyter.
- Provide a reachable `server_url` or retry with a longer `timeout`.
- Pass `super_component_expansion=True` to draw wrapped internal pipelines.

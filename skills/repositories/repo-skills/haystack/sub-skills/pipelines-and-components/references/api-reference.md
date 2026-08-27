# API Reference: Pipelines and Components

This reference covers Haystack public orchestration APIs exposed by `haystack-ai` 2.31.0rc0.

## Imports

```python
from haystack import AsyncPipeline, Pipeline, SuperComponent, component
from haystack.core.errors import (
    BreakpointException,
    PipelineConnectError,
    PipelineError,
    PipelineMaxComponentRuns,
    PipelineRuntimeError,
    PipelineValidationError,
)
from haystack.core.pipeline.breakpoint import load_pipeline_snapshot
from haystack.dataclasses.breakpoints import Breakpoint, PipelineSnapshot
```

`Pipeline`, `AsyncPipeline`, `SuperComponent`, and `component` are public root exports. Component-specific integrations may require optional packages or credentials; route those decisions to the relevant sibling skill.

## Pipeline Constructors

```python
Pipeline(metadata=None, max_runs_per_component=100, connection_type_validation=True)
AsyncPipeline(metadata=None, max_runs_per_component=100, connection_type_validation=True)
```

- `metadata`: serializable dictionary carried with the pipeline.
- `max_runs_per_component`: per-component safety limit; loops raise `PipelineMaxComponentRuns` after the limit is exceeded.
- `connection_type_validation`: validates sender/receiver socket types during `connect()`. Keep `True` unless migrating an old graph deliberately.

## Custom Component Contract

A custom component must be decorated with `@component` and define `run()`. Inputs come from the `run()` signature. Outputs must be declared with `@component.output_types(...)` or with `component.set_output_types(self, ...)` during initialization.

```python
from haystack import component

@component
class AddPrefix:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    @component.output_types(text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"text": f"{self.prefix}{text}"}
```

Key rules:

- `run()` must return a dictionary whose keys match declared output socket names.
- Typed `run()` parameters become input sockets; parameters with defaults become optional sockets.
- If `run()` uses `**kwargs`, declare dynamic inputs with `component.set_input_type(self, name="field", type=str)` or `component.set_input_types(self, field=str)`.
- `component.set_input_type()` and `component.set_input_types()` require `run(..., **kwargs)`; they cannot override fixed `run()` parameters.
- `component.set_output_types()` cannot be combined with `@component.output_types` on `run()` or `run_async()`.
- If a component defines `run_async()`, it must be `async def`, and its parameters and output types must match `run()` exactly.
- Components are registered by qualified class path for deserialization. Custom components must be importable before `Pipeline.loads()` or `Pipeline.from_dict()` can recreate them.

## Adding and Connecting Components

```python
pipe = Pipeline()
pipe.add_component("prefixer", AddPrefix("Q: "))
pipe.add_component("consumer", SomeConsumer())
pipe.connect("prefixer.text", "consumer.text")
```

`add_component(name, instance)` rules:

- `name` must be unique, cannot be `_debug`, and cannot contain `.`.
- `instance` must be a decorated Haystack component.
- A component instance cannot be shared across multiple pipelines; instantiate a fresh component for each graph.

`connect(sender, receiver)` rules:

- Use `"component"` when there is only one compatible socket pair.
- Use `"component.socket"` when a component has multiple inputs/outputs or when ambiguity appears.
- Haystack validates component existence, socket existence, and type compatibility by default.
- Connecting a component to itself is unsupported.
- Multiple senders connected to the same list-typed receiver are promoted to a lazy variadic socket. In sync `Pipeline`, resulting lists are ordered alphabetically by sender component name; in `AsyncPipeline`, branch completion order is not guaranteed.

Useful graph introspection:

```python
pipe.inputs()
pipe.inputs(include_components_with_connected_inputs=True)
pipe.outputs()
pipe.outputs(include_components_with_connected_outputs=True)
pipe.get_component("prefixer")
pipe.get_component_name(instance)
list(pipe.walk())
```

## Running Sync Pipelines

```python
result = pipe.run(
    data={"prefixer": {"text": "hello"}},
    include_outputs_from={"prefixer"},
)
```

`Pipeline.run(data, include_outputs_from=None, *, break_point=None, pipeline_snapshot=None, snapshot_callback=None)`:

- `data` is normally `{component_name: {input_name: value}}`.
- If input names are unique across the pipeline, shorthand `{input_name: value}` is also accepted.
- By default the result contains only leaf component outputs.
- `include_outputs_from={"component_name"}` adds the last output from those intermediate components.
- `break_point` and `pipeline_snapshot` cannot be passed together.
- Components are warmed up before execution.

## Running Async Pipelines

`AsyncPipeline` can run independent branches concurrently. It provides:

```python
await async_pipe.run_async(data, include_outputs_from=None, concurrency_limit=4)
async for partial in async_pipe.run_async_generator(data, include_outputs_from={"x"}, concurrency_limit=4):
    ...
async_pipe.run(data, include_outputs_from=None, concurrency_limit=4)
```

Guidance:

- Use `await run_async(...)` inside async code.
- Use `run_async_generator(...)` when you need partial outputs as components finish.
- The synchronous `AsyncPipeline.run()` wraps async execution, but raises `RuntimeError` if called from an already-running event loop; call `await run_async(...)` there.
- Keep `run()` and `run_async()` component signatures identical when a custom component supports both.

## Loops and Max Runs

Cycles are allowed when the graph and component readiness rules can eventually terminate. Use a low `max_runs_per_component` while prototyping feedback loops.

```python
pipe = Pipeline(max_runs_per_component=3)
```

Runtime behavior:

- A component may run multiple times in one pipeline invocation.
- Only the last output is kept in final results unless captured with `include_outputs_from`.
- Breakpoint `visit_count` is zero-based: `0` is the first visit, `1` the second.
- Non-terminating loops raise `PipelineMaxComponentRuns` instead of running indefinitely.

## Serialization

```python
yaml_text = pipe.dumps()
loaded = Pipeline.loads(yaml_text)
assert loaded == pipe

with open("pipeline.yml", "w", encoding="utf-8") as file:
    pipe.dump(file)
with open("pipeline.yml", encoding="utf-8") as file:
    loaded = Pipeline.load(file)
```

Available forms:

- `to_dict()` / `from_dict(data, callbacks=None, components={...})`
- `dumps(marshaller=YamlMarshaller)` / `loads(data, marshaller=YamlMarshaller, callbacks=None)`
- `dump(fp, marshaller=YamlMarshaller)` / `load(fp, marshaller=YamlMarshaller, callbacks=None)`

Deserialization notes:

- Component data must include a registered import path in `type`.
- Haystack imports modules when possible before looking up component classes in the registry.
- Use `components={"name": existing_instance}` to reuse already-created instances when loading.
- Secret token values should not be serialized. Prefer environment-variable-backed `Secret` objects for provider components.

## Drawing and Notebook Display

```python
from pathlib import Path
pipe.draw(path=Path("pipeline.png"), super_component_expansion=True)
pipe.show(super_component_expansion=True)  # Jupyter only
```

- `draw()` saves an image locally using a Mermaid server.
- `show()` is notebook-only; use `draw()` outside notebooks.
- `super_component_expansion=True` expands wrapped internal pipelines in the diagram.
- Drawing may require network access to a Mermaid server unless you supply an internal `server_url`.

## Breakpoints and Snapshots

```python
from haystack.core.errors import BreakpointException
from haystack.dataclasses.breakpoints import Breakpoint

break_point = Breakpoint(component_name="validator", visit_count=0)
try:
    pipe.run(data=input_data, break_point=break_point, include_outputs_from={"builder"})
except BreakpointException as error:
    snapshot = error.pipeline_snapshot
    partial_results = error.results
```

Snapshot behavior:

- A `Breakpoint` pauses before the named component at the requested visit count.
- `snapshot_callback(snapshot)` can capture snapshots without relying on file output.
- Snapshot file saving is disabled by default; set `HAYSTACK_PIPELINE_SNAPSHOT_SAVE_ENABLED=true` only when file snapshots are desired.
- Resume with `pipe.run(data={}, pipeline_snapshot=snapshot)` or `load_pipeline_snapshot(path)` followed by `pipeline_snapshot=snapshot`.
- On `PipelineRuntimeError`, inspect `error.pipeline_snapshot` to recover the last valid state.

## SuperComponent

`SuperComponent` wraps a `Pipeline` or `AsyncPipeline` so it can be inserted as a single component in a larger graph.

```python
from haystack import Pipeline, SuperComponent

inner = Pipeline()
inner.add_component("prefix", AddPrefix("Q: "))

wrapped = SuperComponent(
    pipeline=inner,
    input_mapping={"question": ["prefix.text"]},
    output_mapping={"prefix.text": "prompt"},
)
result = wrapped.run(question="hello")
assert result["prompt"] == "Q: hello"
```

Mapping rules:

- `input_mapping` maps public wrapper input names to internal `component.socket` paths.
- `output_mapping` maps internal `component.socket` paths to public wrapper output names.
- If mappings are omitted, Haystack derives them from disconnected pipeline inputs and leaf outputs.
- Mapping validation checks component names, socket names, and type compatibility.
- `SuperComponent.run_async()` requires the wrapped pipeline to be an `AsyncPipeline`; otherwise it raises `TypeError`.

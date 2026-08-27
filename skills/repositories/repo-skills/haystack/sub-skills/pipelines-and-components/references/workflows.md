# Workflows: Pipelines and Components

Use these recipes to complete common Haystack orchestration tasks without reopening the source repository.

## Create a Minimal Custom Component

1. Import from the public root API.
2. Decorate the class with `@component`.
3. Put input sockets in the `run()` signature.
4. Declare output sockets with `@component.output_types`.
5. Return a dictionary keyed by output socket names.

```python
from haystack import component

@component
class NormalizeText:
    @component.output_types(text=str)
    def run(self, text: str, lowercase: bool = True) -> dict[str, str]:
        normalized = " ".join(text.split())
        if lowercase:
            normalized = normalized.lower()
        return {"text": normalized}
```

Validation checklist:

- Instantiate the component and inspect `repr(instance)` to see input/output sockets.
- Add it to a one-node `Pipeline` and run a known input.
- If the class needs serialization, implement `to_dict()` and `from_dict()` or ensure constructor parameters are serializable by Haystack defaults.

## Wire a Pipeline Safely

```python
from haystack import Pipeline

pipe = Pipeline(metadata={"purpose": "normalization"}, max_runs_per_component=5)
pipe.add_component("normalize", NormalizeText())
pipe.add_component("prefix", AddPrefix("clean: "))
pipe.connect("normalize.text", "prefix.text")

print(pipe.inputs())
print(pipe.outputs())
result = pipe.run({"normalize": {"text": "  Hello   Haystack  "}}, include_outputs_from={"normalize"})
```

Use explicit socket paths when:

- Either side has more than one socket.
- `PipelineConnectError` says multiple connections are possible.
- You want future readers to see which field is being routed.

Use `pipe.inputs(include_components_with_connected_inputs=True)` and `pipe.outputs(include_components_with_connected_outputs=True)` when auditing the full graph, not just externally visible sockets.

## Repair Mismatched Socket Names

When `connect()` fails:

1. Print component sockets:
   ```python
   print(pipe.get_component("producer"))
   print(pipe.get_component("consumer"))
   print(pipe.inputs(include_components_with_connected_inputs=True))
   print(pipe.outputs(include_components_with_connected_outputs=True))
   ```
2. Confirm that producer output keys match `@component.output_types`.
3. Confirm that consumer input names match `run()` parameters or `component.set_input_type()` names.
4. Reconnect with explicit paths: `pipe.connect("producer.output_name", "consumer.input_name")`.
5. If types differ, fix annotations or set `connection_type_validation=False` only as a temporary migration step.

Common fixes:

- Missing output socket: add `@component.output_types(...)` to `run()`.
- Wrong input name: change the `run()` parameter or use the actual `component.socket` in `connect()`.
- Ambiguous sockets: specify both socket names.
- Optional runtime parameter not exposed: add a default value in `run()` or declare it dynamically for `**kwargs` components.

## Run and Inspect Intermediate Outputs

```python
result = pipe.run(
    {"normalize": {"text": "Hello"}},
    include_outputs_from={"normalize", "prefix"},
)
print(result["normalize"])
print(result["prefix"])
```

Notes:

- Without `include_outputs_from`, final output contains leaf components only.
- In loops, the included output is the last output from the component.
- Include intermediate builders, routers, validators, or joiners when diagnosing blocked graphs.

## Convert a Sync Pipeline to Async

1. Replace `Pipeline()` with `AsyncPipeline()`.
2. Ensure custom components either work with sync `run()` or define matching async `run_async()` signatures.
3. Replace sync execution in async applications with `await pipe.run_async(...)`.
4. Set `concurrency_limit` according to backend limits.
5. Keep `max_runs_per_component` explicit for loops.
6. Re-test serialization with `dumps()` / `loads()` after conversion.

```python
from haystack import AsyncPipeline

async_pipe = AsyncPipeline(max_runs_per_component=5)
async_pipe.add_component("normalize", NormalizeText())
async_pipe.add_component("prefix", AddPrefix("clean: "))
async_pipe.connect("normalize.text", "prefix.text")

result = await async_pipe.run_async(
    {"normalize": {"text": "  Hello   Haystack  "}},
    include_outputs_from={"normalize"},
    concurrency_limit=4,
)
```

Use `run_async_generator()` to stream partial outputs from completed components:

```python
async for partial in async_pipe.run_async_generator(data, include_outputs_from={"normalize"}):
    print(partial)
```

Avoid calling `async_pipe.run()` from within an existing event loop; it raises `RuntimeError` and tells you to use `await pipeline.run_async(...)`.

## Build a Loop with Safety Limits

Loop design checklist:

- The loop must have a route that eventually stops feeding data back.
- Use `Pipeline(max_runs_per_component=3)` or another low bound while prototyping.
- Capture router/validator outputs with `include_outputs_from`.
- Use breakpoints with `visit_count` to inspect a specific iteration.

```python
from haystack.dataclasses.breakpoints import Breakpoint

break_point = Breakpoint(component_name="validator", visit_count=1)
try:
    pipe.run(data, include_outputs_from={"validator"}, break_point=break_point)
except BreakpointException as error:
    print(error.inputs)
    print(error.results)
```

If a loop hits `PipelineMaxComponentRuns`, inspect whether the router emits the exit output, whether the joiner consumes the initial input correctly, and whether connected sockets remain mandatory after loopback wiring.

## Serialize, Load, and Compare Pipelines

```python
yaml_text = pipe.dumps()
loaded = Pipeline.loads(yaml_text)
assert loaded == pipe
assert loaded.run(data) == pipe.run(data)
```

For files:

```python
with open("pipeline.yml", "w", encoding="utf-8") as file:
    pipe.dump(file)
with open("pipeline.yml", encoding="utf-8") as file:
    loaded = Pipeline.load(file)
```

Serialization checklist:

- Custom component class is importable from its qualified module path.
- Constructor parameters are serializable or custom `to_dict()` / `from_dict()` handle them.
- Secrets use environment-variable references, not raw tokens.
- The deserialized pipeline still has the same `inputs()`, `outputs()`, and run result on deterministic test data.

## Debug with Breakpoints and Snapshots

For deliberate pauses:

```python
from haystack.core.errors import BreakpointException
from haystack.dataclasses.breakpoints import Breakpoint

break_point = Breakpoint(component_name="prefix", visit_count=0)
try:
    pipe.run(data, break_point=break_point, include_outputs_from={"normalize"})
except BreakpointException as error:
    snapshot = error.pipeline_snapshot
    print(error.component)
    print(error.inputs)
    print(error.results)
```

For runtime failures:

```python
from haystack.core.errors import PipelineRuntimeError

try:
    pipe.run(data)
except PipelineRuntimeError as error:
    if error.pipeline_snapshot is not None:
        print(error.pipeline_snapshot.pipeline_state.pipeline_outputs)
```

To resume:

```python
result = pipe.run(data={}, pipeline_snapshot=snapshot)
```

Use `snapshot_callback(snapshot)` to store snapshots in memory, a test fixture, a database, or structured logs. File snapshot saving is opt-in through `HAYSTACK_PIPELINE_SNAPSHOT_SAVE_ENABLED=true`.

## Wrap a Pipeline as a SuperComponent

Use `SuperComponent` when a working subgraph should appear as one component in a larger pipeline.

```python
from haystack import Pipeline, SuperComponent

inner = Pipeline()
inner.add_component("normalize", NormalizeText())
inner.add_component("prefix", AddPrefix("clean: "))
inner.connect("normalize.text", "prefix.text")

wrapper = SuperComponent(
    pipeline=inner,
    input_mapping={"raw_text": ["normalize.text"]},
    output_mapping={"prefix.text": "clean_text"},
)

outer = Pipeline()
outer.add_component("cleaner", wrapper)
print(outer.run({"cleaner": {"raw_text": "  Hello  "}}))
```

Mapping guidance:

- Use explicit `input_mapping` when one public input should feed multiple internal inputs.
- Use explicit `output_mapping` when you need outputs from non-leaf internal components.
- Validate the wrapper with `wrapper.__haystack_input__` and `wrapper.__haystack_output__` via `repr(wrapper)`.
- For async wrappers, wrap an `AsyncPipeline` and call `await wrapper.run_async(...)`.

## Draw a Pipeline

```python
from pathlib import Path
pipe.draw(path=Path("pipeline.png"), super_component_expansion=True)
```

If drawing fails, confirm network access to the Mermaid server or provide a reachable `server_url`. In notebooks, `pipe.show()` displays directly, but outside notebooks use `pipe.draw()`.

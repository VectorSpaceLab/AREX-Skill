# DataFlow pipeline foundations API reference

This reference is for `open-dataflow` 1.0.x with import package `dataflow`. It names public package APIs only; generated workflows should not depend on any source checkout, private environment, or test artifact.

## Core imports

```python
from dataflow.pipeline import PipelineABC, BatchedPipelineABC, StreamBatchedPipelineABC
from dataflow.core.operator import OperatorABC
from dataflow.core.prompt import PromptABC, DIYPromptABC, prompt_restrict
from dataflow.utils.storage import (
    FileStorage,
    LazyFileStorage,
    DummyStorage,
    BatchedFileStorage,
    StreamBatchedFileStorage,
    MyScaleDBStorage,
)
from dataflow.wrapper import BatchWrapper
```

## Pipeline classes

| Class | Use when | Key public calls |
| --- | --- | --- |
| `PipelineABC` | Ordinary step-by-step pipeline where each operator consumes the previous step cache and writes a new cache. | `compile()`, then compiled `forward(resume_step=0)`, and `draw_graph(port=0, hide_no_changed_keys=True)`. |
| `BatchedPipelineABC` | The data file should be sliced into batches while still using file-backed step caches. | `compile()`, then `forward(resume_step=0, batch_size=None, resume_from_last=True)`. |
| `StreamBatchedPipelineABC` | Large JSONL/CSV-style inputs should be streamed in chunks instead of fully materialized for each batch. | Same compiled `forward` signature as `BatchedPipelineABC`; requires `StreamBatchedFileStorage` for intended streaming behavior. |

`compile()` replaces operator attributes with an internal recorder, calls the user-defined `forward()` once, builds an operator/key graph, validates input keys against source and prior output keys, and then replaces `forward` with the compiled executor. A task should normally call `compile()` exactly once after constructing the pipeline and before the first real run.

## Operator contract

A custom DataFlow operator subclasses `OperatorABC` and implements `run`.

Recommended signature shape:

```python
class MyOperator(OperatorABC):
    def run(self, storage, input_text, output_result):
        dataframe = storage.read(output_type="dataframe")
        dataframe[output_result] = dataframe[input_text].astype(str)
        return storage.write(dataframe)
```

Rules that matter for compile and registry compatibility:

- `storage` should be the first logical parameter after `self`.
- Column-consuming parameters should be named `input_*` and receive string column names.
- Column-producing parameters should be named `output_*` and receive string column names.
- Other runtime parameters do not participate in key validation and may produce warnings when captured into an operator node, so prefer constructor parameters for fixed configuration.
- The operator should read from the provided stepped storage object and write the full updated record set back through that same storage object.
- Return values are not used by the compiled pipeline for data movement; `storage.write(...)` is the data handoff.

## Compile-time key validation

During compile, DataFlow reads the first storage's step-0 columns and accumulates keys operator by operator:

1. Initial keys come from `storage.get_keys_from_dataframe()` on the first operator's storage.
2. Every `input_*="name"` must already be in the accumulated keys.
3. Every `output_*="name"` is added to later accumulated keys.
4. If any input key is missing, compile raises `KeyError` with the operator attribute name, class name, missing key, and parameter name.

Typical recovery path:

1. Validate the input file columns with `scripts/validate_tabular_input.py`.
2. Check every `input_*` value in pipeline `forward()` for spelling and casing.
3. Confirm the earlier operator's `output_*` value exactly matches the later operator's `input_*` value.
4. Re-run `compile()` before trying the real `forward()`.

## Prompt APIs

`PromptABC` and `DIYPromptABC` are the base classes for prompt templates. `prompt_restrict(...)` is a class decorator for operators or helper classes with a `prompt_template` constructor parameter.

```python
class BuiltInPrompt(PromptABC):
    def build_prompt(self):
        return "Summarize the input."

class CustomPrompt(DIYPromptABC):
    def build_prompt(self):
        return "Custom prompt."

@prompt_restrict(BuiltInPrompt)
class PromptedOp:
    def __init__(self, prompt_template=None):
        self.prompt_template = prompt_template
```

Allowed values are:

- `None`.
- Instances of the prompt classes passed to `prompt_restrict`.
- Instances of any `DIYPromptABC` subclass.

A non-whitelisted `PromptABC` subclass or unrelated object raises `TypeError` and lists accepted classes plus `DIYPromptABC`.

## `draw_graph`

After compile, call:

```python
pipeline.draw_graph(port=0, hide_no_changed_keys=True)
```

Behavior:

- Requires `pyvis`; missing dependency raises an import error that recommends installing `pyvis`.
- Creates a temporary `.pyvis` HTML graph and starts a local HTTP server.
- `port=0` chooses a free port.
- `hide_no_changed_keys=True` hides direct unchanged keys from dataset input to dataset output.
- The call blocks while serving the graph; it is not a CI smoke check.

## Wrappers

`BatchWrapper(operator, batch_size=32, batch_cache=False)` wraps one operator for manual full-dataframe batching. It reads the whole storage input, slices batches, runs the inner operator against an in-memory dummy storage, merges new columns back, and writes the full result to the original storage. Use it only for local batching of a single operator. For pipeline-level batch/resume behavior, prefer `BatchedPipelineABC` or `StreamBatchedPipelineABC`.

`DummyStorage` is intended as in-memory storage for wrapper internals and ad-hoc tests, but `open-dataflow` 1.0.10 exposes it with an abstract `get_keys_from_dataframe` method. If direct `DummyStorage()` instantiation raises `TypeError`, use `FileStorage` for smoke tests or define a tiny local `DataFlowStorage` subclass in the application code.

# Pipeline implementation patterns

Use these patterns to build DataFlow foundations without API keys, model downloads, or a source checkout.

## Minimal custom operator pipeline

```python
from dataflow.core.operator import OperatorABC
from dataflow.pipeline import PipelineABC
from dataflow.utils.storage import FileStorage

class AddLength(OperatorABC):
    def run(self, storage, input_text, output_length):
        dataframe = storage.read(output_type="dataframe")
        dataframe[output_length] = dataframe[input_text].astype(str).str.len()
        return storage.write(dataframe)

class TinyPipeline(PipelineABC):
    def __init__(self, input_path, cache_path="cache"):
        super().__init__()
        self.storage = FileStorage(
            first_entry_file_name=input_path,
            cache_path=cache_path,
            file_name_prefix="tiny",
            cache_type="jsonl",
        )
        self.add_length = AddLength()

    def forward(self):
        self.add_length.run(
            storage=self.storage.step(),
            input_text="text",
            output_length="text_length",
        )

pipeline = TinyPipeline("records.jsonl")
pipeline.compile()
pipeline.forward()
```

Run `scripts/smoke_pipeline_foundations.py` for a complete executable version that creates the fixture, runs two custom operators, checks output values, and can demonstrate a compile-time missing-key failure.

## Compile and run sequence

1. Construct the pipeline object.
2. Call `compile()`.
3. If compile raises `KeyError`, fix column names before any real run.
4. Call the compiled `forward()`.
5. Inspect cache files or read the final step with a new `FileStorage` object.

Do not call an operator directly from the pipeline object after compile; the operator attributes have been wrapped for the compiled runtime.

## Input and output key naming

Good:

```python
self.cleaner.run(storage=self.storage.step(), input_text="raw_text", output_text="clean_text")
self.scorer.run(storage=self.storage.step(), input_text="clean_text", output_score="quality")
```

Bad:

```python
self.cleaner.run(storage=self.storage.step(), text="raw_text", output="clean_text")
self.scorer.run(storage=self.storage.step(), input_text="cleaned_text", output_score="quality")
```

The bad example hides keys from the graph because `text` does not start with `input_`, and the second operator asks for `cleaned_text` even though the first operator wrote `clean_text`.

## Multi-step cache semantics

For an input file with columns `id,text` and two operators:

```text
step 0: input file columns            id,text
step 1: after first operator cache    id,text,text_length
step 2: after second operator cache   id,text,text_length,is_long
```

Each operator should write the full dataframe or full record list, not only the new column. Later operators read the entire previous step.

## Resume patterns

### Ordinary pipelines

`PipelineABC.forward(resume_step=0)` skips compiled operator nodes where the zero-based operator step is lower than `resume_step`.

### Batched pipelines

`BatchedPipelineABC.forward(resume_step=0, batch_size=None, resume_from_last=True)` adds batch controls:

- `batch_size=None` runs each operator once.
- `batch_size=N` slices the input dataframe into batches of size `N`.
- `resume_from_last=True` reads and writes the last-success marker in the cache directory.
- Do not pass `resume_step > 0` together with `resume_from_last=True`.

Use `BatchedFileStorage` with `BatchedPipelineABC` for intended behavior.

### Stream-batched pipelines

`StreamBatchedPipelineABC.forward(...)` has the same signature but obtains chunks from `StreamBatchedFileStorage.iter_chunks()`. Use it for large local JSONL/CSV inputs when chunked reads are more important than repeatedly loading the full file.

## Wrapper batching pattern

For a single expensive operator, `BatchWrapper(op, batch_size=32, batch_cache=False)` can be used outside a compiled batched pipeline:

```python
wrapped = BatchWrapper(op, batch_size=16, batch_cache=True)
wrapped.run(storage=storage.step(), input_text="text", output_text="result")
```

This wrapper reads the whole input dataframe, splits it into batches, runs the underlying operator on each batch through dummy storage, merges any new columns, and writes the complete result once. If `DummyStorage()` raises an abstract-class error in the installed version, avoid `BatchWrapper` for final smoke checks and use `BatchedPipelineABC` or explicit `FileStorage`-backed batches.

## Graph visualization pattern

Use graph rendering for interactive debugging after compile:

```python
pipeline.compile()
pipeline.draw_graph(port=0, hide_no_changed_keys=True)
```

This starts a local HTTP server and blocks until interrupted. It is best for a developer terminal, not a non-interactive CI job. Missing `pyvis` is a dependency issue, not a pipeline graph issue.

## Non-LLM smoke pattern

A high-signal foundation smoke should:

1. Create a tiny local JSONL file.
2. Define one or two `OperatorABC` classes with deterministic dataframe operations.
3. Use `FileStorage` only.
4. Call `compile()` and prove compile-time keys are valid.
5. Call `forward()` and assert the final cache columns and values.
6. Optionally run the same pipeline with an intentional input-key typo and assert that `compile()` raises `KeyError`.

This proves pipeline wrapping, key matching, storage stepping, cache filenames, and dataframe handoff without relying on serving, CLI, network, GPU, or original examples.

# Workflows

## 1. Replace one operator
1. Keep the operator implementation unchanged.
2. Wrap the class with `RayAcceleratedOperator(...).op_cls_init(...)`.
3. Pass the wrapper into the pipeline instead of the serial operator.
4. Keep the same `storage.step()` and `run(...)` call.

```python
self.stage = RayAcceleratedOperator(
    MyRowOp,
    replicas=4,
    num_gpus_per_replica=0.0,
).op_cls_init(model_name="...")

self.stage.run(
    storage=self.storage.step(),
    input_key="text",
    output_key="score",
)
```

## 2. Normal pipeline
The wrapper stays in the same place as a normal `OperatorABC`.
Only the execution backend changes; the pipeline shape, storage choice, and output keys do not.

```python
class MyPipeline(PipelineABC):
    def __init__(self, input_file, cache_path):
        super().__init__()
        self.storage = FileStorage(
            first_entry_file_name=input_file,
            cache_path=cache_path,
            file_name_prefix="step",
            cache_type="jsonl",
        )
        self.stage = RayAcceleratedOperator(
            MyRowOp,
            replicas=4,
            num_gpus_per_replica=0.0,
        ).op_cls_init(model_name="...")

    def forward(self):
        self.stage.run(
            storage=self.storage.step(),
            input_key="text",
            output_key="score",
        )
```

If you compile this pipeline, the compiled runner will bind the wrapped operator's named inputs and auto-shutdown Ray actors after each stage.

## 3. Batched pipeline
Use the same wrapper call inside `forward`. The pipeline owns batching and resume behavior; the wrapper only accelerates each batch.

```python
class MyBatched(BatchedPipelineABC):
    def __init__(self, input_file, cache_path):
        super().__init__()
        self.storage = BatchedFileStorage(
            first_entry_file_name=input_file,
            cache_path=cache_path,
            file_name_prefix="step",
            cache_type="jsonl",
        )
        self.stage = RayAcceleratedOperator(
            MyRowOp,
            replicas=4,
            num_gpus_per_replica=0.0,
        ).op_cls_init(model_name="...")

    def forward(self):
        self.stage.run(
            storage=self.storage.step(),
            input_key="text",
            output_key="score",
        )
```

Use `pipe.compile(); pipe.forward(batch_size=64, resume_from_last=False)` when you want the compiled path.

## 4. Stream-batched pipeline
The same rule applies when the storage streams chunks instead of materializing the full frame. Keep the wrapper call unchanged and let the stream storage control chunk order.

```python
class MyStream(StreamBatchedPipelineABC):
    def __init__(self, input_file, cache_path):
        super().__init__()
        self.storage = StreamBatchedFileStorage(
            first_entry_file_name=input_file,
            cache_path=cache_path,
            file_name_prefix="step",
            cache_type="jsonl",
        )
        self.stage = RayAcceleratedOperator(
            MyRowOp,
            replicas=4,
            num_gpus_per_replica=0.0,
        ).op_cls_init(model_name="...")

    def forward(self):
        self.stage.run(
            storage=self.storage.step(),
            input_key="text",
            output_key="score",
        )
```

## 5. Resource choices
- CPU fallback: `num_gpus_per_replica=0.0`
- Shared GPU: `0.25`, `0.5`, or another explicit fraction
- Dedicated GPU: `1.0`
- More replicas: only when the wrapped operator is row-independent and deterministic

## 6. Cleanup pattern
- Manual scripts: call `shutdown()` once you are done with the Ray-backed operator.
- Compiled pipelines: the compiled runner already calls `shutdown()` after each Ray stage.
- If several Ray stages share one process and use GPUs, cleanup matters even if the actor is idle.

## 7. Determinism checklist
- One row should not depend on another row's output.
- The wrapped operator should not mutate shared global state.
- The output order should match the input order for contiguous shards.
- Any cross-row reduction or global ranking belongs outside this wrapper.

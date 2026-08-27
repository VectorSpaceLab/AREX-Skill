# EasyR1 core API troubleshooting

Use this guide when a low-level EasyR1 API fails before or during trainer execution. For full training launch errors, route to training-workflows. For model checkpoint conversion/export errors, route to checkpoint-export.

## Import and backend limitations

### Symptom

```text
ModuleNotFoundError: No module named 'verl'
ModuleNotFoundError: No module named 'tensordict'
ModuleNotFoundError: No module named 'ray'
```

### Fix

Install/import the EasyR1 package and its CPU API dependencies before running core API helpers. DataProto imports require TensorDict and Ray even for CPU smoke checks.

### Important limitation

A passing DataProto/API smoke does not prove full EasyR1 training is ready. End-to-end training additionally needs a CUDA-capable EasyR1 runtime with compatible PyTorch CUDA, flash-attn, vLLM, Ray workers, model weights, datasets, and enough GPU memory.

## DataProto construction errors

### Mismatched tensor leading dimensions

Typical error:

```text
AssertionError: Not all the tensor in tensors have the same batch size ...
```

Check every tensor's leading batch dimension:

```python
for name, tensor in tensors.items():
    print(name, tuple(tensor.shape))
```

Fix by padding/truncating/rebatching tensors so their leading dimension matches. If you use `num_batch_dims > 1`, every tensor must share those leading dimensions; non-tensor batches are only supported with `num_batch_dims=1`.

### Non-tensor length mismatch

Typical error:

```text
AssertionError: key sample_id length 3 is not equal to bsz 4.
```

Make each `non_tensor_batch` array length equal to the tensor batch size. Convert ragged or string metadata to object arrays if you build the arrays manually:

```python
non_tensors = {"sample_id": np.array(sample_ids, dtype=object)}
```

### Unsupported value type in `from_single_dict`

`DataProto.from_single_dict` accepts only `torch.Tensor` and `numpy.ndarray` values. Wrap Python lists for metadata as object arrays or use `from_dict(non_tensors=...)`.

## `DataProto.union` conflicts

### Symptom

```text
ValueError: Key already exists: input_ids.
ValueError: Key already exists: sample_id.
AssertionError: <key> in dict1 and dict2 are not the same object
```

### Cause

`union` merges tensor keys, non-tensor keys, and `meta_info` keys. Existing keys are allowed only when the values are identical. Different values with the same key are treated as ambiguous data corruption.

### Fix pattern

1. Decide which namespace owns the key.
2. Select disjoint keys before union, or rename one side.
3. Confirm both protos have the same batch length.

```python
left = proto_a.select(batch_keys=["input_ids"], non_tensor_batch_keys=["sample_id"], meta_info_keys=["source"])
right = proto_b.select(batch_keys=["attention_mask"], non_tensor_batch_keys=[], meta_info_keys=[])
left.union(right)
```

If the two tensors should be equal, assert equality before union so the failure is explicit:

```python
torch.testing.assert_close(proto_a.batch["input_ids"], proto_b.batch["input_ids"])
```

## Chunk, split, and padding failures

### Symptom

```text
AssertionError: only support equal chunk. Got size of DataProto 10 and chunk 4.
AssertionError: only support equal split. Got size of DataProto 10 and split 3.
```

### Fix

Use divisibility-preserving batch sizes, or pad first and unpad after downstream work:

```python
padded, pad_size = pad_dataproto_to_divisor(proto, size_divisor=4)
chunks = padded.chunk(4)
# ... process chunks ...
restored = unpad_dataproto(DataProto.concat(chunks), pad_size)
```

Remember that padding repeats rows from the beginning of the batch. Do not include padded rows in final metrics, reward summaries, or saved predictions.

## Repeat, reorder, and item indexing surprises

- `proto[0]` returns `DataProtoItem`, not `DataProto`. Use `proto[0:1]` for a batch of size one.
- `repeat(repeat_times, interleave=True)` gives row order `a,a,b,b`; `interleave=False` gives `a,b,a,b`. Choose the one that matches rollout grouping.
- `reorder(indices)` mutates the proto in-place. Clone or reconstruct first if the original order is still needed.
- `select(..., deepcopy=False)` may share nested metadata objects. Use `deepcopy=True` before mutating selected metadata.

## GRPO or RLOO grouped-rollout assertion

### Symptom

```text
AssertionError: GRPO needs rollout.n > 1.
AssertionError: RLOO needs rollout.n > 1.
```

### Cause

GRPO, GRPO Pass@k, and RLOO compute baselines within a group of responses for the same prompt. The `index` tensor passed to the advantage function must contain at least two rows for each group.

Bad example: every row has a unique index.

```python
index = torch.tensor([0, 1, 2, 3])
```

Good example: two responses per prompt.

```python
index = np.array([0, 0, 1, 1], dtype=np.int64)
```

### Fix

- In synthetic API checks, repeat each prompt index at least twice.
- When directly calling GRPO/RLOO helpers, prefer Python or NumPy scalar group IDs. If a `torch.Tensor` index still triggers the assertion despite repeated numeric values, convert it with `index.detach().cpu().numpy()` so dictionary grouping sees reusable scalar keys rather than distinct zero-dimensional tensor objects.
- In training configs, ensure the rollout setting generates more than one response per prompt when using grouped estimators.
- Preserve prompt/group IDs through dynamic batching and restore outputs before computing grouped advantages.

## Mask, log-prob, and loss shape mismatches

### Symptom

```text
RuntimeError: The size of tensor a ... must match the size of tensor b ...
NotImplementedError: Unknown KL penalty: ...
NotImplementedError: Unknown mode: ...
```

### Fix checklist

- `old_log_probs`, `log_probs`, `advantages`, token rewards, values, returns, and `response_mask` should normally share shape `(batch, response_length)`.
- Use floating tensors for log-probs, rewards, advantages, values, and returns.
- Use numeric or boolean masks with the same response shape. Avoid all-zero masks because masked means divide by `eps` and become uninformative.
- `compute_kl` supports only `kl`, `abs`, `mse`, `low_var_kl`, and `full`.
- `average_loss` and loss helpers support `loss_avg_mode="token"` or `"seq"`.
- `compute_policy_loss` supports `loss_type="default"`, `"gspo"`, `"gspo_token"`, `"cispo"`, and `"sapo"`.

For `log_probs_from_logits`, logits should have shape `(batch, seq, vocab)` and labels `(batch, seq)`. If flash-attn's cross-entropy kernel is not installed, EasyR1 falls back to PyTorch cross entropy for this helper.

## Dynamic sequence-length batching failures

### Missing `attention_mask`

`prepare_dynamic_batch` expects `data.batch["attention_mask"]`. Add the mask to the DataProto tensor batch before calling dynamic batching.

### `max_token_len` too small

Typical error:

```text
AssertionError: max_token_len must be greater than the sequence length.
```

`max_token_len` must be at least the padded sequence length, not merely the average number of valid tokens.

### Wrong output order after micro-batching

Always keep the `batch_idx_list` returned by `prepare_dynamic_batch`. Concatenate micro-batch outputs in the returned micro-batch order, then call:

```python
restored = restore_dynamic_batch(torch.cat(outputs, dim=0), batch_idx_list)
```

Do not sort or flatten `batch_idx_list` yourself unless you also update the inverse mapping.

### Grouped algorithms after dynamic batching

Dynamic batching reorders rows to balance valid token counts. If an algorithm later needs prompt grouping (`index` for GRPO/RLOO), either keep the group index as a tensor/non-tensor column through the same batching path or restore to original order before computing advantages.

### Distributed caveat

When PyTorch distributed is initialized, EasyR1's dynamic batching path performs a cross-rank max of the micro-batch count using CUDA tensors. If you initialized distributed for a CPU-only diagnostic, either avoid that path or use a runtime where CUDA is valid for the process group behavior being tested.

## DataProtoFuture issues

### Symptom

A deferred result cannot be indexed or selected, or code fails because it expected a `DataProto` but received `DataProtoFuture`.

### Fix

`DataProtoFuture` is a Ray handoff wrapper. Pass it through to the next worker method or call `future.get()` to collect and dispatch a real `DataProto`. Do not treat it as a normal proto on the driver.

## Logger/tracker setup errors

### Unsupported logger

```text
ValueError: <name> is not supported.
```

Use one of `console`, `file`, `mlflow`, `swanlab`, `tensorboard`, or `wandb`.

### Missing config keys

`FileLogger`, TensorBoard, WandB, SwanLab, and MLflow expect trainer metadata such as `trainer.project_name`, `trainer.experiment_name`, and/or `trainer.save_checkpoint_path`. Provide a minimal config:

```python
config = {
    "trainer": {
        "project_name": "debug-project",
        "experiment_name": "debug-run",
        "save_checkpoint_path": "checkpoints/debug-run",
    }
}
```

### Optional service dependencies

WandB, SwanLab, MLflow, and TensorBoard logging require their optional packages and may require credentials or offline-mode settings. Use `console` or `file` for deterministic local diagnostics.

## Checkpoint tracker debugging

### Latest checkpoint not found

`find_latest_ckpt(path)` returns `(None, None)` when the tracker file is missing, or `(None, tracker_info)` when the tracker points to a step directory that does not exist.

Check that:

- `checkpoint_tracker.json` exists under the save directory.
- It contains `last_global_step`.
- The matching `global_step_<step>` directory exists.

### Cleanup removed unexpected directories

`remove_obsolete_ckpt` keeps the current checkpoint outside its deletion set, preserves `best_global_step`, and retains the newest older checkpoints according to `save_limit`. Confirm `directory_format` matches your actual step directory names before cleanup.

Route actor shard conversion, Hugging Face export, and LoRA merge questions to checkpoint-export.

## Use the bundled smoke script

From this sub-skill directory, run:

```bash
python scripts/easyr1_dataproto_smoke.py --help
python scripts/easyr1_dataproto_smoke.py
```

If it fails, the printed stage usually narrows the issue to imports, DataProto operations, dynamic batching, or core algorithm tensors.

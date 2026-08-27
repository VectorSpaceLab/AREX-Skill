# EasyR1 core API reference

This reference distills the EasyR1 support APIs needed for debugging data movement, algorithm tensors, dynamic batching, and logging. It assumes the `verl` package is importable. The APIs below are CPU-safe unless they are explicitly described as distributed or CUDA-related; CPU success does not validate full Ray/vLLM/FSDP training.

## Runtime assumptions

- `verl` is the importable package name used by EasyR1.
- Core API smoke tests need PyTorch, NumPy, TensorDict, Ray, and the EasyR1 package. They do not need model downloads or training GPUs.
- Full EasyR1 training uses additional CUDA-oriented dependencies such as flash-attn and vLLM, plus Ray workers and model/dataset access. Treat DataProto/API verification as a narrow support-layer check only.

## DataProto mental model

`DataProto` is EasyR1's standard exchange object between rollout, reward, trainer, and worker components.

```python
from verl.protocol import DataProto

proto = DataProto.from_dict(
    tensors={"input_ids": input_ids, "attention_mask": attention_mask},
    non_tensors={"sample_id": ["a", "b"]},
    meta_info={"split": "debug"},
)
```

A `DataProto` contains three independent namespaces:

| Namespace | Type | Batch rule | Typical contents |
| --- | --- | --- | --- |
| `batch` | `tensordict.TensorDict` or `None` | every tensor has the same leading batch dimension | `input_ids`, `attention_mask`, `position_ids`, log-probs, rewards, masks |
| `non_tensor_batch` | `dict[str, numpy.ndarray]` | arrays are stored as object arrays and must have the same length as `batch` when tensors are present | prompt strings, UUIDs, raw metadata, paths or labels |
| `meta_info` | `dict[str, Any]` | not batched | tokenizer settings, generation metadata, debug flags |

Important construction rules:

- `DataProto.from_dict(tensors=None, non_tensors=None, meta_info=None, num_batch_dims=1)` validates that every tensor has the same first `num_batch_dims` dimensions.
- If `non_tensors` is provided, `num_batch_dims` must be `1` and each non-tensor array length must equal the tensor batch size.
- Non-tensor values are converted to `numpy.ndarray(dtype=object)` when needed.
- `DataProto.from_single_dict(data, meta_info=None)` splits `torch.Tensor` values into `batch` and `numpy.ndarray` values into `non_tensor_batch`; other value types are rejected.
- `DataProtoItem` is the single-row return object from integer indexing. It carries `batch`, `non_tensor_batch`, and `meta_info` for one item.

## DataProto indexing and mutation

| Operation | Behavior | Gotcha |
| --- | --- | --- |
| `len(proto)` | returns tensor batch size, or first non-tensor length if no tensors exist | empty proto length is `0` |
| `proto[i]` | returns `DataProtoItem` | not a `DataProto`; use slices/lists for batched output |
| `proto[start:stop:step]` | returns `DataProto` | preserves shared `meta_info` |
| `proto[[0, 2]]` / `proto[tensor_indices]` | returns `DataProto` | torch indices are moved through NumPy for non-tensors |
| `proto.select(batch_keys, non_tensor_batch_keys, meta_info_keys, deepcopy=False)` | returns a selected view/copy | missing keys are silently filtered out |
| `proto.pop(batch_keys, non_tensor_batch_keys=None, meta_info_keys=None)` | returns selected content and removes it from `proto` | mutates the original object |
| `proto.rename(old_keys, new_keys)` | renames only tensor batch keys | key counts must match; mutates the original object |
| `proto.to(device, non_blocking=False)` | moves tensor batch only | non-tensors and meta stay on host |
| `proto.reorder(indices)` | reorders tensor and non-tensor batches in-place | `indices` must address the current batch dimension |
| `proto.repeat(repeat_times, interleave=True)` | returns repeated tensor and non-tensor rows | `interleave=True` yields `a,a,b,b`; `False` yields `a,b,a,b` |

`meta_info` is passed through most split/select operations by reference unless you ask for a deep copy in `select`. Avoid mutating shared nested metadata in a child proto unless that is intentional.

## Split, concat, padding, and collation

```python
from verl.protocol import DataProto, pad_dataproto_to_divisor, unpad_dataproto

chunks = proto.chunk(chunks=2)
parts = proto.split(split_size=4)
merged = DataProto.concat(chunks)
padded, pad_size = pad_dataproto_to_divisor(proto, size_divisor=8)
restored = unpad_dataproto(padded, pad_size)
```

- `chunk(chunks)` requires `len(proto) % chunks == 0` and returns equally sized `DataProto` chunks.
- `split(split_size)` requires `len(proto) % split_size == 0`; it computes `chunks = len(proto) // split_size`.
- `DataProto.concat(list_of_proto)` concatenates tensor and non-tensor batches along dimension `0` and uses the first proto's `meta_info`.
- `pad_dataproto_to_divisor(data, size_divisor)` appends copies of rows from the beginning until the batch length is divisible by `size_divisor`; it returns `(padded_proto, pad_size)`.
- `unpad_dataproto(data, pad_size)` removes the last `pad_size` rows.
- `batch_collate(list_of_dicts)` converts a list of feature dictionaries into a dictionary of lists. `collate_fn` uses it to build `DataProto` mini-batches for `make_iterator`.
- `make_iterator(mini_batch_size, epochs, seed=None, dataloader_kwargs=None)` requires `proto.batch.batch_size[0] % mini_batch_size == 0` and yields `DataProto` mini-batches.

Use padding helpers when a downstream worker requires divisibility by data-parallel size, tensor-parallel size, rollout grouping, or micro-batch size. Always keep `pad_size` and unpad outputs before comparing to the original order or reporting metrics.

## Union semantics

`proto_a.union(proto_b)` mutates `proto_a` and merges all three namespaces:

- Tensor batches are merged by key. If both protos contain the same tensor key, the tensors must be equal and the TensorDict batch sizes must match.
- Non-tensor batches are merged by key. If both protos contain the same key, arrays must compare equal.
- `meta_info` is merged by key. If a key exists in both dictionaries, values must compare equal.

Preferred pattern:

```python
left = proto.select(batch_keys=["input_ids"], non_tensor_batch_keys=["sample_id"], meta_info_keys=["source"])
right = proto.select(batch_keys=["attention_mask"], non_tensor_batch_keys=[], meta_info_keys=[])
left.union(right)
```

If keys conflict and the values are not identical, rename, pop, or select disjoint namespaces before union. See [troubleshooting.md](troubleshooting.md) for the common `ValueError: Key already exists` case.

## DataProtoFuture for Ray handoff

`DataProtoFuture` wraps Ray object references so the driver can pass deferred `DataProto` results between worker groups.

- `DataProtoFuture.concat(futures)` creates a future that resolves by `DataProto.concat`.
- `future.chunk(chunks)` returns chunk-selecting `DataProtoFuture` objects.
- `future.get()` calls `ray.get`, validates each result is a `DataProto`, applies the collect function, and then applies the optional dispatch function.

Limitations: a `DataProtoFuture` is not a normal `DataProto` on the driver. Do not index, select, mutate, or inspect it before `get()`; pass it through or resolve it.

## Core algorithm helper APIs

Import from `verl.trainer.core_algos`.

### Advantage estimators

`AdvantageEstimator` values:

- `gae`
- `grpo`
- `grpo_passk`
- `reinforce_plus_plus`
- `remax`
- `rloo`

Use `compute_advantage_return(name, **kwargs)` to dispatch through the registered estimator map, or call the functions directly:

| Function | Required tensors | Shape expectation | Notes |
| --- | --- | --- | --- |
| `compute_gae_advantage_return(token_level_rewards, values, response_mask, gamma, lam, **kwargs)` | rewards, values, response mask | `(batch, response_length)` | returns whitened advantages and returns |
| `compute_grpo_outcome_advantage(token_level_rewards, response_mask, index, eps=1e-6, **kwargs)` | outcome rewards, mask, group index | rewards/mask `(batch, response_length)`, index `(batch,)` | each index group must contain more than one response |
| `compute_grpo_passk_outcome_advantage(token_level_rewards, response_mask, index, eps=1e-6, **kwargs)` | outcome rewards, mask, group index | same as GRPO | only the best response per group receives non-zero advantage |
| `compute_rloo_outcome_advantage(token_level_rewards, response_mask, index, **kwargs)` | outcome rewards, mask, group index | same as GRPO | each group must contain more than one response |
| `compute_reinforce_plus_plus_outcome_advantage(token_level_rewards, response_mask, gamma, **kwargs)` | rewards, mask, gamma | `(batch, response_length)` | discounted return with mask reset after EOS |
| `compute_remax_outcome_advantage(token_level_rewards, reward_baselines, response_mask, **kwargs)` | rewards, scalar baselines, mask | baselines `(batch,)` | uses reward baseline per response |

For GRPO/RLOO-style estimators, `index` groups sampled responses by prompt or rollout source. If every index is unique, EasyR1 raises an assertion requiring `rollout.n > 1`. When directly calling these helpers outside the trainer, prefer a Python or NumPy sequence of scalar group IDs; if a `torch.Tensor` of indices triggers one-row groups because zero-dimensional tensor objects are used as dictionary keys, convert it with `index.detach().cpu().numpy()` first.

### KL, reward, policy loss, and value loss

```python
from verl.trainer.core_algos import compute_kl, compute_policy_loss, compute_rewards, compute_value_loss
```

- `compute_kl(log_probs, ref_log_probs, kl_penalty)` supports `kl`, `abs`, `mse`, `low_var_kl`, and `full`.
  - `kl`: `log_probs - ref_log_probs`
  - `abs`: absolute log-prob difference
  - `mse`: half squared log-prob difference
  - `low_var_kl`: Schulman low-variance approximation with clamping
  - `full`: full `torch.nn.functional.kl_div(..., log_target=True, reduction="none").sum(-1)` path for distribution-shaped inputs
- `compute_rewards(token_level_scores, log_probs, ref_log_probs, kl_ratio)` subtracts `kl_ratio * (log_probs - ref_log_probs)` from token scores.
- `average_loss(values, mask, mode, eps=1e-8)` supports `mode="token"` for a batch-token masked mean and `mode="seq"` for per-sequence masked means averaged across sequences.
- `compute_policy_loss(old_log_probs, log_probs, advantages, response_mask, clip_ratio_low, clip_ratio_high, clip_ratio_dual, tau_positive, tau_negative, loss_type, loss_avg_mode, **kwargs)` returns `(pg_loss, metrics)`.
  - `loss_type="default"` is clipped PPO/DAPO-style loss.
  - `loss_type="gspo"` and `"gspo_token"` use sequence-level importance-ratio variants.
  - `loss_type="cispo"` uses the CISPO form.
  - `loss_type="sapo"` uses positive/negative advantage gates controlled by `tau_positive` and `tau_negative`.
  - Metrics include at least `ppo_kl` and `entropy_loss`; default clipped loss also reports clip fractions.
- `compute_value_loss(vpreds, returns, values, response_mask, cliprange_value, loss_avg_mode)` returns `(vf_loss, metrics)` with `vf_clipfrac` and `vpred_mean`.

All token-level tensors should normally share shape `(batch, response_length)`, and masks should be numeric or boolean tensors broadcastable to that shape. Keep dtypes floating for log-probs, rewards, advantages, and values.

### KL controllers

- `FixedKLController(init_kl_coef)` exposes a constant `kl_coef`; `update` is a no-op.
- `AdaptiveKLController(init_kl_coef, target_kl, horizon)` updates `kl_coef` using clipped proportional error; `horizon` must be positive.
- `get_kl_controller(algorithm_config)` expects config attributes `kl_type`, `kl_coef`, and, for adaptive mode, `kl_target` and `kl_horizon`.

## Torch functional helpers

Import from `verl.utils.torch_functional` when debugging masks or token log-probs.

| Helper | Purpose | Key constraints |
| --- | --- | --- |
| `log_probs_from_logits(logits, labels)` | returns log-prob of label ids from logits | logits `(batch, seq, vocab)`, labels `(batch, seq)`; falls back to PyTorch CE when flash-attn CE is unavailable |
| `masked_mean(values, mask, dim=None, eps=1e-8)` | masked mean | mask sum near zero yields denominator `eps` |
| `masked_var(values, mask, unbiased=True)` | masked variance | warns if unbiased correction sees mask sum <= 1 |
| `masked_whiten(values, mask, eps=1e-8)` | zero-center/scale under mask | requires non-degenerate mask for meaningful scale |
| `get_response_mask(response_ids, eos_token_id=2, dtype=torch.long)` | mask is `1` through the first EOS token and `0` after it | `eos_token_id` can be int or list |
| `pad_2d_list_to_length(response, pad_token_id, max_length=None)` | pads ragged 2D lists to a tensor | max length defaults to longest row |
| `pad_sequence_to_length(tensor, max_seq_len, pad_token_id, left_pad=False)` | pads last dimension | returns unchanged tensor if already long enough |
| `postprocess_data(input_ids, attention_mask, position_ids, max_length, pad_token_id, left_pad=True, truncation="error")` | pad/truncate a single sequence triple | truncation must be `left`, `right`, or `error` |

Scheduler helpers include constant and cosine warmup schedules. `AnyPrecisionAdamW` is an optimizer implementation used by training components; treat it as training-internal unless debugging optimizer state or precision behavior.

## Dynamic sequence-length batching

Import from `verl.utils.seqlen_balancing`.

```python
from verl.utils.seqlen_balancing import prepare_dynamic_batch, restore_dynamic_batch

micro_batches, batch_idx_list = prepare_dynamic_batch(proto, max_token_len=4096)
# run model/worker code on micro_batches in returned order
restored_tensor = restore_dynamic_batch(torch.cat(outputs, dim=0), batch_idx_list)
```

Main functions:

| Function | Input | Output | Notes |
| --- | --- | --- | --- |
| `get_seqlen_balanced_partitions(seqlen_list, k_partitions, equal_size)` | list of sequence lengths | list of index lists | uses Karmarkar-Karp; requires `len(seqlen_list) >= k_partitions`; `equal_size=True` requires divisibility |
| `log_seqlen_unbalance(seqlen_list, partitions, prefix)` | lengths and partitions | metric dictionary | returns min/max/balanced min/max/mean keys with prefix |
| `rearrange_micro_batches(batch, max_token_len, dp_group=None)` | TensorDict with `attention_mask` | list of TensorDict micro-batches and index map | `max_token_len` must be at least sequence length |
| `prepare_dynamic_batch(data, max_token_len)` | `DataProto` with `attention_mask` in `batch` | list of `DataProto` micro-batches and index map | splits non-tensors with the same index map |
| `restore_dynamic_batch(data, batch_idx_list)` | concatenated tensor output in micro-batch order | tensor restored to original row order | use the exact `batch_idx_list` from preparation |

Dynamic batching balances valid token counts, not semantic grouping. Keep prompt/response grouping identifiers in `non_tensor_batch` or tensor columns if a later algorithm depends on original groups.

## Logger and tracker helpers

Import from `verl.utils.logger` or `verl.utils.logger.logger`.

`Tracker(loggers="console", config=None)` accepts a string or list of logger names. Supported scalar loggers are:

- `console`
- `file`
- `mlflow`
- `swanlab`
- `tensorboard`
- `wandb`

`Tracker.log(data, step)` sends scalar metrics to each configured logger. `Tracker.log_generation(samples, step)` sends generation samples to compatible generation loggers, where each sample is `(prompt, output, label, score)`.

Config keys commonly needed by loggers:

```python
config = {
    "trainer": {
        "project_name": "debug-project",
        "experiment_name": "debug-run",
        "save_checkpoint_path": "checkpoints/debug-run",
    }
}
```

Logger-specific behavior:

- `ConsoleLogger` prints config and metrics.
- `FileLogger` writes experiment config, JSONL metrics, and generation logs under `trainer.save_checkpoint_path`.
- `TensorBoardLogger` uses `TENSORBOARD_DIR` or `tensorboard_log` and needs TensorBoard installed.
- `WandbLogger`, `SwanlabLogger`, and `MlflowLogger` require their optional packages and any service credentials/modes needed by those tools.
- `AggregateGenerationsLogger` routes generation samples only to generation-capable backends: console, file, wandb, and swanlab.

## Checkpoint utility relationships for debugging

Core API debugging sometimes touches checkpoint metadata, but model export is owned by the checkpoint-export sub-skill.

Support utilities:

- `CHECKPOINT_TRACKER` is the tracker filename `checkpoint_tracker.json`.
- `find_latest_ckpt(path, directory_format="global_step_{}")` reads the tracker, checks whether the referenced step directory exists, and returns `(checkpoint_path, tracker_info)` or `(None, None)`.
- `remove_obsolete_ckpt(path, global_step, best_global_step, save_limit=-1, directory_format="global_step_{}")` removes older step directories while preserving the best step and the newest retained checkpoints.
- `BaseCheckpointManager` saves/loads model, optimizer, scheduler, RNG state, and processor/tokenizer in a distributed FSDP setting; it is not a lightweight CPU-only export helper.

Use these relationships to explain resume/tracker behavior or checkpoint cleanup. For converting actor shards to Hugging Face format, inspect, or merge LoRA checkpoints, route to checkpoint-export.

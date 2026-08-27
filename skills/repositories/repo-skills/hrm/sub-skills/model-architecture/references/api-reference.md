# HRM API and Config Reference

## Dynamic model identifiers

HRM stores model and loss references as strings in Hydra config files. The
utility `utils.functions.load_model_class(identifier, prefix="models.")` splits
an identifier at `@`, imports `prefix + module_path`, and returns the named
class.

Verified identifiers from `config/arch/hrm_v1.yaml`:

| Identifier | Resolves to |
|---|---|
| `hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1` | `models.hrm.hrm_act_v1.HierarchicalReasoningModel_ACTV1` |
| `losses@ACTLossHead` | `models.losses.ACTLossHead` |

If adding a new model, keep the `module@class` format and ensure the module is
importable under the `models.` prefix.

## `HierarchicalReasoningModel_ACTV1Config`

Verified pydantic fields:

- Required data/model shape: `batch_size`, `seq_len`, `num_puzzle_identifiers`,
  `vocab_size`.
- Cycles/layers: `H_cycles`, `L_cycles`, `H_layers`, `L_layers`.
- Transformer shape: `hidden_size`, `expansion`, `num_heads`, `pos_encodings`.
- Puzzle embeddings: `puzzle_emb_ndim`.
- Halting/Q-learning: `halt_max_steps`, `halt_exploration_prob`.
- Numeric details: `rms_norm_eps` default `1e-5`, `rope_theta` default
  `10000.0`, `forward_dtype` default `bfloat16`.

Default architecture config:

```yaml
name: hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1
loss:
  name: losses@ACTLossHead
  loss_type: stablemax_cross_entropy
halt_exploration_prob: 0.1
halt_max_steps: 16
H_cycles: 2
L_cycles: 2
H_layers: 4
L_layers: 4
hidden_size: 512
num_heads: 8
expansion: 4
puzzle_emb_ndim: ${.hidden_size}
pos_encodings: rope
```

## Losses

Verified signatures:

```python
stablemax_cross_entropy(logits, labels, ignore_index: int = -100)
softmax_cross_entropy(logits, labels, ignore_index: int = -100)
ACTLossHead(model: torch.nn.Module, loss_type: str)
```

`ACTLossHead` calls the wrapped model, reads `labels` from
`new_carry.current_data`, computes per-token LM loss, exact sequence accuracy,
Q-halt accuracy, Q-halt loss, and optional Q-continue loss when the model emits
`target_q_continue` during training. `IGNORE_LABEL_ID` is `-100`; dataset labels
matching metadata `ignore_label_id` are converted to `-100` in `PuzzleDataset`.

## Attention/layer dependencies

`models/layers.py` first tries:

```python
from flash_attn_interface import flash_attn_func
```

and falls back to:

```python
from flash_attn import flash_attn_func
```

The `Attention` block projects QKV, applies RoPE when configured, calls
`flash_attn_func(q=query, k=key, v=value, causal=False)`, and reshapes the
result before the output projection. If FlashAttention returns a tuple, the
first element is used for FA2/FA3 compatibility.

## Sparse puzzle embeddings

When `puzzle_emb_ndim > 0`, `HierarchicalReasoningModel_ACTV1_Inner` creates a
`CastedSparseEmbedding`. During training, the sparse embedding copies selected
puzzle rows into local per-batch buffers and the custom distributed SignSGD
optimizer updates only touched puzzle ids. During evaluation, it reads directly
from the full persistent embedding table.

## Pretrain config fields

`PretrainConfig` fields verified from live inspection:

`arch`, `data_path`, `global_batch_size`, `epochs`, `lr`, `lr_min_ratio`,
`lr_warmup_steps`, `weight_decay`, `beta1`, `beta2`, `puzzle_emb_lr`,
`puzzle_emb_weight_decay`, `project_name`, `run_name`, `checkpoint_path`,
`seed`, `checkpoint_every_eval`, `eval_interval`, `eval_save_outputs`.

`load_synced_config` fills default `project_name`, `run_name`, and
`checkpoint_path` on rank 0, then broadcasts the config under distributed
training.

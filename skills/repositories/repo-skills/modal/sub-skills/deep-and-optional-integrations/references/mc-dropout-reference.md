# MC Dropout Reference

`modAL.dropout` provides PyTorch/skorch Monte Carlo dropout query strategies. Use these only when the learner estimator is skorch-like, initialized, and the pool is represented as PyTorch tensors or a dictionary of tensors.

## Query strategy functions

| Function | Selects instances by | Shared important parameters |
|---|---|---|
| `mc_dropout_bald` | BALD-style disagreement over dropout cycles | `n_instances`, `random_tie_break`, `dropout_layer_indexes`, `num_cycles`, `sample_per_forward_pass`, `logits_adaptor` |
| `mc_dropout_mean_st` | Largest mean per-class standard deviation over cycles | Same |
| `mc_dropout_max_entropy` | Largest entropy over dropout-cycle predictions | Same |
| `mc_dropout_max_variationRatios` | Largest variation ratio over mean cycle probabilities | Same |

Each strategy calls `get_predictions(...)`, computes a utility score, then returns the usual modAL selector result: selected indexes plus selected utility values. The exact downstream shape follows the same selector conventions used by other modAL query strategies.

## Parameters that matter in practice

| Parameter | Meaning | Practical guidance |
|---|---|---|
| `classifier` | Usually a `DeepActiveLearner`; must expose `classifier.estimator.module_` and `classifier.estimator.infer(...)`. | Construct with a skorch `NeuralNetClassifier` and let `DeepActiveLearner` call `initialize()`. |
| `X` | Pool to score. | Must be a `torch.Tensor` or a mapping/dictionary whose values are tensors. NumPy, pandas, lists, and scipy matrices are rejected by `get_predictions`. |
| `dropout_layer_indexes` | Indexes into `list(model.modules())` identifying dropout layers. | Use `[]` to activate all dropout layers. If specifying indexes, choose modules whose class name starts with `Dropout`. |
| `num_cycles` | Number of stochastic forward-pass cycles. | Larger values reduce MC noise but cost time and memory. Start small for debugging. |
| `sample_per_forward_pass` | Maximum number of samples per split forward pass. | Lower it to reduce peak memory; increase it only after the user's runtime has capacity. Must be greater than zero. |
| `logits_adaptor` | Callable `(input_tensor, samples) -> tensor` before softmax. | Use when the model output has extra dimensions, nested structures, or padding that must become shape `(n_samples, n_classes)`. |

## `get_predictions` behavior

`get_predictions(classifier, X, dropout_layer_indexes=[], num_predictions=50, sample_per_forward_pass=1000, logits_adaptor=...)`:

1. Asserts `num_predictions > 0` and `sample_per_forward_pass > 0`.
2. Calls `set_dropout_mode(classifier.estimator.module_, dropout_layer_indexes, train_mode=True)`.
3. Splits tensor inputs with `torch.split(X, sample_per_forward_pass)`.
4. For dictionary inputs, splits each tensor value by `sample_per_forward_pass` and reconstructs dictionaries for each split.
5. Calls `classifier.estimator.infer(samples)` under `torch.no_grad()`.
6. Applies `logits_adaptor`, softmaxes non-NaN values, concatenates split predictions, and appends NumPy arrays to the prediction list.
7. Calls `set_dropout_mode(..., train_mode=False)` to put dropout layers back into evaluation mode.

Because reset happens at the end of the normal path, if user code interrupts or raises in a custom adaptor, explicitly reset with `set_dropout_mode(model, indexes, train_mode=False)` before continuing.

## Tensor and dictionary input patterns

Convert NumPy pools explicitly before MC dropout:

```python
import torch

X_tensor = torch.as_tensor(X_numpy, dtype=torch.float32)
query_idx, scores = learner.query(
    X_tensor,
    n_instances=5,
    dropout_layer_indexes=[],
    num_cycles=5,
    sample_per_forward_pass=64,
)
```

For models whose `forward` expects keyword-like dictionary inputs, pass a dictionary of tensors with aligned first dimensions:

```python
X_pool = {
    "tokens": torch.as_tensor(token_ids, dtype=torch.long),
    "mask": torch.as_tensor(attention_mask, dtype=torch.float32),
}
query_idx, scores = learner.query(X_pool, num_cycles=3, sample_per_forward_pass=32)
```

If the estimator or model expects a tuple/list instead of a tensor or dictionary, adapt the model/skorch wrapper so `infer(samples)` accepts one of the supported shapes. Do not pass a raw NumPy array directly to MC dropout.

## Dropout layer indexes

`set_dropout_mode(model, dropout_layer_indexes, train_mode)` inspects `list(model.modules())`.

- `dropout_layer_indexes=[]` means “toggle every module whose class name starts with `Dropout`.”
- A specified index must point to a dropout module. If it points to a non-dropout module, modAL raises `KeyError` with a message that the index is not a Dropout layer.
- An out-of-range index can raise the normal Python index error from the modules list.
- To recover, enumerate modules, choose only dropout rows, or use `[]` while debugging.

The bundled inspection helper can demonstrate this safely:

```bash
python scripts/dropout_inspection.py --list-layers
python scripts/dropout_inspection.py --layer-index 4 --demo-bad-index
```

Run it from the sub-skill directory or pass the script path from any current working directory.

## `logits_adaptor` examples

The default adaptor returns the model output unchanged. If the model returns extra dimensions, flatten from dimension 1 so the result is `(batch, classes_or_logits)`:

```python
def flatten_logits(logits, samples):
    return torch.flatten(logits, start_dim=1)

query_idx, scores = learner.query(
    X_tensor,
    logits_adaptor=flatten_logits,
    num_cycles=3,
    sample_per_forward_pass=16,
)
```

If the model returns a tuple, select the logits tensor before returning:

```python
def tuple_logits(output, samples):
    logits, *_ = output
    return logits
```

The adaptor must return a torch tensor compatible with `softmax(-1)`.

## CPU, CUDA, and memory claims

This skill's verified boundary is CPU-oriented import and API inspection. MC dropout can run on whatever device the user's PyTorch/skorch estimator and tensors are already using, but do not claim CUDA correctness without a separate CUDA smoke test in that environment. For memory pressure, first lower `sample_per_forward_pass`, then lower `num_cycles`, then reduce `n_instances` or pool size for a diagnostic run.

# loralib API reference

This reference distills the public surface in `loralib/layers.py` and
`loralib/utils.py`; signatures were also checked in the installed `loralib`
0.1.2 package.

## Layer signatures

```python
lora.Linear(
    in_features: int,
    out_features: int,
    r: int = 0,
    lora_alpha: int = 1,
    lora_dropout: float = 0.0,
    fan_in_fan_out: bool = False,
    merge_weights: bool = True,
    **kwargs,
)

lora.Embedding(
    num_embeddings: int,
    embedding_dim: int,
    r: int = 0,
    lora_alpha: int = 1,
    merge_weights: bool = True,
    **kwargs,
)

lora.MergedLinear(
    in_features: int,
    out_features: int,
    r: int = 0,
    lora_alpha: int = 1,
    lora_dropout: float = 0.0,
    enable_lora: list[bool] = [False],
    fan_in_fan_out: bool = False,
    merge_weights: bool = True,
    **kwargs,
)
```

`Conv1d`, `Conv2d`, and `Conv3d` are thin constructors over the repository's
`ConvLoRA` wrapper. They forward the ordinary convolution arguments plus
`r`, `lora_alpha`, `lora_dropout`, and `merge_weights`.

## Parameter semantics

- `r=0` leaves the base layer unchanged and does not create `lora_A` or
  `lora_B`. A positive rank creates the low-rank factors.
- `scaling = lora_alpha / r`. Choose `lora_alpha` relative to the rank rather
  than treating it as a second rank.
- The base `weight` is frozen when the adapter is active. The factors are named
  `lora_A` and `lora_B`, which is the key convention used by the utility
  functions.
- `lora_dropout` is applied to the input path of dense/fused linear layers.
- `fan_in_fan_out=True` transposes the low-rank update to match layers whose
  stored weight layout is `(fan_in, fan_out)`.
- `merge_weights=True` merges on `eval()` and unmerges on `train()`; set it to
  `False` when the surrounding model must always execute the explicit update.

## Utility signatures

```python
lora.mark_only_lora_as_trainable(
    model: torch.nn.Module,
    bias: str = "none",
) -> None

lora.lora_state_dict(
    model: torch.nn.Module,
    bias: str = "none",
) -> dict[str, torch.Tensor]
```

`bias` accepts exactly `"none"`, `"all"`, or `"lora_only"`:

- `none`: only names containing `lora_` are trainable/saved.
- `all`: all model biases are trainable/saved alongside LoRA factors.
- `lora_only`: only biases belonging to modules that have a LoRA layer are
  trainable/saved.

Invalid bias values raise `NotImplementedError` in the repository utilities.

## Fused projections

For a fused QKV layer with `out_features = 3 * hidden_size`, use a three-entry
mask such as `[True, False, True]`. The mask selects equal-width output slices
in order. The constructor asserts that `len(enable_lora)` divides
`out_features`; a mismatch is a configuration error, not a checkpoint issue.

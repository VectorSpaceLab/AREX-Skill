# Core API troubleshooting

## Import and version

- `ModuleNotFoundError: torch`: install a PyTorch build that matches the
  target CPU/CUDA/ROCm backend before installing or importing `loralib`.
- `ModuleNotFoundError: loralib`: install the `loralib` distribution into the
  interpreter running the model; an editable source install is optional.
- `AttributeError` on a layer argument: check the pinned API in
  `references/api-reference.md`. This repository's helpers are small and do
  not provide the complete modern PEFT interface.

## Layer construction

- `AssertionError: The length of enable_lora must divide out_features`: choose
  a mask whose length divides the fused output width. For QKV use three slices
  and `out_features=3*hidden_size`.
- Shape errors in a fused or Conv1D-style projection: check
  `fan_in_fan_out`; it must agree with how the host layer stores its weight.
- No `lora_A`/`lora_B` attributes: `r` was zero, `enable_lora` contains no true
  entries, or the ordinary base layer was never replaced.

## Optimizer and checkpoints

- Full-model updates: call `mark_only_lora_as_trainable` before constructing
  the optimizer. Re-run the `requires_grad` inspection after loading a base
  checkpoint.
- Base model missing after adapter load: load the base checkpoint separately;
  adapter state is intentionally incomplete.
- Unexpected adapter keys: recreate the exact module names and rank/mask before
  loading. Do not remove keys just to silence an error.
- Bias mismatch: `bias="all"` and `bias="lora_only"` change both trainability
  and saved keys. Use the same value when saving and loading.

## Merge behavior

If predictions differ between `train()` and `eval()` beyond dropout effects,
check `layer.merged`, `merge_weights`, and repeated mode transitions. The
repository updates weights in place when merging; never add the update manually
while `merged` is already true. Set `merge_weights=False` for models that need
an explicit, always-unmerged path.

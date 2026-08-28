# LoRA and checkpoint operations

## LoRA lifecycle

A typical lifecycle is:

1. Fine-tune with LoRA against a known base model and rank.
2. Keep the adapter file and the exact base/model revision.
3. Extract an adapter by comparing base and fine-tuned weights when needed.
4. Merge the adapter into a copy of the base model, never the only source.
5. Compare merged output with the fine-tuned reference using fixed prompt,
   seed, resolution, frames, steps, and guidance. Use SSIM/LPIPS only when the
   required metric packages and reference policy are available.

LoRA-only training generally needs a higher learning rate than full fine-tuning
because most base weights are frozen. Rank, target modules, dtype, and model
family must match the loader's expectations. A successful file write is not
proof that keys or output behavior are correct.

## Checkpoint conversion

The target is the FastVideo-native component `state_dict`, not an imagined
Diffusers layout. Define an explicit parameter-name mapping, handle fused/split
QKV and MLP keys, and list intentionally skipped training-only keys. Validate
shape, dtype, key coverage, and a small forward/parity check before publishing.
Keep converters separate from model classes and do not rely on private loader
forks.

Generic `.pt` to safetensors conversion is only a container-format operation;
it cannot repair wrong keys, tensors, or architecture. Avoid overwrite unless a
backup and explicit authorization exist. Hub upload requires credentials and is
not part of a safe local smoke.

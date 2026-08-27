# Troubleshooting

## Shape mismatch

### Symptom
- `RuntimeError` while loading a checkpoint or running a forward pass
- size mismatch in `load_state_dict`
- hourglass pooling or upsampling failures on custom inputs

### Likely causes
- input is not RGB and does not have 3 channels
- custom spatial size is too small or not divisible by 16 for the hourglass path
- checkpoint was saved with a different `ngf`, `ndf`, or `light` setting
- a training checkpoint was loaded into an inference-only model or vice versa

### Checks
- Run `python scripts/model_forward_smoke.py --repo-root /path/to/checkout` first.
- Keep synthetic test sizes at `32 × 32` or larger, and prefer sizes divisible by 16.
- Confirm the checkpoint dictionary key map before loading it.

### Fix
- Use `(N, 3, H, W)` tensors.
- Match the architecture arguments used when the weights were saved.
- If you are only checking the generator, load the `genA2B` entry rather than the full training dictionary.

## Checkpoint missing keys

### Symptom
- `KeyError: 'genA2B'`
- missing `disGA`, `disGB`, `disLA`, or `disLB`

### Likely causes
- the file is not a full training snapshot
- a generator-only weight file is being treated like a training checkpoint
- `DataParallel` or export code changed the stored names

### Checks
- Inspect the checkpoint with the smoke script.
- Compare the keys against the training-object reference.

### Fix
- Use the full dictionary for training resume.
- Use the `genA2B` entry for generator-only inference checks.

## Deprecated `F.upsample` warning

### Symptom
- deprecation warnings during forward passes on modern PyTorch

### Cause
- `HourGlassBlock` still uses `torch.nn.functional.upsample`

### Fix
- The warning is expected for source compatibility.
- When porting, replace it with `torch.nn.functional.interpolate` and re-check shapes.

## Device mismatch

### Symptom
- `Expected all tensors to be on the same device`
- checkpoint load or face-ID smoke fails on CPU/GPU differences

### Checks
- Confirm the model and synthetic input are on the same device.
- When loading a checkpoint, use `map_location` that matches the smoke device.

### Fix
- Keep the smoke on CPU unless you explicitly need GPU coverage.
- Move the input tensor, generator, and MobileFaceNet to the same device.

## Face ID model asset missing

### Symptom
- face-ID verification cannot start
- `model_mobilefacenet.pth` is absent

### Fix
- Provide `models/model_mobilefacenet.pth` before claiming face-ID verification.
- If the asset is unavailable, skip the face-ID smoke and report the gap explicitly.

## Porting note

If you port the architecture or trainer, verify these three things again:

1. tuple return order
2. checkpoint key map
3. normalization range

Those are the most common regressions when the model internals are reimplemented in another codebase.


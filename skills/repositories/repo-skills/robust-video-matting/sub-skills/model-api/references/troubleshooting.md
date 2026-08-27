# Model API Troubleshooting

## Import fails: `No module named model`

**Likely cause:** RobustVideoMatting is source-checkout oriented and does not
ship package metadata in this repository snapshot. The top-level source folder
must be on `PYTHONPATH` or added explicitly.

**Recovery:** Run bundled helpers with `--repo-root /path/to/RobustVideoMatting`
or add that checkout to `PYTHONPATH` before importing `from model import
MattingNetwork`.

## Invalid variant or refiner assertion

**Symptoms:** `AssertionError` during `MattingNetwork(...)` construction.

**Likely cause:** The source accepts only:

- `variant in ["mobilenetv3", "resnet50"]`
- `refiner in ["fast_guided_filter", "deep_guided_filter"]`

**Recovery:** Normalize spelling and case. Prefer `mobilenetv3` and
`deep_guided_filter` unless the user specifically asked otherwise.

## Shape error or nonsensical channel counts

**Symptoms:** convolution errors, unexpected output channels, or tensors treated
as batch/time dimensions.

**Likely cause:** Input is channel-last (`[H,W,C]` or `[B,H,W,C]`) or lacks the
batch dimension. RVM expects channel-first:

- `[B,3,H,W]` for single frames/batches.
- `[B,T,3,H,W]` for chunks.

**Recovery:** Convert images through a tensor transform that produces
channel-first RGB floats. Add batch/time axes intentionally. Verify with
`scripts/rvm_model_smoke.py` before debugging a larger pipeline.

## Poor temporal stability or flickering

**Likely cause:** Recurrent states are not recycled. Calling
`model(frame)[:2]` for every frame discards temporal memory.

**Recovery:** Initialize `rec = [None] * 4`, then call
`fgr, pha, *rec = model(src, *rec, downsample_ratio)` for each frame or chunk.
For a chunked `[B,T,C,H,W]` input, carry the four returned states into the next
chunk.

## `segmentation_pass=True` returns the wrong outputs

**Symptoms:** Code expects `fgr, pha` but gets a single-channel tensor.

**Likely cause:** In segmentation mode, the model returns segmentation logits
plus recurrent states: `seg, *rec`. It does not return foreground/alpha.

**Recovery:** Use default `segmentation_pass=False` for matting inference. Use
segmentation mode only for training/diagnostic code that expects logits.

## Pretrained backbone unexpectedly downloads weights

**Likely cause:** `pretrained_backbone=True` calls TorchVision's model-weight
download. This is separate from official RVM checkpoint loading.

**Recovery:** For offline smoke tests use `MattingNetwork(...,
pretrained_backbone=False)`. For official inference load an RVM checkpoint into
the constructed model, or use TorchHub when network access is acceptable.

## Device or dtype mismatch

**Symptoms:** tensors are on CPU while the model is on CUDA, or a frozen model
cannot reveal parameter dtype/device.

**Recovery:** Move input tensors and recurrent states to the same device and
compatible dtype as the model. Converter workflows involving frozen TorchScript
models should explicitly provide `device` and `dtype`; see
[../../inference-workflows/references/converter-reference.md](../../inference-workflows/references/converter-reference.md).

## Downsample/refiner surprises

**Symptoms:** low-quality output, unexpected memory usage, or confusion about
spatial sizes.

**Likely cause:** `downsample_ratio` controls stage-1 resolution while the
refiner returns output at input resolution. Higher ratios are not always better.

**Recovery:** Start with the inference guide's practical choices: about `0.25`
for 1080p portrait video and lower for 4K portrait shots. Use `1` for tiny
smoke tests when avoiding refiner/downsample complexity.

## CUDA requested but unavailable

**Symptoms:** Bundled smoke script exits with CUDA unavailable.

**Recovery:** Use `--device cpu` for API validation, or install a CUDA-capable
PyTorch build in an environment with compatible NVIDIA drivers. A CPU smoke
proves the API shape contract only; it does not verify speed or high-resolution
CUDA behavior.

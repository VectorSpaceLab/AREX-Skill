# Inference Troubleshooting

## `Must provide at least one output`

`convert_video` asserts that at least one of `output_composition`,
`output_alpha`, or `output_foreground` is provided. For CLI use, pass one or
more of `--output-composition`, `--output-alpha`, or `--output-foreground`. For
the bundled image-sequence helper, omit all output booleans only if you accept
its default composition+alpha behavior.

## Invalid `output_type`

The converter supports only `"video"` and `"png_sequence"`. Use PNG sequence
mode for debuggable artifacts and fewer media-encoding dependencies.

## Downsample ratio assertion

`downsample_ratio` must be omitted or satisfy `0 < ratio <= 1`. For automatic
max-side-512 behavior, leave it as `None`. For 1080p portrait video, `0.25` is a
reasonable starting point.

## `No module named av`, `pims`, or video codec errors

Video reading/writing depends on PyAV/PIMS and FFmpeg-capable wheels or system
libraries. If the user only needs frames, switch to image-sequence input and
`output_type="png_sequence"`. If video output is required, install media
dependencies and confirm the container/codec can be opened before blaming the
model.

## Image sequence order is wrong

`ImageSequenceReader` sorts filenames lexicographically. Names such as `1.png`,
`10.png`, `2.png` sort unexpectedly. Rename to zero-padded names like
`0001.png`, `0002.png`, `0010.png` before conversion.

## Checkpoint loading fails

Symptoms include missing/unexpected keys or device deserialization errors.

Recovery:

- Match checkpoint variant to model variant (`mobilenetv3` weights with
  `MattingNetwork("mobilenetv3")`, not `resnet50`).
- Use `torch.load(path, map_location=device)` when loading on CPU or a different
  GPU than the checkpoint was saved from.
- Confirm the file is a PyTorch RVM state dict, not a TorchScript/ONNX/CoreML
  artifact.

## CUDA requested but unavailable

Use CPU for functionality checks, or install a CUDA-capable PyTorch build in an
environment with compatible NVIDIA drivers. CPU conversion can be very slow for
large videos; do not present it as evidence for RVM's GPU speed claims.

## Frozen TorchScript converter fails to infer dtype/device

The converter infers dtype and device from `next(model.parameters())`. Frozen
TorchScript modules may need explicit arguments:

```python
convert_video(frozen_model, ..., device="cuda", dtype=torch.float32)
```

## TorchHub unexpectedly needs network

`torch.hub.load("PeterL1n/RobustVideoMatting", "mobilenetv3")` defaults to
pretrained weights and can download both source and checkpoint files. Use local
checkpoint loading when offline or when reproducibility requires explicit
artifacts. For source-level smoke tests, `hubconf.mobilenetv3(pretrained=False)`
avoids downloading weights.

## ONNX recurrent states are wrong

Initial ONNX recurrent states are zero arrays shaped `[1,1,1,1]` with dtype
matching the model precision. `downsample_ratio` is always FP32 shaped `[1]`.
Recycle `r1o..r4o` into `r1i..r4i` for the next frame.

## TensorFlow outputs look transposed

TensorFlow SavedModel examples use channel-last `[B,H,W,C]`; PyTorch examples
use channel-first `[B,C,H,W]`. Transpose inputs and outputs when moving between
frameworks.

## CoreML rejects image size or recurrent inputs

Official CoreML artifacts are fixed-resolution. The first frame should omit
recurrent inputs; later frames should include `r1i..r4i`. If the requested size
is different, resize before inference or export a matching CoreML model.

## Video output is much slower than published FPS

The README speed table measures tensor throughput with `inference_speed_test.py`.
The converter uses Python video decoding/encoding and tensor transfers, so it
is expected to be slower. For speed investigations, separate model throughput
from media IO and route benchmarking details to
[../../evaluation-tools/SKILL.md](../../evaluation-tools/SKILL.md).

---
name: inference-workflows
description: "Use when running RobustVideoMatting inference, loading weights,
  using convert_video or TorchHub, converting image/video inputs, or reasoning
  about exported model runtimes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# RobustVideoMatting Inference Workflows

Use this sub-skill for user-facing RVM inference: loading models, converting
videos or image sequences, configuring outputs, and adapting the documented
runtime formats.

## Read this when

- The user asks to run RVM on a video or image sequence.
- The task mentions `convert_video`, `python inference.py`, output alpha,
  foreground, or composition files.
- You need to load official PyTorch weights, TorchHub models, TorchScript,
  ONNX, TensorFlow, TensorFlow.js, or CoreML RVM artifacts.
- The user is tuning `downsample_ratio`, `seq_chunk`, `input_resize`, video
  bitrate, or image-sequence output.

Route other tasks elsewhere:

- MattingNetwork constructor, forward tensors, and recurrent-state internals:
  [model-api](../model-api/SKILL.md).
- Dataset layouts and training stages: [training-data](../training-data/SKILL.md).
- Metric evaluation or speed benchmarking: [evaluation-tools](../evaluation-tools/SKILL.md).

## Inference workflow

1. Confirm the runtime surface.
   - For source-checkout PyTorch inference, import `MattingNetwork` and
     `convert_video` from the local RVM source modules.
   - For TorchHub, expect network access unless weights are already cached.
   - For exported formats, follow the tensor I/O contracts in
     [references/model-loading.md](references/model-loading.md).

2. Load a model.

   ```python
   import torch
   from model import MattingNetwork

   model = MattingNetwork("mobilenetv3").eval().to("cuda")
   model.load_state_dict(torch.load("rvm_mobilenetv3.pth", map_location="cuda"))
   ```

3. Convert a video file or sorted image-sequence directory with the converter
   API. Always request at least one output.

   ```python
   from inference import convert_video

   convert_video(
       model,
       input_source="frames_or_input.mp4",
       output_type="png_sequence",
       output_composition="composition",
       output_alpha="alpha",
       downsample_ratio=0.25,
       seq_chunk=4,
   )
   ```

4. For safe PNG image-sequence conversion from arbitrary working directories,
   use the bundled wrapper:

   ```bash
   python scripts/rvm_convert_image_sequence.py \
     --repo-root /path/to/RobustVideoMatting \
     --variant mobilenetv3 \
     --checkpoint rvm_mobilenetv3.pth \
     --input-dir frames \
     --output-dir rvm_outputs \
     --device cpu \
     --alpha --composition
   ```

5. Validate outputs. PNG sequence mode writes numbered images under the output
   directories you request. Video mode uses PyAV/H.264 and can fail for media
   dependency or codec reasons unrelated to model quality.

## Bundled references and script

- Read [references/converter-reference.md](references/converter-reference.md)
  for the verified `convert_video` signature, CLI flags, output modes, and
  downsample/sequence-chunk behavior.
- Read [references/model-loading.md](references/model-loading.md) for PyTorch,
  TorchHub, TorchScript, ONNX, TensorFlow, TensorFlow.js, and CoreML loading
  and tensor I/O contracts.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  checkpoint, media dependency, output selection, device/dtype, recurrent-state,
  and exported-runtime failures.
- Run [scripts/rvm_convert_image_sequence.py](scripts/rvm_convert_image_sequence.py)
  when the user has a local checkpoint plus frame directory and wants safe PNG
  outputs without invoking the original repo script directly.

## Key decisions

- Prefer `mobilenetv3` unless the user explicitly asks for the larger ResNet50
  variant.
- Use `output_type="png_sequence"` for debuggable alpha/foreground/composition
  artifacts; use `output_type="video"` only when video encoding dependencies are
  available and a video container is required.
- Leave `downsample_ratio=None` for auto max-side-512 behavior, or set it based
  on resolution/content. For 1080p portrait video, `0.25` is a common starting
  point.
- Increase `seq_chunk` to process multiple sequential frames at once when memory
  permits. The converter still recycles recurrent states across chunks.
- Do not automate pretrained weight downloads in generated scripts; ask users
  to provide explicit checkpoint paths or use TorchHub with clear network/cache
  expectations.

## Acceptance check for inference answers

A good answer names the selected runtime, exact converter arguments or CLI
flags, required input/output paths, checkpoint/device handling, validation
steps, and likely failure modes. It should not require future agents to open the
original repository docs or scripts.

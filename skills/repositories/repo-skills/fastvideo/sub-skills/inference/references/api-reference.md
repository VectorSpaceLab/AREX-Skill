# Inference API reference

## Public classes

`VideoGenerator.from_pretrained(model_path, **kwargs)` creates a generator from
a model ID/path and convenience engine options. `from_config(config)` accepts a
`GeneratorConfig` or mapping. `from_file(path, overrides=None)` loads a nested
JSON/YAML run configuration. `from_fastvideo_args(...)` is a lower-level
integration hook.

`generate(request, *, log_queue=None)` is the preferred entry point and accepts
a `GenerationRequest` or mapping, returning one `GenerationResult` or a list for
prompt batches. `generate_async(request, *, log_queue=None)` yields typed
progress/final events. `generate_video(...)` is deprecated compatibility code;
new integrations should not build around its legacy kwargs.

`SamplingParam.from_pretrained(model_path)` loads model-family defaults. It
contains input fields (`image_path`, `video_path`, references, control data),
text fields, dimensions/FPS, denoising/guidance, refinement, continuation,
output flags, and trajectory-return flags. The typed request is safer because
unknown fields are rejected at schema boundaries.

## Result behavior

Video results may include `video_path`, `frames`, `samples`, `size`, timing,
trajectory fields, and logging metadata. Image workloads save PNG, audio-only
workloads save WAV, and video workloads save MP4 when `save_video` is enabled.
`return_frames` controls materialized frame output and may be disabled for
metadata-only requests. Latent output is not RGB media.

## Common request patterns

- T2V: string `prompt` plus `sampling` and `output`.
- I2V: `inputs.image_path` or an in-memory image plus prompt.
- V2V/refine: `inputs.video_path`, `inputs.refine_from`, or family-specific
  references; confirm the preset before passing extra fields.
- Prompt batch: `prompt` can be a list; do not combine it with
  `inputs.prompt_path`. A prompt file is one non-empty prompt per line.
- LTX-2/audio: use model-specific typed fields and expect audio metadata or
  continuation envelopes where enabled.

Do not pass model-specific pipeline fields as arbitrary sampling fields. Use
`pipeline`/preset configuration for initialization and validated stage overrides
for supported per-request changes.

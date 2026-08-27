# Local Inference API Reference

Read this when translating a user request into the public `ltx_video.inference` API or checking which CLI flags map to `InferenceConfig`. For direct `LTXVideoPipeline` calls, use `../../pipeline-components/SKILL.md`; for YAML fields, use `../../model-configs/SKILL.md`.

## Public imports

```python
from ltx_video.inference import InferenceConfig, infer, load_pipeline_config
```

The root command script uses `transformers.HfArgumentParser(InferenceConfig)`, so dataclass fields become CLI flags. Both underscore and hyphen spellings are accepted for multi-word flags.

## `InferenceConfig` fields

| Field | Default | CLI flag(s) | Purpose / notes |
| --- | --- | --- | --- |
| `prompt` | required | `--prompt` | Prompt for generation. Write a detailed chronological cinematic paragraph. |
| `output_path` | `outputs/<date>` | `--output_path`, `--output-path` | Output directory. `infer` creates it and writes PNG/MP4 files inside. |
| `pipeline_config` | `configs/ltxv-13b-0.9.7-dev.yaml` | `--pipeline_config`, `--pipeline-config` | YAML config path. Prefer an explicit current config from `model-configs`. |
| `seed` | `171198` | `--seed` | Random seed used for Python, NumPy, torch, CUDA/MPS where available. |
| `height` | `704` | `--height` | Requested output height. `infer` pads to multiple of 32 internally. |
| `width` | `1216` | `--width` | Requested output width. `infer` pads to multiple of 32 internally. |
| `num_frames` | `121` | `--num_frames`, `--num-frames` | Requested frames. `infer` pads to `N*8+1` internally and crops back. |
| `frame_rate` | `30` | `--frame_rate`, `--frame-rate` | FPS for MP4 output. |
| `offload_to_cpu` | `False` | `--offload_to_cpu`, `--offload-to-cpu` | Only offloads when CUDA is available and total GPU memory is below 30 GiB. If no CUDA, warning says offload is irrelevant. |
| `negative_prompt` | `worst quality, inconsistent motion, blurry, jittery, distorted` | `--negative_prompt`, `--negative-prompt` | Negative prompt passed to the pipeline. |
| `input_media_path` | `None` | `--input_media_path`, `--input-media-path` | Image/video to modify with the video-to-video style path. Distinct from conditioning media. |
| `image_cond_noise_scale` | `0.15` | `--image_cond_noise_scale`, `--image-cond-noise-scale` | Noise scale for hard-conditioned image latents. |
| `conditioning_media_paths` | `None` | `--conditioning_media_paths`, `--conditioning-media-paths` | One or more image/video files used as keyframe/segment conditions. |
| `conditioning_strengths` | `None` | `--conditioning_strengths`, `--conditioning-strengths` | Optional strengths in `[0, 1]`, one per conditioning item. Defaults to all `1.0` when omitted. |
| `conditioning_start_frames` | `None` | `--conditioning_start_frames`, `--conditioning-start-frames` | Required when conditioning media paths are supplied; one target frame per item. |

## Key functions

```python
infer(config: InferenceConfig)
```

High-level generation entry point. It loads a YAML config, downloads checkpoint/upscaler files from Hugging Face when configured names are not local files, constructs the pipeline, loads optional prompt enhancer models when threshold logic enables them, validates conditioning arguments, pads dimensions/frame count, runs the pipeline, crops back, and writes PNG/MP4 outputs.

```python
load_pipeline_config(pipeline_config: str)
```

Searches first next to the installed `ltx_video` package and then at the user-supplied path. Raises `ValueError` if neither exists. Use `../../model-configs/scripts/inspect_ltxv_config.py` to validate custom YAML before calling `infer`.

```python
get_device()
```

Returns `"cuda"` if torch CUDA is available, else `"mps"` if MPS is available, else `"cpu"`.

```python
get_total_gpu_memory()
```

Returns the first CUDA device's total memory in GiB, or `0` when CUDA is unavailable.

```python
load_media_file(media_path, height, width, max_frames, padding, just_crop=False)
```

Loads image or video media, center-crops/resizes to the target aspect ratio, applies CRF compression to frames, normalizes to `[-1, 1]`, pads, and returns a tensor shaped `(1, 3, F, H, W)`. Video extensions recognized by the code are `.mp4`, `.avi`, `.mov`, and `.mkv`.

```python
prepare_conditioning(conditioning_media_paths, conditioning_strengths, conditioning_start_frames, height, width, num_frames, padding, pipeline)
```

Builds a list of `ConditioningItem` objects. For each media path it counts video frames when needed, lets a pipeline trim conditioning sequences if available, loads media with `just_crop=True`, and stores `(media_tensor, start_frame, strength)`.

## Validation behavior in `infer`

`infer` performs these static conditioning checks before generation:

- if `conditioning_media_paths` is provided, `conditioning_start_frames` must also be provided;
- `conditioning_media_paths`, `conditioning_strengths`, and `conditioning_start_frames` must have the same length when strengths are provided;
- every strength must be between `0` and `1` inclusive;
- every start frame must be in `[0, num_frames - 1]`.

Additional direct-pipeline assertions occur later, especially for video conditioning sequences:

- conditioning media tensors are rank 5 `(B, C, F, H, W)`;
- video conditioning frame counts should be `N*8+1`;
- non-first video conditioning sequences should start on multiples of 8;
- conditioned media must fit into the generated timeline after trimming.

## Padding formulas

`infer` runs generation on padded shapes and then crops the output back:

```python
height_padded = ((height - 1) // 32 + 1) * 32
width_padded = ((width - 1) // 32 + 1) * 32
num_frames_padded = ((num_frames - 2) // 8 + 1) * 8 + 1
```

This means a request such as `705x1217x122` costs the padded `736x1248x129` run, even though the saved output is cropped to the requested dimensions.

## Prompt enhancement behavior

The selected YAML controls prompt enhancement with three fields consumed by `infer`: `prompt_enhancement_words_threshold`, `prompt_enhancer_image_caption_model_name_or_path`, and `prompt_enhancer_llm_model_name_or_path`.

```python
prompt_word_count = len(config.prompt.split())
enhance_prompt = (
    prompt_enhancement_words_threshold > 0
    and prompt_word_count < prompt_enhancement_words_threshold
)
```

When `enhance_prompt` is true, pipeline construction loads the configured image-caption model, processor, LLM model, and tokenizer. These are separate from the base checkpoint and text encoder and can require their own cache/network and memory. When prompt word count meets or exceeds a positive threshold, enhancement is disabled for that run.

## Output naming

`infer` writes into `output_path` as a directory:

- one-frame outputs use `image_output_<batch>_<prompt-fragment>_<seed>_<HxWxF>_<index>.png`;
- multi-frame outputs use `video_output_<batch>_<prompt-fragment>_<seed>_<HxWxF>_<index>.mp4`.

The prompt fragment is sanitized and truncated. The index scans up to 999 to avoid overwrites; use a new directory for repeated experiments to avoid `FileExistsError`.

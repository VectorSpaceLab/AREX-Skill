# Local inference workflows

This reference covers the repository CLI `inference.py` and the public Python entry point `ltx_video.inference.infer(InferenceConfig)`. It does not cover direct `LTXVideoPipeline` wiring; route component-level work to `../../pipeline-components/SKILL.md`. Route YAML/model selection and config editing to `../../model-configs/SKILL.md`.

## Runtime preflight

Before a heavy local run:

1. Install the package with inference media extras. Missing `imageio`, `av`, or `torchvision` usually means the `[inference]` extra was not installed.
2. Choose a config deliberately. Do not rely on an implicit package default unless you have verified the file exists. Use the sibling `model-configs` catalog and inspector to choose or validate a readable YAML path before running.
3. Decide whether Hugging Face downloads are allowed. If `checkpoint_path` or `spatial_upscaler_model_path` in the config is not a local file, `infer` may download from the `Lightricks/LTX-Video` model repository. Text encoder and prompt-enhancer models are loaded with `transformers` from their configured names or local paths.
4. Confirm backend expectations. CUDA is the practical default for full generation; MPS is supported by the project on macOS; CPU import may work but full video generation can be impractically slow.
5. Validate output dimensions and frames. LTX-Video pads height/width to multiples of 32 and frame count to `N*8+1`, runs the padded shape, then crops to the requested shape.
6. For conditioning media, validate all lists together: paths, target start frames, and optional strengths.
7. Build commands with `../scripts/build_inference_command.py` or an argument list. Avoid string-concatenated shell commands for user-provided prompts or paths.

## Safe command builder

From this sub-skill directory or by using the script path directly:

```bash
python scripts/build_inference_command.py \
  --prompt "A cinematic shot of a red fox crossing a snowy road at sunrise" \
  --pipeline-config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 --width 1216 --num-frames 121 \
  --seed 1234 \
  --output-path outputs/fox-run
```

The builder prints one shell-safe command and emits static warnings to stderr. It does not import `ltx_video`, run inference, open checkpoints, or download models. If `--repo-root` points to a checkout or a config path is otherwise readable, it also inspects top-level YAML fields for prompt-enhancement, FP8, multi-scale, and network/download warnings. The printed command is a `python inference.py ...` command intended for an environment where the repo CLI script or an equivalent wrapper is available.

## Text-to-video through the CLI

Use no input or conditioning media for pure text-to-video:

```bash
python inference.py \
  --prompt "A handheld cinematic shot of waves crashing against black rocks at sunset, sea spray catching orange light" \
  --pipeline_config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 \
  --width 1216 \
  --num_frames 121 \
  --frame_rate 30 \
  --seed 171198 \
  --output_path outputs/t2v-smoke
```

Notes:

- Use explicit dimensions and frame count so padding and memory cost are intentional.
- The command writes into an output directory, not directly to a requested `.mp4` filename.
- A one-frame run (`--num_frames 1`) writes a PNG; multi-frame runs write MP4.

## Text-to-video through Python

```python
from ltx_video.inference import InferenceConfig, infer

config = InferenceConfig(
    prompt=(
        "A handheld cinematic shot of waves crashing against black rocks at "
        "sunset, sea spray catching orange light"
    ),
    pipeline_config="path/to/ltxv-13b-0.9.8-distilled.yaml",
    height=704,
    width=1216,
    num_frames=121,
    frame_rate=30,
    seed=171198,
    output_path="outputs/t2v-smoke",
)

infer(config)
```

Keep Python snippets as dataclass construction plus `infer(config)`. Route direct pipeline instantiation or batched `LTXVideoPipeline.__call__` use to `../../pipeline-components/SKILL.md`.

## Image-to-video / first-frame conditioning

The repository README models image-to-video as conditioning media at target frame `0`:

```bash
python inference.py \
  --prompt "A woman in a pink sweater turns toward the camera as fog drifts over a quiet field" \
  --conditioning_media_paths input_first_frame.png \
  --conditioning_start_frames 0 \
  --conditioning_strengths 1.0 \
  --image_cond_noise_scale 0.15 \
  --pipeline_config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 --width 1216 --num_frames 121 --seed 42 \
  --output_path outputs/i2v
```

Python equivalent:

```python
from ltx_video.inference import InferenceConfig, infer

infer(InferenceConfig(
    prompt="A woman in a pink sweater turns toward the camera as fog drifts over a quiet field",
    pipeline_config="path/to/ltxv-13b-0.9.8-distilled.yaml",
    height=704,
    width=1216,
    num_frames=121,
    seed=42,
    output_path="outputs/i2v",
    conditioning_media_paths=["input_first_frame.png"],
    conditioning_start_frames=[0],
    conditioning_strengths=[1.0],
    image_cond_noise_scale=0.15,
))
```

Important behavior:

- If strengths are omitted, `infer` uses `1.0` for every conditioning item.
- Images count as one-frame conditioning items, so any start frame in `[0, num_frames-1]` is valid at the top-level API validation stage.
- The media is center-cropped/resized and padded to match the padded generation dimensions.

## Video extension with conditioning media

For extension, place an existing video segment into the generated timeline with `conditioning_media_paths` and `conditioning_start_frames`.

Forward continuation from the beginning:

```bash
python inference.py \
  --prompt "The camera continues forward through the misty forest, revealing sunlight between tall pine trees" \
  --conditioning_media_paths opening_clip.mp4 \
  --conditioning_start_frames 0 \
  --conditioning_strengths 1.0 \
  --pipeline_config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 --width 1216 --num_frames 121 --seed 7 \
  --output_path outputs/extend-forward
```

Place a clip later in the timeline:

```bash
python inference.py \
  --prompt "A continuous cinematic transition from a quiet city street into a bright aerial view" \
  --conditioning_media_paths middle_reference.mp4 \
  --conditioning_start_frames 32 \
  --conditioning_strengths 0.8 \
  --pipeline_config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 --width 1216 --num_frames 121 --seed 8 \
  --output_path outputs/extend-middle
```

Rules for video conditioning sequences:

- Target start frames are zero-based.
- Top-level `infer` requires each start frame to be `0 <= start < num_frames`.
- For non-first video sequences, the pipeline requires the target start frame to be a multiple of 8.
- Video conditioning segments are expected as `N*8+1` frames (9, 17, 25, ...). The pipeline has a trimming helper for overlong sequences, but future agents should pre-trim or at least expect the logged trim so the effective conditioned segment is intentional.
- The conditioned segment must fit in the generated timeline after trimming.

## Video-to-video / input media modification

`input_media_path` is distinct from `conditioning_media_paths`. It supplies an image or video as the initial media item to modify through the pipeline rather than as a list of keyframe/segment conditions.

```bash
python inference.py \
  --prompt "Transform the input clip into a painterly golden-hour film shot while preserving the main motion" \
  --input_media_path source_clip.mp4 \
  --pipeline_config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 --width 1216 --num_frames 121 --seed 99 \
  --output_path outputs/v2v
```

Python:

```python
from ltx_video.inference import InferenceConfig, infer

infer(InferenceConfig(
    prompt="Transform the input clip into a painterly golden-hour film shot while preserving the main motion",
    pipeline_config="path/to/ltxv-13b-0.9.8-distilled.yaml",
    input_media_path="source_clip.mp4",
    height=704,
    width=1216,
    num_frames=121,
    seed=99,
    output_path="outputs/v2v",
))
```

Config fields such as `skip_initial_inference_steps` affect video-to-video strength/noising behavior and belong to YAML/config selection; route those decisions to `../../model-configs/SKILL.md`.

## Multiple conditioning items

Pass parallel lists in one CLI flag each:

```bash
python inference.py \
  --prompt "A dancer begins in a moonlit studio, leaps through a splash of blue light, then lands in a sunlit courtyard" \
  --conditioning_media_paths first_pose.png leap_reference.mp4 final_pose.png \
  --conditioning_start_frames 0 32 96 \
  --conditioning_strengths 1.0 0.7 0.9 \
  --pipeline_config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
  --height 704 --width 1216 --num_frames 121 --seed 314 \
  --output_path outputs/multi-condition
```

Python equivalent:

```python
from ltx_video.inference import InferenceConfig, infer

infer(InferenceConfig(
    prompt=(
        "A dancer begins in a moonlit studio, leaps through a splash of blue "
        "light, then lands in a sunlit courtyard"
    ),
    pipeline_config="path/to/ltxv-13b-0.9.8-distilled.yaml",
    conditioning_media_paths=["first_pose.png", "leap_reference.mp4", "final_pose.png"],
    conditioning_start_frames=[0, 32, 96],
    conditioning_strengths=[1.0, 0.7, 0.9],
    height=704,
    width=1216,
    num_frames=121,
    seed=314,
    output_path="outputs/multi-condition",
))
```

Validation checklist for multi-conditioning:

- `conditioning_media_paths` requires `conditioning_start_frames`.
- `conditioning_media_paths`, `conditioning_start_frames`, and `conditioning_strengths` must have the same length when strengths are provided.
- Strengths must be floats in `[0, 1]`.
- Start frames must be integers in `[0, num_frames - 1]`.
- Non-first video segments must start on multiples of 8 and should have `N*8+1` effective frames.
- If a video is longer than the remaining generation window, the pipeline can trim it; verify that this is acceptable before running.

## Prompt enhancement decisions

`infer` reads `prompt_enhancement_words_threshold` from the selected YAML config.

- If the threshold is `> 0` and the prompt word count is below the threshold, `infer` constructs the pipeline with `enhance_prompt=True`. That can load the configured image-caption model and LLM model and may require remote downloads/cache.
- If the threshold is `> 0` but the prompt word count is equal to or above the threshold, prompt enhancement is disabled for that run.
- If the threshold is `0` or negative in the config, prompt enhancement is disabled.

Operational guidance:

- For deterministic local runs without extra prompt-enhancer downloads, use a config with threshold `0` or a prompt long enough to exceed the threshold. Config editing/selection routes to `../../model-configs/SKILL.md`.
- For direct `LTXVideoPipeline(..., enhance_prompt=True)` behavior, route to `../../pipeline-components/SKILL.md`.
- Prompt engineering remains useful even when enhancement is enabled: write a single detailed chronological paragraph with concrete motion, camera, setting, lighting, and changes.

## Output behavior

`output_path` is treated as a directory. `infer` creates it with parents if needed. It then writes one file per batch item:

- `image_output_<batch>_<prompt-fragment>_<seed>_<height>x<width>x<frames>_<index>.png` for one-frame output.
- `video_output_<batch>_<prompt-fragment>_<seed>_<height>x<width>x<frames>_<index>.mp4` for multi-frame output.

The prompt fragment is sanitized to letters/spaces, lowercased, truncated, and joined with hyphens. The index scans from `0` to `999` to avoid collisions; after that, `infer` raises `FileExistsError`. Use a fresh output directory for repeated experiments.

## Safe command construction pattern

When assembling commands in agent code, use a list and shell quoting rather than string concatenation:

```python
import shlex

cmd = [
    "python", "inference.py",
    "--prompt", user_prompt,
    "--pipeline_config", config_path,
    "--height", str(height),
    "--width", str(width),
    "--num_frames", str(num_frames),
]
print(shlex.join(cmd))
```

Never interpolate raw prompts, paths, or negative prompts into a shell command. Prefer `subprocess.run(cmd, check=True)` with a list when actually running generation.

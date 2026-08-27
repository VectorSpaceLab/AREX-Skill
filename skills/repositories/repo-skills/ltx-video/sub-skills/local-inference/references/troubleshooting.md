# Local Inference Troubleshooting

Use this when LTX-Video CLI or `infer(InferenceConfig)` runs fail before, during, or after generation. For YAML-field errors route to `../../model-configs/SKILL.md`; for direct component assertions route to `../../pipeline-components/SKILL.md`.

## Quick triage

1. Run the root environment checker if available, then run the command builder for static validation.
2. Inspect the selected YAML with `../../model-configs/scripts/inspect_ltxv_config.py` before any heavy run.
3. Decide whether checkpoint/text-encoder/upscaler/prompt-enhancer downloads are allowed.
4. Confirm the backend: full local generation is intended for CUDA or supported MPS; CPU-only runs can be impractically slow.

## Missing dependencies or inference extras

Symptoms:

- `ModuleNotFoundError` for base dependencies such as `diffusers`, `transformers`, `sentencepiece`, `huggingface_hub`, `einops`, or `timm`.
- `ModuleNotFoundError` for inference media dependencies such as `imageio`, `av`, or `torchvision`.
- `python inference.py --help` fails before printing flags.
- Media read/write errors before model generation begins.

Likely causes:

- The active Python environment does not contain the `ltx-video` distribution and its base dependencies.
- The package was installed without the `[inference]` extra.

Fix:

```bash
python -m pip install "ltx-video[inference]"
# or, from a checkout intended for editing:
python -m pip install -e ".[inference]"
```

Then rerun a help/preflight check rather than starting full generation immediately. Treat a help failure as an environment problem first, not as an inference-argument problem.

## Model download and cache failures

Symptoms:

- Hugging Face errors while resolving a `.safetensors` filename;
- long stalls before pipeline construction;
- missing `ltxv-spatial-upscaler-0.9.8.safetensors` for multi-scale configs;
- offline failures even though the YAML filename looks correct.

Facts:

- `infer` treats a `checkpoint_path` that is not an existing local file as a filename to download from the `Lightricks/LTX-Video` Hugging Face model repo.
- `spatial_upscaler_model_path` is handled similarly for multi-scale configs.
- Text encoder and prompt-enhancer fields are loaded through `transformers` using their configured names or local paths.

Fixes:

- Use local filesystem paths in the YAML for offline runs.
- Disable prompt enhancement in the YAML with `prompt_enhancement_words_threshold: 0` if prompt-enhancer model downloads are not allowed.
- Validate the YAML with `../../model-configs/scripts/inspect_ltxv_config.py` before retrying.
- Do not treat a network/download failure as a CLI syntax issue.

## FP8 / Q8 kernel failures

Symptoms:

- `ValueError: Q8-Kernels not found. To use FP8 checkpoint, please install Q8 kernels ...`
- import failure for `q8_kernels.integration.patch_transformer`.

Cause: a config uses `precision: float8_e4m3fn`. LTX-Video's FP8 path imports external Q8 kernels that are not installed by the base package or `[inference]` extra.

Fix:

- Prefer the matching bfloat16 config unless the user explicitly has compatible hardware and the external Q8 kernels installed.
- Route config choice to `../../model-configs/SKILL.md`.

## Conditioning argument errors

Symptoms and fixes:

| Error fragment / symptom | Likely cause | Fix |
| --- | --- | --- |
| `conditioning_start_frames must also be provided` | Media paths were supplied without start frames. | Add one start frame per media item. |
| `must have the same length` | Paths, strengths, and starts are not parallel lists. | Count every list; omit strengths entirely to default all to `1.0`. |
| `All conditioning strengths must be between 0 and 1` | Strength outside valid range. | Clamp or choose a deliberate soft/hard conditioning value. |
| `All conditioning start frames must be between 0 and ...` | Start frame is negative or beyond output frame count. | Use zero-based target frames inside `[0, num_frames - 1]`. |
| Assertion around `media_frame_number % 8 == 0` | Non-first video sequence is not aligned to the latent temporal factor. | Move non-first video segment start to a multiple of 8. |
| Assertion around `n_frames % 8 == 1` | Video conditioning segment frame count is not `N*8+1`. | Pre-trim or pad segment to 9, 17, 25, ... frames. |

Use `../scripts/build_inference_command.py` to catch static list/range errors before running generation.

## Dimension and frame surprises

Symptoms:

- Logs report padded dimensions different from requested dimensions.
- Memory usage is higher than expected.
- Output is cropped to requested dimensions even though generation used a larger tensor.

Cause: `infer` pads height/width to multiples of 32 and `num_frames` to `N*8+1` before calling the pipeline, then crops back.

Fix:

- Prefer dimensions already divisible by 32.
- Prefer frame counts already equal to `N*8+1`, such as 1, 9, 17, 25, 33, 49, 121, or 257.
- Use the command builder to see padding warnings.

## Media decoding and preprocessing failures

Symptoms:

- `imageio` cannot open or count frames in a conditioning/input video.
- FFmpeg or codec errors occur while reading `.mp4`, `.avi`, `.mov`, or `.mkv`.
- PIL cannot open an image or the image mode is incompatible.
- A video conditioning segment fails after loading because its frame count or target placement is invalid.

Fix:

- Convert videos to a common MP4/H.264 file that `imageio` can read.
- Convert still images to RGB PNG or JPEG.
- Keep conditioning videos short and pre-trimmed to `N*8+1` frames when possible.
- Align non-first video conditioning start frames to multiples of 8 and ensure the segment fits inside `num_frames`.
- Remember that non-video extensions are treated as still images by `load_media_file`.

## Prompt enhancement downloads or unexpected prompt changes

Symptoms:

- Additional caption/LLM model downloads start even though only an LTX checkpoint was expected.
- Output behavior differs from the literal prompt.
- Prompt enhancement tests or runs are slow.

Cause: `infer` enables prompt enhancement when `prompt_enhancement_words_threshold > 0` and the prompt word count is below the threshold.

Fix:

- Use a config with `prompt_enhancement_words_threshold: 0` for strict/offline prompt behavior.
- Or intentionally write a long enough prompt to exceed the configured threshold.
- For direct prompt-enhancer model calls, route to `../../pipeline-components/SKILL.md`.

## Output path and collision errors

Symptoms:

- Expected an exact `.mp4` path but got a file under a directory.
- `FileExistsError` after many repeated runs.

Cause: `output_path` is a directory. The output filename is generated from base type, prompt fragment, seed, resolution, and an index scanned from 0 to 999.

Fix:

- Give each experiment a fresh output directory.
- Move/rename outputs after generation if a stable final filename is required.

## Backend and memory issues

Symptoms:

- CUDA out-of-memory;
- MPS dtype/device errors;
- CPU run appears hung;
- `offload_to_cpu` warning says offloading will not occur.

Guidance:

- Select a smaller or distilled config with `../../model-configs/SKILL.md`.
- Reduce height, width, or frame count; remember padding can increase effective size.
- Use bfloat16 configs unless FP8 support is prepared.
- `offload_to_cpu` only helps on CUDA when total GPU memory is below the code threshold; it is not a CPU acceleration mechanism.
- Do not claim success from an import-only check when the requested task requires full GPU generation evidence.

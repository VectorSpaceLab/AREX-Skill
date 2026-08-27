# Inference troubleshooting

Start with one image, CPU mode, no sidecar, and `--verbose` if needed. Preserve
the first error and the exact model, tags, dimensions, threshold, and command
used; changing several variables at once hides the cause.

## Selection and path failures

| Symptom | Likely cause | Check and fix |
|---|---|---|
| `You must provide project path or model path.` | Neither project nor model was supplied. | Use `--project-path PROJECT`, or supply `--model-path MODEL` together with `--tags-path TAGS`. |
| `You must provide project path or tags path.` | Neither project nor tags were supplied. | Add `--project-path PROJECT`, or add `--tags-path TAGS`; explicit model-only mode is incomplete. |
| Click says a path does not exist or has the wrong type | CLI path validation failed before the command. | Check spelling, permissions, and whether project/model/tags are a file or directory as required. |
| Model file not found inside a project | `project.json`'s `model` value does not match the saved artifact. | Inspect the value and provide `model-MODEL_NAME.keras` or `.h5`; for a direct route use `--model-path`. |
| Tags fail to load | Missing `PROJECT/tags.txt`, wrong explicit path, or unreadable encoding. | Validate the file as UTF-8, one tag per line, with no header. |
| Direct model loads but predictions fail | Model has custom objects, unsupported format, or compiled state/dependency issue. | Try the default `--no-compile` first, then `--compile` only when the saved model needs its compile state. Keep the original model unchanged. |

When project and direct options are mixed, the direct model overrides project
model selection and direct tags override project tags. This is useful for
controlled comparisons but makes accidental vocabulary mismatches easy; use
`--verbose` and record every path.

## Folder discovery and empty runs

| Symptom | Likely cause | Check and fix |
|---|---|---|
| A directory is treated as an image and TensorFlow reports a read/decode error | `evaluate` was called without `--allow-folder`. | Add `--allow-folder`, or pass individual image files. |
| A folder run prints no image headings | No files matched `--folder-filters`, or the target is empty. | Test one file first; use the default patterns, then a narrow pattern such as `**/*.png` only if it matches your tree. The implementation splits on commas literally and does not trim spaces. |
| A nested image is missing | The custom filter does not match its extension/case, or the target was a regular file and filters were intentionally bypassed. | Confirm `Path.rglob` behavior with the exact pattern and use comma-separated patterns without spaces. |
| `evaluate-project` raises `AttributeError: module 'deepdanbooru.data' has no attribute 'load_tags_from_project'` | This is a source defect in the covered 1.0.0 revision: its native project loader calls a helper exposed under `dd.project`, not `dd.data`. | Use `evaluate TARGET --project-path PROJECT --allow-folder` for production. The bundled smoke helper tests that supported fallback and does not claim a native run. A separately reviewed native compatibility fix must record its version/source provenance. |
| `evaluate-project` and `evaluate` see different files | They use different selection controls. | Use the supported `evaluate` route with `--allow-folder` and explicit filters; native `evaluate-project` always recurses fixed case-insensitive PNG/JPG/JPEG/GIF patterns when its loader is corrected. |
| Sidecar is missing after `--save-txt` | The run failed before writing, or selection was empty. | Run without `--save-txt`, lower the threshold, and inspect stdout. The skill guard rejects empty selections rather than creating an empty sidecar. |
| Existing `.txt` changed | Native sidecar writes use `w` mode. | Native behavior overwrites; use `scripts/save_txt_guard.py` to preserve existing sidecars unless `--allow-overwrite` is explicit. |

## Shape, decoder, and vocabulary failures

1. Print or inspect `model.input_shape`. `evaluate` reads
   `model.input_shape[1]` as height and `[2]` as width and sends one normalized
   HWC image as a batch. A model with channels-first input, dynamic spatial
   dimensions, or an unusual multi-input signature is outside this helper's
   assumptions.
2. For `evaluate-project`, compare `project.json`'s `image_width` and
   `image_height` with the model input. The project route uses the JSON values,
   so a stale context can produce a shape error or silently wrong input.
3. Run [`image_preprocess_smoke.py`](../scripts/image_preprocess_smoke.py) to
   check shape and normalized range without model weights. It uses a temporary,
   deterministic PNG.
4. If an image cannot be decoded, verify its bytes and extension independently.
   The folder matcher can admit GIF while the source decoder's documented paths
   are PNG and TensorFlow-IO WebP fallback. Convert a problematic input to a
   known PNG for diagnosis.
5. Count nonblank lines in the actual tags file and compare with the model's
   output dimension. A mismatch is not corrected by changing the threshold.

## Threshold and output diagnosis

No printed tags means only that every named score was below the threshold (or
that inference failed before output). Run a single image without `--save-txt`
using thresholds such as `0.0`, `0.5`, and a deliberately high value. The
comparison is inclusive (`score >= threshold`), and output order is tag-file
order rather than score order. If scores appear plausible but names are wrong,
stop and fix model/tag alignment instead of changing the threshold.

The console prints a heading for every discovered path even when no tag passes
once the command reaches its image loop. If there is no heading, diagnose target
discovery or an earlier model/decoder exception. Native `evaluate-project` never
writes sidecars; only `evaluate` has `--save-txt`. In the covered 1.0.0 source,
native `evaluate-project` can fail before this loop because of the missing
tag-loader symbol; use the supported project-backed `evaluate` fallback above.

## CPU and compile behavior

The verified required backend is CPU. Run with default `evaluate` behavior and
avoid claiming GPU support from a successful CPU run. `--allow-gpu` merely
prevents the command from setting `CUDA_VISIBLE_DEVICES=-1`; it does not install
CUDA libraries or validate a GPU. If a GPU-specific run behaves differently,
reproduce it in the verified CPU environment before classifying the model or
input as faulty.

Compilation is not needed for prediction. `--no-compile` is the default and is
usually the safest load mode for inference-only use. Use `--compile` only when
there is a concrete reason to restore the serialized training configuration and
its optimizer/loss dependencies.

## Minimal recovery sequence

```console
python scripts/image_preprocess_smoke.py
python scripts/dummy_evaluate_smoke.py
python scripts/evaluate_project_smoke.py

deepdanbooru evaluate ONE_IMAGE \
  --project-path PROJECT \
  --threshold 0.0 \
  --verbose
```

If the three local checks pass but the real command fails, compare the real
model artifact, project context, tag count, image bytes, and exact command
flags. For a missing project or model, stop inference and hand off to
[project-data-setup](../../project-data-setup/SKILL.md); for conversion or
attribution artifacts, use [post-training-tools](../../post-training-tools/SKILL.md).

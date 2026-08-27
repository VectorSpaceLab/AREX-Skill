---
name: inference-evaluation
description: "Run and troubleshoot DeepDanbooru image-tag inference through the
  project or explicit model/tag APIs, including preprocessing, folder traversal,
  thresholds, and text outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference and evaluation

Use this sub-skill when a trained DeepDanbooru model must turn one or more
images into tags. It covers the `evaluate` and `evaluate-project` CLI commands,
the corresponding Python functions, image preprocessing, recursive folder
selection, thresholds, and optional `.txt` sidecars.

This is an inference skill, not a training or dataset-preparation procedure.
For a missing or malformed project, tag file, or dataset, use
[project-data-setup](../project-data-setup/SKILL.md) first. For model conversion
or experimental Grad-CAM output, use
[post-training-tools](../post-training-tools/SKILL.md). The bundled smoke
scripts are tiny local checks; they do not download weights, contact a network,
or read the original checkout.

## Choose the entry point

| Situation | Entry point | Important constraint |
|---|---|---|
| Use a project to select both model and tags | `deepdanbooru evaluate TARGET --project-path PROJECT` | Project must contain `project.json`, `tags.txt`, and its selected model artifact. |
| Use an explicit saved model and tag file | `deepdanbooru evaluate TARGET --model-path MODEL --tags-path TAGS` | Without `--project-path`, **both** explicit paths are required. |
| Override only one project component | `evaluate` with project plus `--model-path` or `--tags-path` | A direct model or tags path takes precedence for that component. |
| Evaluate a file or recursively every recognized image below a folder | `deepdanbooru evaluate TARGET --project-path PROJECT --allow-folder` | This is the supported 1.0.0 project-folder path. Native `evaluate-project` is not recommended because its loader calls a missing symbol; see below. |
| Call inference from Python | `deepdanbooru.commands.evaluate_image` or `evaluate` | Match the model's NHWC input dimensions and tag-output dimension. |

The `evaluate` function accepts a folder only when `allow_folder=True`. The
Click CLI defaults that flag off, so passing a directory without `--allow-folder`
is a common mistake. In the exact 1.0.0 source revision, native
`evaluate-project` calls the missing `dd.data.load_tags_from_project` symbol and
raises `AttributeError` before inference. Use `evaluate` with `--project-path`
and `--allow-folder` for production. The bundled project smoke helper exercises
that supported fallback; it does not claim a native `evaluate-project` run.

## CPU-first prerequisites

The verified environment is Python 3.11 with TensorFlow 2.21.0 and no CUDA
libraries in the verification prefix. CPU correctness is required. By default,
`evaluate` sets `CUDA_VISIBLE_DEVICES=-1` before loading the model; do not remove
that safeguard for a CPU run. `--allow-gpu` only leaves device selection
unchanged. It is an opt-in switch, **not evidence that GPU support is ready**;
GPU readiness was not verified for this repository.

Before a real run, confirm:

1. `deepdanbooru --help` and `deepdanbooru evaluate --help` work in the chosen
   environment.
2. The model is loadable and has an image input shape with height at index 1 and
   width at index 2, for example `(None, 299, 299, 3)`.
3. The tag file is newline-separated and is the exact vocabulary used for the
   model's output units.
4. Target paths exist and contain decodable images. `--save-txt` writes beside
   each image and the native helper can overwrite an existing sidecar. For a
   guarded skill-layer write, use `scripts/save_txt_guard.py`: it rejects an
   empty selected-tag list, rejects a sibling directory even with overwrite
   enabled, and requires explicit overwrite permission for regular files.

## Fast, inspectable workflow

1. Start with one known image and `--threshold 0.5`, without `--save-txt`.
2. Choose the project route or provide both explicit model and tags paths. Use
   `--verbose` when diagnosing path selection or load failures.
3. Inspect the printed scores and tag order. If no tag is printed, rerun with a
   lower diagnostic threshold such as `0.0`; do not immediately assume the
   image decoder or model failed.
4. Add `--allow-folder` and a narrow `--folder-filters` only after one-file
   inference works. Confirm the discovered set and natural ordering.
5. Enable `--save-txt` only after output is useful, and verify each sidecar.
   The native path writes selected tag names only and replaces existing files;
   use the guard helper when empty output or replacement must be refused.
6. Use the deterministic helpers when the environment or a fixture is in doubt:
   `python scripts/image_preprocess_smoke.py`,
   `python scripts/dummy_evaluate_smoke.py`, and
   `python scripts/evaluate_project_smoke.py`.

Read the focused contracts before changing a command:

- [CLI reference](references/cli-reference.md)
- [Python API reference](references/api-reference.md)
- [Image inputs and tags](references/image-inputs-and-tags.md)
- [Troubleshooting](references/troubleshooting.md)

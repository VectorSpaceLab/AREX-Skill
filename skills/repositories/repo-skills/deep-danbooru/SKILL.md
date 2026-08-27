---
name: deep-danbooru
description: "Use DeepDanbooru for anime-style image tag estimation, project and
  Danbooru-style dataset preparation, TensorFlow training, image evaluation,
  TFLite conversion, and experimental Grad-CAM workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepDanbooru

Use this repo skill when a task names DeepDanbooru or `deepdanbooru`, asks for
anime-style multi-label image tagging, or needs the package's project, dataset,
training, evaluation, TensorFlow Lite, or Grad-CAM workflows. This skill covers
the 1.0.0 source contract represented by the provenance snapshot; read it before
refreshing against a changed checkout.

## Route by task

- **Project, tags, or dataset layout**: read
  [`project-data-setup`](sub-skills/project-data-setup/SKILL.md). It owns
  `create-project`, `download-tags`, `make-training-database`, `project.json`,
  `tags.txt`, SQLite `posts`, and `images/<prefix>/` validation.
- **Training or checkpoint recovery**: read
  [`model-training`](sub-skills/model-training/SKILL.md). It owns config
  validation, supported ResNet/optimizer/loss values, data preflight,
  `train-project`, checkpoints, and `.keras` exports.
- **Tag inference or evaluation**: read
  [`inference-evaluation`](sub-skills/inference-evaluation/SKILL.md). It owns
  `evaluate`, `evaluate-project`, Python inference APIs, preprocessing,
  thresholds, recursive folders, and `.txt` sidecars.
- **Export or attribution artifacts**: read
  [`post-training-tools`](sub-skills/post-training-tools/SKILL.md). It owns
  `conv2tflite`, TFLite checks, and experimental `grad-cam` output.

Use the owning sub-skill rather than trying to make the root a full API manual.
The root references below contain cross-cutting install, CLI, and failure
information.

## Install and verify

The source package declares a base install plus a TensorFlow extra. For the
repository's documented full workflow, install the TensorFlow requirements in a
fresh compatible Python environment:

```console
python -m pip install "deepdanbooru[tensorflow]"
# Or, when the distribution's published requirements file is available:
python -m pip install -r requirements.txt
```

The package imports TensorFlow and TensorFlow I/O through its public module and
CLI paths. Do not call a CPU import proof of CUDA readiness. Start with the
bundled no-download diagnostic:

```console
python scripts/environment_smoke.py
python -m deepdanbooru --help
python -m deepdanbooru evaluate --help
```

The console entry point is `deepdanbooru`. CPU TensorFlow is the verified
correctness backend for this skill. `evaluate` is CPU-first unless
`--allow-gpu` is explicitly supplied; this source snapshot did not verify GPU
libraries or GPU performance.

## Operating boundaries

- Do not download Danbooru tags, model weights, or datasets without explicit
  network/credential approval. The bundled scripts are offline and safe by
  default.
- Do not launch full training as a smoke test. Validate the project, tags,
  SQLite schema, image paths, and package imports first; training is expensive
  and writes checkpoints/exports.
- Treat the known 1.0.0 `evaluate-project` loader defect as real: its native
  route calls the absent `dd.data.load_tags_from_project` symbol. For production
  folder inference, use `evaluate --project-path ... --allow-folder`, which uses
  the available project tag loader. The bundled project smoke helper exercises
  that fallback and does not claim an unverified native run.
- The native `evaluate --save-txt` path can fail for an empty selected-tag list
  and overwrites an existing sibling sidecar with `w`. Use the skill helper
  `sub-skills/inference-evaluation/scripts/save_txt_guard.py` when sidecar output
  needs a local safety boundary: it rejects empty selections and sibling
  directories, and requires an explicit flag to overwrite a regular file.
- Read [`repo-provenance.md`](references/repo-provenance.md) before deciding
  whether this graph is stale; package/source version drift remains possible.
- Read [`install-and-cli.md`](references/install-and-cli.md) for the full command
  map and dependency/version caveat.
- Read [`troubleshooting.md`](references/troubleshooting.md) for package-wide
  recovery.

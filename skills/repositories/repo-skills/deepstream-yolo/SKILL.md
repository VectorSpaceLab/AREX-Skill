---
name: deepstream-yolo
description: "Routes DeepStream-Yolo deployment, model conversion, multi-GIE,
  and INT8 workflows for supported YOLO-family models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepStream-Yolo

Use this skill for DeepStream YOLO deployment work: build the custom parser library, choose the right config template, convert weights to ONNX, wire multiple GIEs, and prepare INT8 calibration runs.

## Start here

1. Read `references/repo-provenance.md` if you need to know whether this skill still matches the current checkout.
2. Run `scripts/check-deepstream-toolchain.sh` before any build or runtime attempt.
3. If you want to inspect or edit the bundled runtime tree first, run `scripts/stage-runtime-tree.sh --output-dir ./deepstream-yolo-runtime`.
4. Read `references/model-family-matrix.md` before changing a config template.
5. Use the sub-skill that matches the task family:
   - `sub-skills/deployment/SKILL.md` for single-model build/run work.
   - `sub-skills/model-conversion/SKILL.md` for exporter selection and ONNX conversion.
   - `sub-skills/multi-gie/SKILL.md` for multiple primary/secondary detectors.
   - `sub-skills/int8-benchmarking/SKILL.md` for calibration and benchmark tuning.

## What this skill covers

- DeepStream app configuration for one detector.
- Custom parser library builds in `nvdsinfer_custom_impl_Yolo`.
- Model-family-specific config templates and their special knobs.
- Ultralytics-family exporter scripts and labels generation.
- Multi-GIE folder scaffolding and plugin-version updates.
- INT8 calibration image lists, OpenCV build switch, and benchmark notes.

## Shared references

- `references/installation.md` — read when you need the host prerequisites, `CUDA_VER` mapping, or a quick reminder that DeepStream runtime is separate from the Python inspection environment.
- `references/runtime-assets.md` — read when you need to know where the bundled parser source, configs, and multi-GIE layout image live.
- `scripts/stage-runtime-tree.sh` — stage the bundled parser source and configs into a fresh runtime tree before running or editing them.
- `scripts/build-nvdsinfer-plugin.sh` — stage the bundled runtime tree and build the custom parser library on a DeepStream host.
- `references/model-family-matrix.md` — read when you need to match a model family to a config template or understand the important special knobs.
- `references/troubleshooting.md` — read when build, runtime, export, or calibration errors need a cross-cutting fix.
- `references/repo-routing-metadata.json` — used by the repo-skill router during import and discovery.
- `references/repo-provenance.md` — read when checking staleness or refreshing this skill.

## Runtime expectations

- The generated skill is self-contained; do not depend on the original source checkout being preserved.
- DeepStream runtime commands need an NVIDIA DeepStream host or container; this generated skill can still document the workflow even when that SDK is absent on the current machine.
- The bundled `assets/` tree contains the parser source, build files, config templates, and multi-GIE illustration needed for self-contained runtime staging.
- The Ultralytics exporter path was inspected in a temporary Python environment with `torch`, `ultralytics`, `onnx`, `onnxslim`, and `onnxruntime` installed.

## Route summary

### `deployment`
Use this for:
- building `nvdsinfer_custom_impl_Yolo`
- choosing and editing a single-model `config_infer_primary*.txt`
- wiring `deepstream_app_config.txt` for one detector
- troubleshooting DeepStream build and runtime issues
- understanding how custom models and labels fit into the pipeline

### `model-conversion`
Use this for:
- converting Ultralytics-family `.pt` checkpoints to ONNX
- deciding which exporter script to use
- generating `labels.txt`
- understanding which upstream repos are still reference-only in this skill

### `multi-gie`
Use this for:
- duplicating the repo layout for multiple detectors
- changing `YOLOLAYER_PLUGIN_VERSION`
- wiring `secondary-gie` entries and `operate-on-gie-id`
- moving engine files into the correct `gieN/` folder

### `int8-benchmarking`
Use this for:
- enabling INT8 calibration support with `OPENCV=1`
- preparing `calibration.txt` and `INT8_CALIB_IMG_PATH`
- reading the benchmark table and tuning NMS values
- deciding when calibration is blocked by missing OpenCV dev headers

## Quick reminders

- Set `CUDA_VER` before building.
- Use the config template that matches the model family, not just the checkpoint name.
- Keep `labels.txt` synchronized with the exporter output or the class list.
- Do not treat CPU-only inspection as proof that DeepStream runtime works.

---
name: pinto-model-zoo
description: "Use PINTO_model_zoo for model catalog search, artifact
  acquisition, conversion planning, inference demo preparation, and edge/backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PINTO_model_zoo

Use this repo skill when a user asks about PINTO_model_zoo models, directories, model-format availability, download scripts, inference demos, conversion/quantization recipes, or edge/backend deployment planning.

PINTO_model_zoo is a large model artifact and conversion-script zoo, not an installable Python package. Its main operating surface is the model catalog, numbered model folders, per-folder licenses, artifact/download scripts, and heterogeneous demo/conversion scripts for TensorFlow, TFLite, ONNX, OpenVINO, TFJS, TF-TRT, CoreML, EdgeTPU, and related runtimes.

## Always apply these gates

1. **License gate:** check the selected model folder's license before use, publication, packaging, or redistribution. The conversion scripts and upstream model artifacts may have different licenses.
2. **Acquisition gate:** do not run `download*.sh`, curl/wget, Google Drive, large artifact downloads, or archive extraction without explicit user approval.
3. **Backend gate:** do not claim TensorFlow Lite, EdgeTPU, OpenVINO, TFJS, TF-TRT, CoreML, GPU, Raspberry Pi, camera, or browser behavior is verified until that concrete runtime/hardware case has actually run.
4. **Self-containment gate:** use bundled references/scripts in this skill for selection, inspection, and planning. Treat a user checkout or model folder as input data, not as documentation the skill depends on.

## Route map

| User intent | Use |
|---|---|
| Find models by task, model id/name, directory, format flag, or remarks. | `sub-skills/model-catalog/SKILL.md` |
| Understand format flags and rank candidates for a deployment target. | `sub-skills/model-catalog/SKILL.md` plus `sub-skills/model-catalog/references/catalog-selection.md` |
| Inspect a selected model folder, review download scripts, or diagnose Google Drive/network acquisition. | `sub-skills/model-acquisition/SKILL.md` |
| Plan or debug an inference/demo script, runtime imports, missing assets, camera/video replacement, or CI smoke test. | `sub-skills/inference-demos/SKILL.md` |
| Plan conversion, quantization, OpenVINO/TFLite/ONNX/CoreML/TFJS/TF-TRT/EdgeTPU deployment, or calibration requirements. | `sub-skills/conversion-and-deployment/SKILL.md` |
| Cross-cutting license, artifact, optional dependency, hardware, or staleness problems. | `references/troubleshooting.md` |

## Bundled references and scripts

- `references/model-zoo-overview.md` summarizes repository structure, format families, and operating boundaries.
- `references/model-catalog.json` is the self-contained parsed catalog snapshot used by `scripts/query_model_catalog.py`.
- `references/repo-provenance.md` records the source commit, dirty state, and evidence paths used to build this skill. Read it before deciding whether a checkout needs `refresh-repo-skill`.
- `references/repo-routing-metadata.json` is consumed by DisCo's managed repo-skills importer when import is later approved.
- `scripts/query_model_catalog.py` searches the bundled catalog by name, category, id, directory, format, or remarks.
- `scripts/check_model_folder.py` inspects a user-supplied model folder for licenses, notes, artifacts, scripts, and backend hints without executing anything.

## Minimal verification commands

These commands validate the bundled skill helpers; they do not prove any model backend runtime:

```bash
python scripts/query_model_catalog.py --query YOLOX --format ONNX --limit 5
python scripts/query_model_catalog.py --list-formats
python scripts/check_model_folder.py /path/to/a/selected/PINTO_model_zoo/model-folder --json
```

Use sub-skill helpers for script classification:

```bash
python sub-skills/model-acquisition/scripts/inspect_download_plan.py /path/to/model-folder --json
python sub-skills/inference-demos/scripts/classify_runtime_script.py /path/to/demo.py --json
python sub-skills/conversion-and-deployment/scripts/classify_conversion_script.py /path/to/convert_or_quantize.py --json
```

## Typical operating sequence

1. Use `model-catalog` to select candidate model folders and format flags.
2. Use `model-acquisition` to check license status and artifact/download availability.
3. Use `inference-demos` to plan a safe runtime smoke check or adapt a demo.
4. Use `conversion-and-deployment` only when an existing catalog artifact is missing or the user requires a changed precision, shape, target backend, or deployment package.
5. Report what is actually verified and what remains blocked by network, license, assets, optional dependencies, datasets, or hardware.

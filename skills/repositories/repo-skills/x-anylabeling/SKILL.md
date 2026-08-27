---
name: x-anylabeling
description: "Use X-AnyLabeling for AI-assisted visual and multimodal
  annotation, XLABEL conversion, model configuration, training, packaging, and
  repository workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# X-AnyLabeling

Use this repo skill when a task names X-AnyLabeling, `x-anylabeling-cvhub`,
`anylabeling`, `xanylabeling`, XLABEL JSON, AI-assisted annotation, annotation
format conversion, built-in/custom auto-labeling model configuration, or
X-AnyLabeling development workflows.

## Operating assumptions

- Public package: `x-anylabeling-cvhub`.
- Import package: `anylabeling`.
- CLI entry point: `xanylabeling`.
- Skill baseline version: `4.0.2`; read `references/repo-provenance.md` before
  deciding whether this skill is stale for a newer checkout or release.
- Python support: package metadata requires Python `>=3.11`; Python `3.12` is
  the recommended runtime in the project docs and was used for verification.
- Runtime extras are mutually exclusive by backend family: `cpu`, `gpu`,
  `gpu-cu11`, and `gpu-cu13`. Install only one ONNX Runtime backend variant in
  a single environment.
- Construction verified CPU package import, CLI/version/help, conversion
  registry, ONNX Runtime CPU provider, and no-download model-registry
  inspection. CUDA, TensorRT, model downloads, remote servers, builds, and
  training are documented but not verified by this skill.

## First install and smoke check

For ordinary CPU annotation/conversion use:

```bash
python -m pip install "x-anylabeling-cvhub[cpu]"
xanylabeling version
xanylabeling convert
```

For a local development checkout, install the matching backend extra in editable
mode instead of installing all extras:

```bash
python -m pip install -e ".[cpu]"
# or exactly one of: .[gpu], .[gpu-cu11], .[gpu-cu13]
```

Run the bundled environment checker when a future task needs to confirm package
identity, CLI availability, ONNX Runtime providers, or model-registry access:

```bash
python scripts/check_xanylabeling_env.py --show-model-registry --json
```

Read `references/install-and-runtime.md` for backend extra selection, CLI launch
behavior, config/work-dir behavior, and headless/runtime notes. Use
`references/troubleshooting.md` for cross-cutting install/import/Qt/backend
failures before drilling into sub-skill-specific troubleshooting.

## Route by task

| User intent | Load |
|---|---|
| Launch the GUI, open image/video data, configure labels/flags, edit shapes, review quality, understand XLABEL JSON, or preview labels without opening the GUI | `sub-skills/annotation-ui/SKILL.md` |
| Convert between XLABEL and YOLO/VOC/COCO/DOTA/MASK/MOT/MOTS/PPOCR/ODVG/VLM-R1-OVD, or use `LabelConverter` APIs | `sub-skills/conversion-cli/SKILL.md` |
| Choose/load built-in auto-labeling models, write custom model configs/adapters, troubleshoot downloads, ModelScope, ONNX Runtime, GPU extras, TensorRT, or remote/API models | `sub-skills/auto-labeling-models/SKILL.md` |
| Use Ultralytics training integration, inspect the hidden training worker, plan PyInstaller builds, refresh translations/resources, interpret ONNX exporter utilities, or follow contribution/test hygiene | `sub-skills/developer-workflows/SKILL.md` |

## Common cross-skill workflows

- **Create an annotated dataset for YOLO training:** use
  `annotation-ui` for manual/AI-assisted labels, `conversion-cli` to export
  YOLO/pose/segmentation labels, then `developer-workflows` to preflight
  Ultralytics training.
- **Use a custom detector in the GUI:** use `developer-workflows` only if you
  still need to export/train the model, then use `auto-labeling-models` to write
  the custom config and load it, and `annotation-ui` to validate predictions in
  XLABEL.
- **Repair a failed conversion:** use `conversion-cli` for command/API errors;
  if the source XLABEL is malformed, cross-load `annotation-ui` for schema and
  shape/group semantics.
- **Diagnose model loading:** use `auto-labeling-models` for config/download/
  backend errors, then `references/troubleshooting.md` for cross-cutting install
  or Qt runtime failures.

## Included root references and script

- `references/repo-provenance.md` — source snapshot, package version, evidence
  paths, and refresh checks.
- `references/install-and-runtime.md` — install modes, backend extras, CLI
  launch/config behavior, work directories, and safe smoke checks.
- `references/troubleshooting.md` — cross-cutting install/import, Qt/display,
  ONNX Runtime, model-cache, and optional-backend symptoms.
- `references/repo-routing-metadata.json` — structured router metadata for the
  managed DisCo repo-skills router.
- `scripts/check_xanylabeling_env.py` — safe package/CLI/backend/model-registry
  inspection helper that does not download models or launch the GUI.

## Avoid this skill when

- The task is only about a different annotation platform, a generic YOLO/SAM
  library, or an unrelated model zoo with no X-AnyLabeling integration.
- The task asks to reproduce research results, train a model at scale, or run a
  remote service without X-AnyLabeling-specific data/config/GUI involvement.
- The task requires executing GPU/TensorRT/model-download/training/build flows
  as verification; this skill can plan and troubleshoot them, but those local
  executions need task-specific approval, hardware, data, and acceptance gates.

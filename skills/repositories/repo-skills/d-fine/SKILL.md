---
name: d-fine
description: "Route D-FINE object-detection setup, training, architecture
  inspection, inference, export, and troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# D-FINE Repo Skill

Use this skill when the user is working with the D-FINE object-detection repository and needs command guidance, config selection, architecture inspection, inference/export recipes, or troubleshooting.

## Quick install and smoke check

From a D-FINE checkout, install the runtime dependencies first:

```bash
pip install -r requirements.txt
```

Add optional backend packages only when the workflow needs them:

- `pip install -r tools/inference/requirements.txt` for ONNX Runtime, TensorRT, or OpenVINO inference helpers.
- `pip install -r tools/benchmark/requirements.txt` for FLOPs or TensorRT benchmark helpers.
- `pip install onnx onnxsim` before ONNX export if they are not already available.
- `pip install matplotlib` if solver/validator imports fail during inspection.

Then run the bundled smoke probe from the checkout root:

```bash
python scripts/dfine_environment_probe.py --repo-root . --config configs/dfine/dfine_hgnetv2_n_coco.yml --build-model
```

Read [references/install-and-environment.md](references/install-and-environment.md) for the public install paths and optional backend prerequisites, and read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches the checkout.

## Route map

- **Dataset/config selection, class counts, remap policy, and YAML preflight**: use [sub-skills/data-and-configs/SKILL.md](sub-skills/data-and-configs/SKILL.md).
- **Training, `--test-only`, resume, tuning, AMP/EMA, DDP launch, and output dirs**: use [sub-skills/training-evaluation/SKILL.md](sub-skills/training-evaluation/SKILL.md).
- **Registry, model graph, deploy mode, and API inspection**: use [sub-skills/architecture-api/SKILL.md](sub-skills/architecture-api/SKILL.md).
- **PyTorch / ONNX / OpenVINO / TensorRT inference, export, benchmark, and EMA extraction**: use [sub-skills/inference-export/SKILL.md](sub-skills/inference-export/SKILL.md).

## What this skill covers

- Choosing the right D-FINE config family for COCO, Objects365, Objects365-to-COCO, custom COCO-format, CrowdHuman, and VOC workflows.
- Building and checking `train.py` commands without mixing resume and tuning.
- Inspecting `YAMLConfig`, registry-based object construction, and the D-FINE model graph.
- Generating safe command recipes for image/video inference, ONNX export, TensorRT/OpenVINO deployment, and FLOPs/latency checks.
- Diagnosing import, dependency, checkpoint, config, and backend failures using bundled troubleshooting references.

## How to use the route map

1. Start with the sub-skill that matches the user-visible task.
2. Read the linked reference there for signatures, workflows, and failure modes.
3. Run the bundled helper script if the task needs a safe command generator or a config/model probe.
4. If a workflow crosses sub-skill boundaries, hand off instead of mixing unrelated logic in one answer.

## Cross-cutting notes

- D-FINE uses `src`-based registry imports, so missing registration usually means the defining module was not imported.
- `HGNetv2.pretrained` should usually be disabled for inspection or export smoke unless the user explicitly wants pretrained lookup.
- TensorRT, OpenVINO, and benchmark workflows are optional backend paths; do not claim them as verified unless the matching runtime packages are installed.
- Keep generated runtime guidance self-contained; do not depend on opening the original repository docs at answer time.

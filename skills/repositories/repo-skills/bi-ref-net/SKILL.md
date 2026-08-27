---
name: bi-ref-net
description: "Route BiRefNet image segmentation, matting, inference,
  configuration, training, evaluation, and model-export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BiRefNet Repo Skill

Use this skill when a task involves BiRefNet / BiRefNet-style high-resolution binary image segmentation, background removal, dichotomous image segmentation, camouflaged object detection, salient object detection, or trimap-free matting.

BiRefNet is a source-code-first PyTorch repository plus Hugging Face model-family workflow. Prefer self-contained instructions and bundled helpers here instead of reopening the original repository notebooks or shell scripts.

## First checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a checkout or before refreshing it.
2. Read [references/environment-and-install.md](references/environment-and-install.md) before installing dependencies, choosing CPU/CUDA, or using the Hugging Face one-line model path.
3. Run [scripts/check_birefnet_environment.py](scripts/check_birefnet_environment.py) when you need a safe dependency/import/backend probe.
4. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, import, backend, data, and model-asset failures.

Minimal source-code inspection check for a checkout:

```bash
python scripts/check_birefnet_environment.py --repo-root /path/to/BiRefNet --check-source
```

Minimal dependency-only check:

```bash
python scripts/check_birefnet_environment.py
```

## Route map

- Use [configuration-and-data](sub-skills/configuration-and-data/SKILL.md) when the task is about `Config`, tasks/testsets, dataset roots, `im`/`gt` layout, dynamic size, loss/backbone knobs, or preflight data validation.
- Use [model-architecture](sub-skills/model-architecture/SKILL.md) when the task is about `BiRefNet`, backbones, decoder flags, checkpoint key cleanup, weight compatibility, Hugging Face loading choices, or ONNX/export planning.
- Use [inference-and-postprocessing](sub-skills/inference-and-postprocessing/SKILL.md) when the task is about image/video inference, masks, foreground refinement, alpha/comparison outputs, device selection, or adapting the notebook inference flow.
- Use [training-and-evaluation](sub-skills/training-and-evaluation/SKILL.md) when the task is about fine-tuning, `train.py`/launcher semantics, checkpoints/resume epochs, metrics, `eval_existingOnes.py`, or best-epoch selection.

## Common task routing

| User asks for... | Go to |
|---|---|
| "How do I format custom data for BiRefNet?" | `configuration-and-data` |
| "Which config fields change task, backbone, size, or losses?" | `configuration-and-data` plus `model-architecture` |
| "Load a BiRefNet checkpoint or fix state-dict key mismatches" | `model-architecture` |
| "Run background removal on images or save masks/foregrounds" | `inference-and-postprocessing` |
| "Process videos with BiRefNet" | `inference-and-postprocessing` |
| "Fine-tune from existing weights" | `training-and-evaluation` plus `configuration-and-data` |
| "Evaluate predictions or choose the best epoch" | `training-and-evaluation` |
| "Convert to ONNX or plan deployment" | `model-architecture` with inference constraints from `inference-and-postprocessing` |

## Verification-friendly helpers

Use these bundled scripts before recommending expensive work:

- `scripts/check_birefnet_environment.py --check-source --repo-root <checkout>` checks dependencies, source imports, torch backend visibility, state-dict prefix cleanup, and patch helpers.
- `sub-skills/configuration-and-data/scripts/birefnet_dataset_check.py` checks custom dataset `im`/`gt` pairing without training.
- `sub-skills/model-architecture/scripts/birefnet_model_probe.py` verifies checkpoint-prefix cleanup and can instantiate `BiRefNet(bb_pretrained=False)` when memory is acceptable.
- `sub-skills/inference-and-postprocessing/scripts/birefnet_image_infer.py --dry-run` plans image mask outputs without loading model weights.
- `sub-skills/training-and-evaluation/scripts/birefnet_metric_smoke.py` verifies metric dependencies with tiny masks.

## When not to use this skill

Do not use this skill as the primary guide for SAM, YOLO, Detectron2, MMSegmentation, or another segmentation package unless the user is specifically comparing those tools to BiRefNet. Do not use it for generic PyTorch training advice that does not involve BiRefNet config, checkpoints, data layout, or metrics. Use a deployment-specific skill when the user asks primarily about TensorRT, GGUF, web APIs, or a third-party serving platform rather than BiRefNet itself.

## Dependency and backend stance

- The repository documents Python 3.11 and `pip install -r requirements.txt` with PyTorch >= 2.5.0.
- CPU is enough for import checks, config/data validation, metric smoke tests, patch-helper probes, and CPU foreground refinement.
- Practical full-resolution inference, GPU refinement, DDP/Accelerate training, and ONNX GPU conversion are CUDA-sensitive. Do not claim they are locally verified unless you run an explicit backend check with model/data assets.
- The README's `AutoModelForImageSegmentation.from_pretrained(..., trust_remote_code=True)` path requires `transformers`, which is not listed in the repository requirements file.

## Self-containment rules

- Use bundled references/scripts instead of telling future agents to open source notebooks or shell scripts.
- When a helper needs source modules, pass an explicit `--repo-root` for the user's current BiRefNet checkout or use a Hugging Face model path; never depend on the checkout that produced this skill.
- Do not run long training, model/data downloads, Slurm jobs, cleanup scripts, or ONNX conversion unless the user explicitly provides assets, hardware, and approval.

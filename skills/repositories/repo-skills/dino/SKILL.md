---
name: dino
description: "Routes DINO DETR object-detection setup, COCO data validation,
  CUDA deformable-attention preparation, training, evaluation, inference,
  visualization, and bounded benchmarking tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DINO repo skill

Use this skill for the official IDEA Research implementation of **DINO: DETR
with Improved DeNoising Anchor Boxes for End-to-End Object Detection**. It is a
router and operating guide for a DINO checkout or compatible installed runtime;
it is not a replacement for model weights, COCO data, or the PyTorch/CUDA
runtime.

## Route by task

- **Prepare or diagnose an environment, COCO layout, model shape, or compiled
  deformable-attention operator:** read
  [data-model-setup](sub-skills/data-model-setup/SKILL.md).
- **Train, fine-tune, resume, choose scale/backbone, or construct a
  single/distributed/Submitit command:** read
  [training](sub-skills/training/SKILL.md).
- **Evaluate a checkpoint, run one custom image, interpret boxes, visualize, or
  measure GFLOPS/FPS:** read
  [inference-evaluation](sub-skills/inference-evaluation/SKILL.md).

For a task spanning routes, run setup first, then training or inference. Do not
start a long job until the setup route has recorded its data, config, package,
and backend gates.

## Minimum prerequisites

The upstream project documents Python 3.7.3, PyTorch 1.9.0, and CUDA 11.1 as
its historical reference environment. Keep `torch` and `torchvision` on a
compatible release family and compile the custom operator against the same
CUDA family. A verified modern inspection combination used Python 3.11,
PyTorch 2.5.1+cu121, torchvision 0.20.1+cu121, CUDA 12.1 `nvcc`, GCC 12.4,
and an A100 (compute capability 8.0). Treat that as evidence for one tested
combination, not a universal compatibility promise.

Install the documented runtime requirements in an isolated environment:

```bash
python -m pip install -r requirements.txt
python -m pip check
```

For standard DINO deformable attention, verify `torch`, `torchvision`,
`pycocotools`, and `MultiScaleDeformableAttention`. Add `panopticapi` only
for panoptic/mask workflows. Read
[data-model-setup environment guidance](sub-skills/data-model-setup/references/environment.md)
before compiling CUDA code.

## Safe first checks

From the target project root, run the bundled read-only probes before changing
anything:

```bash
python skills/disco/dino/sub-skills/data-model-setup/scripts/check_dino_environment.py \
  --require-extension --require-coco --pip-check
python skills/disco/dino/sub-skills/data-model-setup/scripts/validate_coco_layout.py \
  /path/to/COCODIR --split val
```

The first command checks imports and reports backend status; it does not install
or build. The second checks JSON references and paths without downloading,
copying, deleting, or rewriting data. Add `--require-cuda` and `--smoke-cuda`
only when a free visible GPU is intentionally selected.

## Cross-cutting rules

- Pair 4-scale checkpoints with `DINO_4scale.py` and 5-scale checkpoints with
  `DINO_5scale.py`; also match backbone and class vocabulary.
- `num_classes` follows the repository's maximum category-ID-plus-one
  convention. For custom data, preserve the documented denoising rule
  `dn_labelbook_size >= num_classes + 1`.
- DINO's deformable encoder/decoder depends on the compiled CUDA operator. A
  CPU import or config parse is not evidence that the CUDA model path works.
- `batch_size` is per process. Compute the effective global batch before
  comparing runs or changing learning-rate assumptions.
- `--resume` restores a full training state; `--pretrain_model_path` performs
  partial model initialization and is the fine-tuning path.
- Do not download checkpoints/data, launch Slurm jobs, mutate dataset roots,
  or start long training from the bundled helper scripts by accident.

For install/import/config failures, read [shared troubleshooting](references/troubleshooting.md).
For provenance or refresh decisions, read [repository provenance](references/repo-provenance.md).
For a reviewable evaluation command, use [the bundled evaluator planner](scripts/run_dino_eval.py); for a reviewable operator build, use [the bundled extension wrapper](scripts/build_dino_extension.py). Both print commands and require explicit launch flags for side effects.

## Verification boundary

This skill was integrated from source commit `d84a491d41898b3befd8294d1cf2614661fc0953`.
The prepared environment passed package imports, `pip check`, config/API smoke
checks, CUDA allocation on a selected free A100, and compilation/import of the
custom operator. Full COCO training/evaluation, downloaded checkpoints,
pretrained Swin/ConvNeXt assets, the numerical operator test, and active Slurm
submission were intentionally deferred; preserve those limits in any result
report.

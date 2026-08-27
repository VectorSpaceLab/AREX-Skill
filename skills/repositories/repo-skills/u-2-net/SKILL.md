---
name: u-2-net
description: "Route U-2-Net salient object detection, human segmentation,
  portrait generation, architecture, and training-preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# U-2-Net Repo Skill

Use this skill when the task is about U-2-Net/U2NET PyTorch workflows: salient object detection masks, human/person segmentation, portrait drawing, portrait compositing, model architecture/checkpoints, dependency checks, or DUTS-style training preparation.

## First checks

- This generated skill bundles distilled U-2-Net model code and helper scripts. It does **not** bundle pretrained `.pth` weights.
- Core workflows need Python with `torch`, `torchvision`, `numpy`, `Pillow`, `scikit-image`, and usually `cv2` for portrait own-image mode.
- A typical CPU-oriented install is:

  ```bash
  python -m pip install torch torchvision numpy pillow scikit-image opencv-python matplotlib
  ```

  Choose a CUDA-enabled PyTorch install only when the user explicitly needs GPU acceleration and the host supports it.
- Run [`scripts/check_environment.py`](scripts/check_environment.py) when debugging imports or optional CUDA.
- Read [model weights](references/model-weights.md) before choosing a checkpoint.
- Read [repo provenance](references/repo-provenance.md) when checking staleness against a new checkout.

## Route map

| User task | Read |
| --- | --- |
| Choose between `U2NET`, `U2NETP`, side outputs, checkpoint compatibility, or run a tiny architecture smoke test. | [`sub-skills/model-architecture/SKILL.md`](sub-skills/model-architecture/SKILL.md) |
| Run generic saliency masks with `u2net`/`u2netp`, human/person segmentation, or troubleshoot mask outputs. | [`sub-skills/salient-object-inference/SKILL.md`](sub-skills/salient-object-inference/SKILL.md) |
| Run portrait drawing, own-photo face-crop portrait inference, Haar cascade handling, or sigma/alpha composites. | [`sub-skills/portrait-workflows/SKILL.md`](sub-skills/portrait-workflows/SKILL.md) |
| Validate DUTS-style data layout, inspect preprocessing, or plan bounded retraining. | [`sub-skills/data-and-training/SKILL.md`](sub-skills/data-and-training/SKILL.md) |
| Optional PaddleHub/Gradio web demo. | [`references/optional-demos.md`](references/optional-demos.md) |

## Minimal dependency check

```bash
python scripts/check_environment.py --check-cuda
```

For architecture-only smoke testing from this skill directory:

```bash
python sub-skills/model-architecture/scripts/smoke_architecture.py --model u2netp --height 64 --width 64 --device cpu
```

For pretrained saliency, supply explicit weights:

```bash
python sub-skills/salient-object-inference/scripts/u2net_infer.py \
  --task saliency \
  --model u2netp \
  --weights PATH_TO_WEIGHTS/u2netp.pth \
  --input-dir INPUT_IMAGES \
  --output-dir OUTPUT_MASKS \
  --device cpu
```

## Cross-cutting references

- [Troubleshooting](references/troubleshooting.md): install/import, missing weights, optional CUDA/PaddleHub, script-style repo, and training safety.
- [Model weights](references/model-weights.md): checkpoint-to-workflow matrix and no-download policy.
- [Optional demos](references/optional-demos.md): PaddleHub/Gradio route and why it is not part of the minimum workflow.
- [Routing metadata](references/repo-routing-metadata.json): structured scenario placement for managed repo-skill import.

## Safety and scope

Do not start large downloads, full training, web demos, or checkpoint overwrites without explicit user approval. Use random-weight smoke flags only for dependency and plumbing checks; never present random outputs as U-2-Net predictions.

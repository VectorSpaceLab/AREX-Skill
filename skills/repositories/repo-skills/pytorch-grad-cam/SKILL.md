---
name: pytorch-grad-cam
description: "Guides PyTorch grad-cam workflows for class activation maps,
  model/task adaptation, CAM metrics, method selection, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Grad-CAM Repo Skill

Use this repo skill for the `grad-cam` Python distribution, imported as
`pytorch_grad_cam`, when a task involves class activation maps, pixel
attribution, PyTorch vision explainability, CAM method selection, custom model
targets, reshape transforms, ROAD/ARCC metrics, Deep Feature Factorization, or
troubleshooting CAM outputs.

## Package identity and installation

- Install package: `pip install grad-cam`
- Import package: `import pytorch_grad_cam`
- Core dependency family: PyTorch, TorchVision, NumPy, OpenCV, ttach,
  matplotlib, SciPy, scikit-learn, Pillow, tqdm.
- Optional workflow dependencies: `timm` for Swin examples,
  `transformers` for CLIP/HuggingFace examples, vendor packages for HPU.

Minimal public import check:

```bash
python - <<'PY'
from importlib.metadata import version
from pytorch_grad_cam import GradCAM, ScoreCAM, AblationCAM, FinerCAM
print("grad-cam", version("grad-cam"))
print(GradCAM, ScoreCAM, AblationCAM, FinerCAM)
PY
```

For a safe diagnostic that does not download models, run
[`scripts/check_grad_cam_environment.py`](scripts/check_grad_cam_environment.py).
For method names and installed signatures, run
[`scripts/inspect_cam_methods.py`](scripts/inspect_cam_methods.py).

Read [`references/package-overview.md`](references/package-overview.md) for the
verified package surface, dependencies, and workflow map. Read
[`references/troubleshooting.md`](references/troubleshooting.md) when install,
import, optional dependency, device, or source-independence issues appear. Read
[`references/repo-provenance.md`](references/repo-provenance.md) before deciding
whether this skill is stale for another checkout.

## Route map

### Core CAM generation

Read [`sub-skills/cam-generation/SKILL.md`](sub-skills/cam-generation/SKILL.md)
when the task asks to produce Grad-CAM/CAM heatmaps for a PyTorch classifier,
choose target layers, target classes, smoothing options, guided backpropagation,
batch behavior, or a safe single-image smoke test.

Common triggers: "run GradCAM on my model", "overlay a heatmap", "why is my CAM
blank", "use aug_smooth/eigen_smooth", "combine CAM with guided backprop", or
"test GradCAM without downloading ImageNet weights".

### Model/task adaptation

Read
[`sub-skills/model-task-adaptation/SKILL.md`](sub-skills/model-task-adaptation/SKILL.md)
when activations or outputs are not ordinary CNN classification logits: ViT,
Swin, CLIP, HuggingFace vision models, object detection, semantic segmentation,
embeddings/similarity, custom target callables, `reshape_transform`, or
`FasterRCNNBoxScoreTarget` / `SemanticSegmentationTarget`.

### Metrics, evaluation, and factorization

Read
[`sub-skills/metrics-and-evaluation/SKILL.md`](sub-skills/metrics-and-evaluation/SKILL.md)
for ROAD metrics, confidence-change metrics, ARCC, RefineCAM,
Deep Feature Factorization, or tasks that compare/tune explanations rather than
only creating one heatmap.

### Method and API selection

Read [`sub-skills/methods-and-api/SKILL.md`](sub-skills/methods-and-api/SKILL.md)
for expert method tradeoffs, installed class signatures, lifecycle/context
manager behavior, method-specific gotchas, device/backends, FinerCAM,
SegEigenCAM, ShapleyCAM, KPCA-CAM, AblationCAM variants, or low-level API
questions.

## Operating rules

1. Build workflows around a user's model, input tensor, target layer(s), and
   target scalar(s). CAM methods explain a scalar output with respect to a
   spatial activation tensor.
2. Do not rely on original repository examples, notebooks, or images at
   runtime. Use the bundled references and scripts in this skill tree.
3. Prefer safe synthetic checks before downloading pretrained weights or large
   datasets. The bundled smoke scripts use tiny in-memory models and tensors.
4. Treat `ScoreCAM` and `AblationCAM` as potentially expensive because they use
   many forward passes; set `cam.batch_size` deliberately.
5. Use a `with CAMClass(...) as cam:` block when possible so hooks are released.
6. Keep backend claims precise: CPU verifies the core API; CUDA/MPS/HPU require
   matching framework/vendor runtimes for real device execution.
7. If a task needs CLIP/Swin/HuggingFace or external pretrained models, surface
   the optional dependency and network/model-cache requirement before running.

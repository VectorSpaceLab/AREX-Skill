# FastReID inference workflows

This reference covers safe model construction and feature extraction patterns. It intentionally avoids training, dataset downloads, model downloads, and deployment/export workflows.

## CPU-safe model dry-run

Use this pattern when you need to prove that a config can construct a model and accept an image-shaped tensor without requiring CUDA, datasets, checkpoints, or downloads:

```python
import torch
from fastreid.config import get_cfg
from fastreid.modeling import build_model

cfg = get_cfg()
# Optionally merge a user-supplied config here.
cfg.defrost()
cfg.MODEL.DEVICE = "cpu"
cfg.MODEL.BACKBONE.PRETRAIN = False
cfg.MODEL.HEADS.NUM_CLASSES = max(int(cfg.MODEL.HEADS.NUM_CLASSES), 1)
cfg.freeze()

model = build_model(cfg)
model.eval()
images = torch.rand(1, 3, 256, 128, dtype=torch.float32)
with torch.no_grad():
    features = model(images)
print(tuple(features.shape))
```

Expected behavior for a standard Baseline/EmbeddingHead recipe is a 2-D tensor `(batch, feature_dim)`. A verified Baseline CPU smoke produced `(1, 2048)`.

Use bundled `scripts/model_forward_smoke.py` for this workflow. It overrides the device and pretrain flag by default and prints model/config metadata plus the output shape.

## DefaultPredictor-style behavior

FastReID's `DefaultPredictor(cfg)` pattern performs these steps:

1. Clone and defrost the config.
2. Force `MODEL.BACKBONE.PRETRAIN = False`.
3. Build the model with `build_model(cfg)`.
4. Set the model to eval mode.
5. Load `cfg.MODEL.WEIGHTS` using `Checkpointer(model).load(...)`.
6. Accept a tensor shaped `(B, C, H, W)`, move it to the model device, run no-grad inference, and return CPU features.

Important distinction:

- `build_model(cfg)` only constructs modules and moves them to the device.
- `Checkpointer.load(path)` loads weights.
- `cfg.MODEL.WEIGHTS` is meaningful for predictor/trainer/checkpointer flows, not for bare construction.

For safe operating scripts, do not let a config silently trigger checkpoint or pretrain downloads. Clear or ignore `MODEL.WEIGHTS` unless the user explicitly supplies a local checkpoint, and set `MODEL.BACKBONE.PRETRAIN=False` unless the task is explicitly about using pretrained backbone initialization.

## Demo-style single-image preprocessing

The feature demo pattern expects an OpenCV-style image array and converts it for the model:

1. Read or receive a BGR image array shaped `(H, W, 3)`.
2. Convert BGR to RGB with `image[:, :, ::-1]`.
3. Resize to `(width, height)` derived from `cfg.INPUT.SIZE_TEST`, where the config value is `[height, width]`.
4. Convert to `float32`.
5. Transpose from HWC to CHW.
6. Add a batch dimension to obtain `(1, 3, height, width)`.
7. Feed the tensor to a model/predictor in eval mode.
8. Optionally apply `torch.nn.functional.normalize(features, dim=1)` for cosine-similarity feature use.

Bundled `scripts/feature_extraction_smoke.py` implements this path without importing any local demo module. It can use a synthetic image for dry-runs, or a user-supplied local image if OpenCV is available.

## Checkpoint expectations

A typical FastReID model checkpoint is a local `.pth` file readable by `torch.load` through FastReID's `Checkpointer`. Common checkpoint layouts include a top-level `"model"` state dictionary plus optional trainer state. Checkpointer-compatible loading reports missing, unexpected, or incorrect-shape keys.

Safe rules for future agents:

- Treat model-zoo weights as external artifacts; do not assume they are present.
- Require an explicit local path for reproducible inference.
- Refuse or pause before loading URLs if the user did not authorize network access.
- If using a classification checkpoint with a different number of identities, expect classifier weight shape mismatches. ReID feature extraction may still be possible if backbone/head feature layers load, but the mismatch must be reported.
- Keep the runtime device consistent: CPU checkpoint loading is fine, but the model and input tensor must be on the same device during forward.

## Feature extraction with and without weights

### Without weights

A no-weight feature smoke validates preprocessing, config merging, model construction, and tensor shape. It does **not** validate semantic ReID quality.

Recommended use:

```bash
python scripts/feature_extraction_smoke.py --repo-root /path/to/fastreid-source --dry-run
```

Expected signal: the script prints the preprocessed tensor shape and an output feature shape. It should also state that no checkpoint was loaded.

### With a local checkpoint

Use a local checkpoint only when the user provides one:

```bash
python scripts/feature_extraction_smoke.py \
  --repo-root /path/to/fastreid-source \
  --config-file /path/to/user_config.yml \
  --image /path/to/image.jpg \
  --weights /path/to/model.pth
```

Expected signal: the script loads the checkpoint, preprocesses the image, runs eval inference, and prints output and normalized feature shapes.

## Rank/rerank utility snippets

Rank metric import:

```python
from fastreid.evaluation.rank import evaluate_rank
cmc, all_ap, all_inp = evaluate_rank(
    distmat, q_pids, g_pids, q_camids, g_camids,
    max_rank=50,
    use_metric_cuhk03=False,
    use_cython=False,  # safe pure-Python fallback
)
```

Re-ranking import:

```python
from fastreid.evaluation.rerank import re_ranking
reranked_qg = re_ranking(q_g_dist, q_q_dist, g_g_dist, k1=20, k2=6, lambda_value=0.3)
```

Evaluation loops, dataset loaders, and metric reporting for full benchmark evaluation belong to the training-and-evaluation sub-skill.

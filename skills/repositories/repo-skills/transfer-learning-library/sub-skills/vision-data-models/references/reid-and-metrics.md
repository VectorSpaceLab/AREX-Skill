# Re-identification Models, Datasets, and Metrics

This reference covers TLLib person re-identification surfaces used by domain adaptation/generalization workflows. Full Market/Duke/MSMT/MMT/SPGAN training is dataset-, GPU-, and optional-dependency-heavy; this sub-skill focuses on the installed API contracts and safe metric/model usage.

## Dataset tuple convention

Re-id datasets and metric helpers operate on image tuples:

```python
(filename_or_path, person_id, camera_id)
```

Typical split attributes exposed by dataset wrappers are `train`, `query`, and `gallery`. The wrappers inherit common checks/statistics from base dataset classes.

Common imports:

```python
from tllib.vision.datasets.reid.market1501 import Market1501
from tllib.vision.datasets.reid.dukemtmc import DukeMTMC
from tllib.vision.datasets.reid.msmt17 import MSMT17
```

Example local-only intent:

```python
market = Market1501(root="/path/to/reid-data")
train_items = market.train
query_items = market.query
gallery_items = market.gallery
```

Operational cautions:

- Market1501, DukeMTMC, MSMT17, PersonX, and UnrealPerson have external licenses or distribution constraints.
- Treat automatic download links as best-effort only; use local verified datasets for real runs.
- Query/gallery evaluation excludes same-person same-camera matches, so tiny synthetic metric cases must include same identity across different cameras.

## Re-id ResNet factories

Imports:

```python
from tllib.vision.models.reid.resnet import (
    reid_resnet18,
    reid_resnet34,
    reid_resnet50,
    reid_resnet101,
)
```

Pattern:

```python
backbone = reid_resnet50(pretrained=False)
features = backbone(images)  # 4D feature map
```

Contracts:

- `ReidResNet` modifies the final ResNet stage stride for higher-resolution feature maps.
- The forward pass returns feature maps rather than classifier logits.
- `pretrained=True` downloads ImageNet weights through Torch's model URL mechanism; avoid it in smoke tests and offline environments.
- These factories rely on legacy TorchVision `model_urls` availability. If imports fail, use the compatibility guidance in `troubleshooting.md`.

## `ReIdentifier`

Import:

```python
from tllib.vision.models.reid.identifier import ReIdentifier
```

Pattern:

```python
backbone = reid_resnet50(pretrained=False)
model = ReIdentifier(backbone, num_classes=751, finetune=True)

model.train()
class_logits, raw_features = model(images)

model.eval()
embeddings = model(images)  # bottleneck features for retrieval/evaluation
```

Contracts:

- The default pool layer is adaptive average pooling plus flatten.
- If no custom bottleneck is given, a `BatchNorm1d(backbone.out_features)` bottleneck is used.
- The final classification head has no bias and is initialized with small normal weights.
- `features_dim` reports the dimension before the final classifier head.
- `get_parameters(base_lr=1.0, rate=0.1)` returns LR groups; with `finetune=True`, the backbone uses `rate * base_lr`.

## Re-id losses and distance helpers

Imports:

```python
from tllib.vision.models.reid.loss import (
    pairwise_euclidean_distance,
    hard_examples_mining,
    CrossEntropyLossWithLabelSmooth,
    TripletLoss,
    TripletLossXBM,
    SoftTripletLoss,
    CrossEntropyLoss,
)
```

CPU-safe helpers:

```python
dist = pairwise_euclidean_distance(features_a, features_b)
```

Training losses:

- `CrossEntropyLossWithLabelSmooth(num_classes, epsilon=0.1)` consumes logits `(N, C)` and integer labels `(N,)`.
- `TripletLoss(margin, normalize_feature=False)` consumes feature vectors `(N, F)` and identity labels `(N,)`.
- `TripletLossXBM` adds external memory-bank features and labels.
- `SoftTripletLoss` supports teacher-style soft triplet targets.
- `CrossEntropyLoss` consumes student logits and target logits of the same shape.

Important caveat: some legacy loss constructors call `.cuda()` internally. On CPU-only hosts, instantiate those classes only after checking CUDA availability or patching/replacing the contained PyTorch loss modules in your own training code. The CPU smoke script intentionally uses CPU-safe metric/distance helpers rather than these GPU-assuming constructors.

## Sampler

Import:

```python
from tllib.utils.data import RandomMultipleGallerySampler
```

Pattern:

```python
sampler = RandomMultipleGallerySampler(train_items, num_instances=4)
```

Contract:

- Input dataset/list elements must be `(image_path, person_id, camera_id)`.
- The sampler tries to draw multiple images per identity, preferring different cameras when available.
- If an identity has too few images, replacement sampling is used where necessary.

## Metric helpers

Imports:

```python
from tllib.utils.metric.reid import (
    cmc,
    mean_ap,
    re_ranking,
    pairwise_distance,
    evaluate_all,
    validate,
)
```

Tiny metric example:

```python
import torch
from tllib.utils.metric.reid import cmc, mean_ap

dist = torch.tensor([
    [0.10, 0.80, 0.90],
    [0.70, 0.20, 0.60],
])
query_ids = [1, 2]
gallery_ids = [1, 2, 3]
query_cams = [0, 0]
gallery_cams = [1, 1, 2]

rank_curve = cmc(dist, query_ids, gallery_ids, query_cams, gallery_cams, topk=3)
map_value = mean_ap(dist, query_ids, gallery_ids, query_cams, gallery_cams)
```

Contracts:

- `dist_mat` shape is `(num_query, num_gallery)`, where lower distance means closer match.
- `cmc` and `mean_ap` accept Torch tensors for distances and convert them to NumPy internally.
- Query matches with the same person id and same camera are filtered out.
- If no valid query remains, metric functions raise `RuntimeError("No valid query")`.
- `re_ranking(q_g_dist, q_q_dist, g_g_dist, k1=20, k2=6, lambda_value=0.3)` combines query-gallery, query-query, and gallery-gallery distances; use small `k1/k2` for tiny fixtures.

## Feature extraction and validation

`extract_reid_feature(data_loader, model, device, normalize, print_freq=200)` expects a loader yielding:

```python
(images_batch, filenames_batch, person_ids_batch, camera_ids_batch)
```

It returns a dictionary:

```python
{filename: feature_tensor}
```

`validate(val_loader, model, query, gallery, device, criterion='cosine', cmc_flag=False, rerank=False)` then:

1. switches the model to eval mode,
2. extracts features,
3. computes pairwise distance,
4. reports mAP and optionally CMC,
5. optionally re-ranks distances.

Operational cautions:

- Re-id validation can consume significant memory; pairwise distances are computed on CPU to reduce GPU pressure.
- Normalize features for cosine-style comparison.
- Do not enable ranked-result visualization in a smoke test; it writes images and requires OpenCV.

## When to route elsewhere

- For re-id domain adaptation algorithms such as MMT/SPGAN, use this reference for datasets/models/metrics, then route training-loop and loss-composition decisions to `domain-adaptation` or `translation` as appropriate.
- For re-id domain generalization method choice, use this reference for data/model surfaces, then route to `task-generalization`.

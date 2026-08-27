# Workflows

This page gives the practical flows that the `feature-extraction` sub-skill should support.

## 1) Extract embeddings from paths, numpy arrays, or tensors

### Direct API pattern

```python
from torchreid.utils import FeatureExtractor

extractor = FeatureExtractor(
    model_name='osnet_x0_25',
    model_path='/path/to/local_checkpoint.pth.tar',
    device='cpu',
    verbose=False,
)

features = extractor([
    '/data/q1.jpg',
    '/data/q2.jpg',
])
print(features.shape)   # (2, D)
```

### Input forms that work

- `['a.jpg', 'b.jpg']`
- `['a.jpg']`
- `[numpy_array_a, numpy_array_b]`
- `numpy_array_a`
- `torch_tensor_bchw`
- `torch_tensor_chw`

### Local-weight safety rule

`FeatureExtractor` may try to use pretrained weights if `model_path` is missing or invalid. For no-download flows, pass a verified local checkpoint path or build the lower-level model with `pretrained=False` and load weights manually.

## 2) Compare query and gallery images

### Minimal no-download distance flow

```python
import numpy as np
from torchreid.utils import FeatureExtractor
from torchreid.metrics import compute_distance_matrix

extractor = FeatureExtractor(
    model_name='osnet_x0_25',
    model_path='/path/to/local_checkpoint.pth.tar',
    device='cpu',
    verbose=False,
)

query_images = ['/data/q1.jpg', '/data/q2.jpg']
gallery_images = ['/data/g1.jpg', '/data/g2.jpg', '/data/g3.jpg']

q_feat = extractor(query_images)
g_feat = extractor(gallery_images)
distmat = compute_distance_matrix(q_feat, g_feat, metric='euclidean')
print(distmat.shape)  # torch.Size([2, 3])
```

### Optional evaluation

If you also know person IDs and camera IDs:

```python
from torchreid.metrics import evaluate_rank

cmc, mAP = evaluate_rank(
    distmat.cpu().numpy(),
    q_pids=np.array([0, 1]),
    g_pids=np.array([0, 1, 2]),
    q_camids=np.array([0, 1]),
    g_camids=np.array([1, 0, 2]),
    max_rank=3,
)
```

### Bundled helper command

Manifest files can keep the example completely local and explicit:

```text
# query.txt
/path/to/q1.jpg 0 0
/path/to/q2.jpg 1 1

# gallery.txt
/path/to/g1.jpg 0 1
/path/to/g2.jpg 1 0
/path/to/g3.jpg 2 2
```

```bash
python scripts/compare_embeddings.py \
  --model-name osnet_x0_25 \
  --weights /path/to/local_checkpoint.pth.tar \
  --query-list query.txt \
  --gallery-list gallery.txt
```

The helper prints the distance-matrix shape and, when labels are present on every line, CMC/mAP.

### Optional re-ranking

```python
from torchreid.utils import re_ranking

q_g = distmat.cpu().numpy()
q_q = compute_distance_matrix(q_feat, q_feat).cpu().numpy()
g_g = compute_distance_matrix(g_feat, g_feat).cpu().numpy()
reranked = re_ranking(q_g, q_q, g_g)
```

## 3) Compute model complexity

```python
from torchreid import models, utils

model = models.build_model(
    name='osnet_x0_25',
    num_classes=1,
    pretrained=False,
    use_gpu=False,
)
params, flops = utils.compute_model_complexity(model, (1, 3, 256, 128))
```

### Complexity caveat

The FLOP count is an estimate of the eval-time graph only. It is not a runtime benchmark.

## 4) Visualize ranked results

```python
from torchreid.utils import visualize_ranked_results

visualize_ranked_results(
    distmat.cpu().numpy(),
    (query_records, gallery_records),
    data_type='image',
    width=128,
    height=256,
    save_dir='visrank_out',
    topk=10,
)
```

### Record format

For image-ReID, each record should begin with `(img_path, pid, camid)`.
For video-ReID, the first element may be a list or tuple of frame paths.

## 5) Visualize activation maps

### Safe wrapper flow

```bash
python scripts/visualize_actmap.py \
  --root /path/to/reid-data \
  -d market1501 \
  -m osnet_x1_0 \
  --weights /path/to/local_checkpoint.pth.tar \
  --save-dir /tmp/visactmap_osnet_x1_0_market1501 \
  --run
```

### Recovery note

If the model does not accept `return_featuremaps=True`, choose an OSNet-family model or add that forward-argument support before running the visualization.

## 6) Smoke-test the whole feature stack

```bash
python scripts/feature_extraction_smoke.py --model-name osnet_x0_25
```

This synthetic helper should confirm:

- model construction with `pretrained=False`
- local checkpoint loading
- CPU feature extraction
- distance-matrix shape
- rank-evaluation wiring

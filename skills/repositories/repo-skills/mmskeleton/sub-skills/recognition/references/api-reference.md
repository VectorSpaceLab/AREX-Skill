# ST-GCN API and shape reference

Return to the [recognition router](../SKILL.md). For command construction use
the [CLI reference](cli-reference.md); for aliases use the [model-zoo
reference](model-zoo.md); for failures use [troubleshooting](troubleshooting.md).

## `ST_GCN_18`

The public model is constructed as:

```python
from mmskeleton.models.backbones.st_gcn_aaai18 import ST_GCN_18

model = ST_GCN_18(
    in_channels=3,
    num_class=60,
    graph_cfg={"layout": "ntu-rgb+d", "strategy": "spatial"},
    edge_importance_weighting=True,
    data_bn=True,
)
```

The constructor accepts `in_channels`, `num_class`, `graph_cfg`,
`edge_importance_weighting` (default `True`), `data_bn` (default `True`), and
additional block options such as `dropout`. The model is for classification,
not for creating skeletons from video.

### Forward contract

- Input is a five-dimensional tensor `(N, C, T, V, M)`:
  - `N`: batch size
  - `C`: input channels, normally 3 (`x`, `y`, visibility/score as supplied by
    the chosen dataset pipeline)
  - `T`: temporal sequence length
  - `V`: number of graph nodes/joints
  - `M`: number of people/instances retained per frame
- `V` must agree with `graph_cfg.layout`; do not silently pad an 18-joint
  tensor to use a 25-joint graph.
- `model(x)` returns logits with shape `(N, num_class)`. Logits are finite only
  when the input, model, and backend are valid; apply the task's chosen
  post-processing separately.
- `extract_feature(x)` returns `(output, feature)`, where `output` preserves a
  class-channel spatiotemporal representation and `feature` is the final
  256-channel representation. Their exact temporal/node sizes depend on the
  input and the model's temporal strides; use `model(x)` when only class logits
  are needed.

The bundled [tiny smoke script](../scripts/run_stgcn_smoke.py) uses a small
synthetic tensor and checks the primary forward contract without loading a
checkpoint.

## Graph layouts and strategies

`graph_cfg` is passed to `mmskeleton.ops.st_gcn.graph.Graph`.

| Layout | Joints (`V`) | Typical source |
|---|---:|---|
| `openpose` | 18 | OpenPose skeleton |
| `ntu-rgb+d` | 25 | NTU RGB+D skeleton |
| `ntu_edge` | 24 | NTU edge representation |
| `coco` | 17 | COCO keypoints |

Supported partition strategies are:

- `uniform`: one normalized adjacency slice.
- `distance`: one normalized adjacency slice for each hop in
  `range(0, max_hop + 1, dilation)`.
- `spatial`: root/close/further spatial partitions for each valid hop. With
  the defaults (`max_hop=1`, `dilation=1`) this produces three slices.

The default graph values are `layout="openpose"`, `strategy="uniform"`,
`max_hop=1`, and `dilation=1`. Unknown layouts or strategies raise a
`ValueError`. The adjacency buffer has shape `(K, V, V)`, where `K` is the
strategy-dependent spatial kernel size.

## Shape diagnosis

1. Determine `V` from the data source before choosing a graph layout.
2. Convert data to `(C, T, V, M)` per sample and batch it to `(N, C, T, V, M)`;
   do not pass `(N, T, V, C, M)` or `(N, C, V, T, M)` without an explicit
   transform.
3. Set `num_class` to the number of label classes. This controls the output
   width; it does not repair labels or make an incompatible checkpoint head
   compatible.
4. Keep `in_channels` consistent with the prepared tensor. JSON schema and
   transforms belong to [data-preparation](../../data-preparation/SKILL.md).

A layout mismatch normally appears as a matrix/reshape or adjacency shape
error during forward. A class-count mismatch may appear while loading a
checkpoint or later as an invalid loss/label contract. Fix the configuration
and data contract rather than padding or truncating joints without a documented
mapping.

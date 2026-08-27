# Det3D Model Families and Component Contracts

## Detector graph

The repository uses a single-stage graph:

```text
voxel/pillar example
  -> reader (feature encoding)
  -> backbone or pillar scatter
  -> optional neck (usually RPN)
  -> MultiGroupHead
  -> loss during training OR decode/NMS during evaluation
```

`SingleStageDetector` builds `reader`, `backbone`, optional `neck`, and
`bbox_head`. `VoxelNet` and `PointPillars` override `extract_feat` and
`forward` to adapt the voxel/pillar input contract. A model config is not a
complete input example: data pipelines must produce voxelized tensors and
anchor/target fields before the forward call.

## Family map

| User-facing family | Detector `type` | Typical reader | Typical backbone/scatter | Typical head |
| --- | --- | --- | --- | --- |
| VoxelNet | `VoxelNet` | `VoxelFeatureExtractor`, V2, V3, or `SimpleVoxel` | `SpMiddleFHD` or `SpMiddleResNetFHD` | `MultiGroupHead` |
| SECOND example | `VoxelNet` | `VoxelFeatureExtractorV3` | `SpMiddleFHD` | `RPN` + `MultiGroupHead` |
| PointPillars | `PointPillars` | `PillarFeatureNet` | `PointPillarsScatter` | `RPN` + `MultiGroupHead` |
| CBGS example | `VoxelNet` | `VoxelFeatureExtractorV3` | `SpMiddleResNetFHD` | `RPN` + `MultiGroupHead` |

There is no separate `SECOND` or `CBGS` detector class in the visible model
registry. Selecting `model.type="SECOND"` or `model.type="CBGS"` is therefore
not equivalent to selecting the corresponding example composition.

## Reader contracts

### Voxel readers

`VoxelFeatureExtractor` and `VoxelFeatureExtractorV2` are learned VFE stacks.
They receive `(features, num_voxels, coors)`, compute point-relative features,
mask padded points, and max-pool to voxelwise features. `VFEV3_ablation` and
`VoxelFeatureExtractorV3` compute simple per-voxel means; V3 returns the first
`num_input_features` means. `SimpleVoxel` reduces the first features to a
radial/height-style representation. The chosen input feature count must agree
with point records and the sparse backbone's `num_input_features`.

### Pillar reader and scatter

`PillarFeatureNet` receives `(features, num_voxels, coors)`. It adds cluster and
pillar-center decorations, plus optional point distance, masks empty pillars,
and runs PFN layers. Its `voxel_size` and `pc_range` are used to calculate
pillar centers, so they must match the voxelizer. `PointPillarsScatter` is
registered as a `BACKBONES` type even though it is a scatter stage. It receives
voxel features, `[batch,z,y,x]` coordinates, batch size, and input shape, then
creates a dense pseudo-image.

## Sparse voxel backbones

`SpMiddleFHD`, `SpMiddleFHDNobn`, `SpMiddleResNetFHD`, and `RCNNSpMiddleFHD`
are sparse-convolution components. Their import and construction depend on the
historical spconv/CUDA stack. The `ds_factor` controls spatial reduction and
must participate in `assigner.out_size_factor`. Do not claim a config executes
because its Python syntax parses when spconv or compiled custom ops are absent.

## Neck and head

`RPN` builds downsample blocks and deblocks. It requires equal-length stride,
layer-count, and filter lists; upsample scales must align. The examples pass
`num_input_features` equal to the preceding sparse/scatter output and set
`MultiGroupHead.in_channels` to the concatenated deblock channels.

`MultiGroupHead` creates one `Head` branch per task. Each branch has box and
classification 1x1 convolutions, and optionally a direction classifier when
`loss_aux` is present. With `encode_background_as_zeros=True`, classification
channels are based on foreground classes; otherwise a background channel is
included. `use_sigmoid_score` and `encode_rad_error_by_sin` alter loss/decode
semantics and must match the intended checkpoint.

## Tasks, anchors, and box coding

A task's class names determine its head class count. The target pipeline groups
anchor generators by the same ordered task partition. `TargetAssigner` generates
per-task anchors and thresholds, then assigns labels (`-1` ignore, `0`
background, positive class ids), box targets, and outside weights.

The core anchor generator options are:

- `anchor_generator_stride`: sizes, strides, offsets, rotations, optional
  velocities, class name, match thresholds;
- `anchor_generator_range`: 3D sizes and six-value ranges;
- `bev_anchor_generator_range`: BEV sizes and ranges.

`GroundBox3dCoderTorch` is common in the examples. `n_dim` describes the anchor
box dimension; `code_size` can differ when angle-vector encoding or velocity
fields are enabled. The head uses `box_coder.code_size` for regression channels
and `box_coder.n_dim` for anchor tensors. Validate both rather than assuming a
7D box for every dataset.

## Checkpoint compatibility

A Det3D trainer checkpoint is normally:

```python
{
    "meta": {"det3d_version": ..., "config": ..., "CLASSES": ...},
    "state_dict": ...,
    "optimizer": ...  # optional
}
```

The evaluator may restore `model.CLASSES` from `meta["CLASSES"]`; old
checkpoints may omit it and then rely on dataset classes. State keys can carry a
`module.` prefix. Shape mismatches in head branches are expected when class
counts, task grouping, box code, direction loss, or channel widths change.
Treat them as migration decisions, not harmless warnings.

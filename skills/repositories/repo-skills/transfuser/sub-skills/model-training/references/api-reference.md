# Training API and Model Reference

## Purpose

Use this file when editing a training command, constructing the model directly, changing a config field, selecting a fusion variant, or checking whether a tensor/checkpoint can satisfy the training API. The source modules are intentionally not runtime dependencies of this skill; this is the distilled contract from `config.py`, `data.py`, `model.py`, the four backbone files, and `point_pillar.py`.

## Imports and public constructors

From a checkout with `team_code_transfuser` on `PYTHONPATH`:

```python
from config import GlobalConfig
from data import CARLA_Data, lidar_to_histogram_features
from model import LidarCenterNet
```

The installed inspection environment successfully imported `config`, `data`, `model`, and `train`, but model construction still requires CUDA and may require cached pretrained `timm` weights.

### `GlobalConfig(root_dir='', setting='all', **kwargs)`

The constructor assigns `root_dir`, builds `train_towns`, `val_towns`, `train_data`, and `val_data` for `all` or `02_05_withheld`, does nothing for `eval`, and applies arbitrary keyword overrides with `setattr` after split construction. This makes kwargs powerful but easy to misuse: unknown names are accepted and typos do not fail fast.

### Dataset and helper APIs

- `CARLA_Data(root, config, shared_dict=None)` expects `root` to be the list of route directories built by `GlobalConfig`, not the original dataset root string. `shared_dict` is normally a `diskcache.Cache` or `None`.
- `CARLA_Data.__len__()` returns the number of enumerated current-frame sequences.
- `CARLA_Data[index]` returns the modality/label/command dictionary described in `data-format.md`.
- `lidar_to_histogram_features(lidar)` converts an XYZI point array to a `(2,256,256)` float32 BEV tensor-like NumPy array.
- `get_depth(data)`, `get_waypoints(labels, len_labels)`, `transform_waypoints`, `align`, `parse_labels`, `load_crop_bev_npy`, and `draw_target_point` are useful pure preprocessing functions. They assume the source repository's `utils.py` transforms and legacy NumPy/OpenCV behavior.

### `LidarCenterNet(config, device, backbone, image_architecture='resnet34', lidar_architecture='resnet18', use_velocity=True)`

This top-level `nn.Module`:

- stores `config`, `device`, `pred_len`, target-point and PointPillars settings;
- creates `PointPillarNet` when `config.use_point_pillars` is true;
- dispatches exact backbone strings to `TransfuserBackbone`, `LateFusionBackbone`, `GeometricFusionBackbone`, or `latentTFBackbone`;
- creates segmentation/depth decoders when `config.multitask` is true;
- creates a CenterNet-style detection head, a GRU waypoint decoder, and PID helpers.

The constructor raises on an unsupported backbone. It calls `.to(device)` for internal modules and should be given a CUDA device in the supported training path.

`forward(...)` expects:

```text
rgb, lidar_bev, ego_waypoint, target_point, target_point_image,
ego_vel, bev, label, depth, semantic,
num_points=None, save_path=None, bev_points=None, cam_points=None
```

The first two arguments are batched tensors. `ego_vel` is reshaped by the engine to `(B,1)`. `bev_points` and `cam_points` are required for geometric fusion. PointPillars requires `num_points` and raw LiDAR in the `lidar_bev` slot before the internal pillar encoder.

It returns a dictionary with waypoint, BEV, detection, and optional depth/semantic loss terms. `forward_ego` is the inference-oriented path that returns predicted waypoints and local metric boxes, but runtime CARLA integration belongs to the sibling sensor-agent sub-skill.

## GlobalConfig settings

The following class attributes are training/model-affecting settings. Values are the source defaults unless changed by CLI or kwargs:

### Input, geometry, and sequence

| Field | Default | Contract |
|---|---:|---|
| `seq_len`, `img_seq_len`, `lidar_seq_len` | `1`, `1`, `1` | Current code asserts image sequence length 1 and transformer GPTs force sequence length 1. |
| `pred_len` | `4` | Four future ego waypoints. |
| `img_resolution` | `(160,704)` | Cropped H,W image shape; returned RGB is C,H,W. |
| `img_width` | `320` | Augmentation crop-width reference; source comment requires consistency with `scale`. |
| `scale` | `1` | Image/depth/semantic preprocessing scale. |
| `lidar_resolution_width/height` | `256/256` | Histogram and detection-grid dimensions. |
| `pixels_per_meter` | `8.0` | LiDAR and label pixel conversion. |
| `lidar_pos` | `[1.3,0,2.5]` | LiDAR mounting offset used for target/waypoint transforms. |
| `camera_pos`, `camera_width`, `camera_height`, `camera_fov`, `camera_rot_0/1/2` | source values | Sensor geometry used by data/agent contracts. |
| `bev_resolution_width/height` | `160/160` | BEV loss target/output resize. |

### Augmentation, multitask, and detection

| Field | Default | Contract |
|---|---:|---|
| `use_target_point_image` | `False` | Model input setting; CLI default overwrites it to `1`. Adds a target-point channel. |
| `gru_concat_target_point` | `True` | GRU input is 4-D (delta x,y plus target x,y) instead of 2-D. |
| `augment` | `True` | Enables random rotation; `inv_augment_prob=0.1` means apply with probability 0.9. |
| `aug_max_rotation` | `20` degrees | Maximum random rotation. |
| `multitask` | `True` | Enables depth and semantic heads/losses. |
| `ls_seg`, `ls_depth` | `1.0`, `10.0` | Internal semantic/depth loss multipliers. |
| `num_class` | `7` | Semantic classes. |
| `num_dir_bins` | `12` | Detection yaw classes. |
| `bb_confidence_threshold` | `0.3` | Inference box filter. |
| `top_k_center_keypoints` | `100` | Detection decode top-k. |
| `center_net_max_pooling_kernel` | `3` | Local-max kernel. |
| `channel` | `64` | BEV feature/head channel count. |
| `fp16_enabled` | `False` | OpenMMLab head flag; no CLI mixed-precision switch is provided. |
| `bounding_box_divisor` | `2.0` | Legacy box-scale correction. |

`classes`, `classes_list`, and `converter` encode the seven semantic categories and source segmentation mapping. Do not replace them with arbitrary class order without retraining all auxiliary heads.

### PointPillars

| Field | Default | Contract |
|---|---:|---|
| `use_point_pillars` | `False` | Selects raw-point encoder in data/model. |
| `max_lidar_points` | `40000` | Fixed raw XYZI padding length. |
| `min_x`, `max_x` | `-16`, `16` | Point-pillar x range. |
| `min_y`, `max_y` | `-32`, `0` | Point-pillar y range. |
| `num_input` | `9` | Decorated feature width: raw features plus cluster/center offsets. |
| `num_features` | `[32,32]` | Dynamic PointNet MLP widths; final canvas has 32 channels. |

### Transformer/FPN architecture

| Field | Default |
|---|---:|
| `backbone` | `transFuser` |
| `img_vert_anchors`, `img_horz_anchors` | `5`, `22` |
| `lidar_vert_anchors`, `lidar_horz_anchors` | `8`, `8` |
| `n_embd`, `block_exp`, `n_layer`, `n_head` | `512`, `4`, `8`, `4` |
| `n_scale` | `4` (geometric fusion scale count) |
| `perception_output_features` | `512` |
| `bev_features_chanels` | `64` |
| `bev_upsample_factor` | `2` |
| `embd_pdrop`, `resid_pdrop`, `attn_pdrop` | `.1`, `.1`, `.1` |
| GPT init mean/std/norm | `0.0`, `.02`, `1.0` |

The training CLI's `--n_layer` default is `4`, overriding the class default of `8`. Record the CLI value in `args.txt` as the effective run setting.

### Optimization, debug, and control carry-over

`lr=1e-4`, `detailed_losses` and `detailed_losses_weights` define the aggregate loss contract. `debug=False`, `sync_batch_norm=False`, and `train_debug_save_freq=50` control diagnostic paths. PID and CARLA control fields (`turn_KP=1.25`, `turn_KI=.75`, `turn_KD=.3`, `speed_KP=5`, `speed_KI=.5`, `speed_KD=1`, `default_speed=4`, throttle/brake limits, and stuck/action-repeat values) are primarily runtime-agent settings; do not change them as a training hyperparameter without tracing their checkpoint/agent impact.

## Backbones

### `transFuser`

`TransfuserBackbone` performs multi-scale image/LiDAR transformer fusion at four encoder stages, injects optional velocity, creates a 512-dimensional fused feature, and returns an FPN tuple plus an image feature grid. It supports image/LiDAR architectures exposing the expected timm stage interface; tested examples in the source help include `efficientnet_b0`, `resnet34`, and `regnety_032`, while the implementation explicitly handles `regnet*` and `convnext*` naming differences.

### `late_fusion`

`LateFusionBackbone` runs independent timm image/LiDAR encoders and adds pooled features, with optional velocity addition. The LiDAR first convolution is rebuilt for `2*lidar_seq_len` channels, plus one when target-point image is enabled, or `num_features[-1]` plus one with PointPillars.

### `latentTF`

`latentTFBackbone` uses transformer fusion but replaces LiDAR channel 0/1 in-place with a normalized positional grid. It still receives the LiDAR tensor shape and target-point channel, and current GPT code supports sequence length 1. Do not pass a reused tensor that must retain original histogram values without cloning it.

### `geometric_fusion`

`GeometricFusionBackbone` performs image↔BEV projected correspondence fusion at up to `n_scale` stages. The loader's `lidar_bev_cam_correspondences` must provide `bev_points` and `cam_points`; these are not optional placeholders. Projection tensors encode up to five correspondences per grid cell and are sensitive to the configured image/LiDAR geometry.

## PointPillarNet contract

`PointPillarNet(num_input=9, num_features=[32,32], min_x=-10, max_x=70, min_y=-40, max_y=40, pixels_per_meter=4)` is instantiated by `LidarCenterNet` using config ranges and `pixels_per_meter=8`. Its `forward(lidar_list, num_points)` expects a batch-like iterable of padded point tensors and per-example actual counts. It:

1. slices each raw point tensor to `num_points[i]`;
2. filters points to the configured x/y range;
3. computes integer pillar coordinates and decorated 9-D features;
4. applies `DynamicPointNet`, which uses `torch_scatter.scatter_max`;
5. scatters final 32-channel features into a `(B,32,ny,nx)` canvas.

`LidarCenterNet` rotates the canvas before feeding the selected fusion backbone. A missing `torch-scatter` install, wrong raw point width, invalid counts, or a changed range changes the learned input contract.

## Architecture and checkpoint compatibility checklist

Before loading weights, match:

- backbone string and model family;
- image and LiDAR timm architecture names;
- CLI `n_layer`, velocity, target-point image, PointPillars, `multitask`, channel/anchor/resolution settings;
- number/class layout of CenterNet, semantic, depth, and waypoint heads;
- DDP `module.` key prefix convention;
- optimizer type/state and whether Zero Redundancy was used;
- exact source/version/compiled dependency family.

Use `inspect_checkpoint.py` for a read-only first pass and never use `strict=False` as a substitute for resolving missing or unexpected keys.

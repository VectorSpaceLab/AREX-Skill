# Configuration and model selection

The pipeline is a text protobuf parsed as
`TrainEvalPipelineConfig`. Keep one immutable copy of the input config with
each experiment. The training code writes its parsed serialization to
`<model-dir>/pipeline.config`.

## Config families

The repository's bundled historical recipes are identified by relative names;
use an equivalent user-visible path placeholder rather than hard-coding a
checkout location.

| Family | Representative recipes | Model graph selected |
|---|---|---|
| KITTI SECOND | `car.fhd.config`, `car.fhd.onestage.config`, `car.lite.config`, `people.fhd.config` | `VoxelNet` with `SimpleVoxel`/`SimpleVoxelRadius`, sparse middle extractors such as `SpMiddleFHD`/`SpMiddleFHDLite`/`SpMiddleFHDPeople`, and usually `RPNV2`. |
| KITTI PointPillars | `pointpillars/car/xyres_16.config` through `xyres_28.config`, `pointpillars/ped_cycle/xyres_*.config`, `pointpillars/pp_pretrain.config` | `VoxelNet` registry entry with `PillarFeatureNet`, `PointPillarsScatter`, and `RPNV2`; the architecture is PointPillars even though the top-level network class is `VoxelNet`. |
| NuScenes SECOND | `nuscenes/all.fhd.config` | `VoxelNet` with `SimpleVoxel`, `SpMiddleFHD`, and `RPNV2`. |
| NuScenes PointPillars | `nuscenes/all.pp.lowa.config`, `all.pp.mida.config`, `all.pp.largea.config`, and deprecated `all.pp.deprecated.config` | PointPillars VFE/scatter with `RPNV2`; the `deprecated` recipe uses `PillarFeatureNetOld`. |
| NuScenes multi-head | `nuscenes/all.pp.mhead.config` | `VoxelNetNuscenesMultiHead`, `PillarFeatureNetRadius`, `PointPillarsScatter`, and `RPNNoHead`. This route has additional class/order constraints. |

Recipe names are evidence of historical intent, not a guarantee that a current
backend can parse or execute them. Confirm the actual config file and commit
used for a checkpoint.

## Pipeline fields to validate

### `model.second`

The builder requires a `second_pb2.VoxelNet` message and maps these fields:

- `network_class_name`: lookup in `REGISTERED_NETWORK_CLASSES`;
- `voxel_generator`: voxel size, point-cloud range, points per voxel, and
  historical block filtering fields;
- `voxel_feature_extractor.module_class_name` and `num_filters`;
- `middle_feature_extractor.module_class_name`, input channel count,
  downsample factor, and filter lists;
- `rpn.module_class_name`, layer counts/strides, filters, upsample strides,
  input channels, group norm settings, and groups;
- `num_point_features`: must agree with prepared point arrays (recipes commonly
  use 4); it is not automatically inferred from the dataset;
- box coder, target assigner, loss, class settings, direction classifier, score
  encoding, post-center range, and NMS controls.

The builder derives a dense shape from the voxel grid and VFE output, constructs
box/target assigners, resolves the model registry, and passes all NMS/loss/RPN
parameters to the model. It requires all class-level multi-class-NMS flags to
agree and all class-level rotate-NMS flags to agree. With class-agnostic NMS
disabled, per-class NMS limits/thresholds must also agree in the builder's
assertions.

### Input readers

`train_input_reader` and `eval_input_reader` are `InputReader` messages. Validate:

- `batch_size` and `preprocess.num_workers` (training values are per GPU when
  multi-GPU training is selected);
- `dataset.dataset_class_name`;
- dataset root and generated info paths;
- database sampler path and filter/preprocessing settings;
- `preprocess.max_number_of_voxels`, especially for fp16;
- class names and the class order used by target assignment/evaluation.

Dataset generation, KITTI/NuScenes directory layouts, info files, and database
sampler artifacts belong to `data-preparation`. A config that parses but points
to missing info or database files is not runnable.

### `train_config`

The source schema contains:

| Field | Meaning / guard |
|---|---|
| `optimizer` | one of RMSProp, momentum/SGD, or Adam branches; optimizer builder uses source-specific wrappers and does not support moving average. |
| `steps` | total optimizer loop steps for the visible schedule. For historical multi-GPU scaling, divide the single-GPU count by GPU count as the README instructs. |
| `steps_per_eval` | periodic save/evaluation cadence; apply the same multi-GPU scaling rule. Must be positive for the periodic branch. |
| `save_checkpoints_secs` | declared protobuf field; source training saves at evaluation/final/error points rather than using this as a timer. |
| `save_summary_steps` | declared summary cadence; the distilled current loop uses the `display_step` CLI parameter for printed metrics, so do not assume this protobuf field controls that output. |
| `enable_mixed_precision` | historical Apex fp16 path, not modern AMP; requires compatible Apex and sparse backend. |
| `loss_scale_factor` | passed to optimizer/Apex setup; negative values select dynamic scaling in the source path. |
| `clear_metrics_every_epoch` | clears model metrics at epoch boundaries when true. |

Optimizer learning-rate messages select `multi_phase`, `one_cycle`,
`exponential_decay`, or `manual_stepping` in the source scheduler builder.
Scheduler construction receives `train_config.steps`; changing steps changes
schedule interpretation.

## Registry concepts

Registries are populated by decorators when model modules import:

- VFE: `VoxelFeatureExtractor`, `VoxelFeatureExtractorV2`, `SimpleVoxel`,
  `SimpleVoxelRadius`, `PillarFeatureNetOld`, `PillarFeatureNet`,
  `PillarFeatureNetRadius`, and `PillarFeatureNetRadiusHeight`;
- middle: `SparseMiddleExtractor`, `SpMiddleFHD`, `SpMiddleFHDPeople`,
  `SpMiddle2K`, `SpMiddleFHDLite`, `SpMiddleFHDLiteHRZ`, `SpMiddleFHDHRZ`,
  and `PointPillarsScatter`;
- RPN: `RPN`, `ResNetRPN`, `RPNV2`, and `RPNNoHead`;
- network: `VoxelNet` and `VoxelNetNuscenesMultiHead`.

Registry lookup errors mean the corresponding module was not registered or the
config name is wrong. Do not fix this by changing names until import order and
backend compatibility are understood. The model package initializer imports
the multi-head module, while `VoxelNet` itself imports the VFE, middle, RPN,
and PointPillars modules.

## Multi-head NuScenes rule

`VoxelNetNuscenesMultiHead` asserts ten classes and an `RPNNoHead`. It separates
large classes (`car`, `truck`, `trailer`, `bus`, `construction_vehicle`) from
small classes (`pedestrian`, `traffic_cone`, `bicycle`, `motorcycle`, `barrier`)
and concatenates predictions in the order expected by the target assigner.
The config's class settings must preserve that semantic mapping. The guide
explicitly requires output order to match class settings and a `feature_map_size`
for each class in custom multi-head configurations.

## Safe configuration inspection

A text-only check can be performed without detector construction:

```bash
python - <<'PY'
from pathlib import Path
from google.protobuf import text_format
from second.protos import pipeline_pb2
p = Path("<config-path>")
cfg = pipeline_pb2.TrainEvalPipelineConfig()
text_format.Merge(p.read_text(), cfg)
print("network_class_name:", cfg.model.second.network_class_name)
print("train/eval batch:", cfg.train_input_reader.batch_size,
      cfg.eval_input_reader.batch_size)
print("steps/eval:", cfg.train_config.steps, cfg.train_config.steps_per_eval)
print("mixed precision:", cfg.train_config.enable_mixed_precision)
PY
```

This validates protobuf syntax and prints selected fields only. It does **not**
validate dataset existence, sparse backend compatibility, model construction,
NMS, CUDA, or checkpoint shape compatibility. Use the generated environment's
Python and do not add a source-checkout path to published instructions.

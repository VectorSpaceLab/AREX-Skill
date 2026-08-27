# Training, builders, models, and checkpoint APIs

The following names and signatures are distilled from the source API. They are
reference contracts, not evidence that the current environment can import or
execute the detector graph.

## Conversion and construction

```python
example_convert_to_torch(example, dtype=torch.float32, device=None) -> dict
build_network(model_cfg, measure_time=False) -> torch.nn.Module
```

`example_convert_to_torch` maps floating arrays (`voxels`, `anchors`,
`reg_targets`, `reg_weights`, `bev_map`, `importance`) to the requested float
type; coordinates, labels, and point counts to int32; anchor masks to uint8;
calibration members to tensors; and leaves metadata-like values unchanged.
When `device` is omitted it selects `cuda:0`, so explicitly pass a device in
any standalone utility. It does not prove that the model accepts CPU tensors.

`build_network` builds a voxel generator, box coder, target assigner, and the
registered network. The `second_builder.build` contract is:

```python
build(model_cfg: second_pb2.VoxelNet,
      voxel_generator,
      target_assigner,
      measure_time=False)
```

It validates the protobuf type and maps every model sub-config into the
constructor. It is a legacy-backend guarded call because voxel generation,
NMS, sparse middle layers, and model imports depend on old APIs.

`input_reader_builder.build` is:

```python
build(input_reader_config, model_config, training,
      voxel_generator, target_assigner=None, multi_gpu=False)
```

It returns a `DatasetWrapper` with `__len__`, `__getitem__`, and a
`.dataset` property. The wrapper is not a data preparation tool; use the data
sub-skill to create its expected files.

## `VoxelNet` contract

The registered `VoxelNet` constructor accepts the generated/output shape,
class count, input features, VFE/middle/RPN registry names and dimensions,
normalization flags, direction/NMS settings, target assigner, loss functions and
weights, voxel generator, post-center range, and model name. The most useful
runtime methods are:

```python
update_global_step() -> None
get_global_step() -> int
clear_global_step() -> None
forward(example: dict) -> dict
predict(example: dict, preds_dict) -> dict-or-annotations
metrics_to_float() -> None
convert_norm_to_float(net) -> None
clear_metrics() -> None
clear_timer() -> None
get_avg_time_dict() -> dict
```

Training `forward` expects a prepared batch dictionary with `voxels`,
`num_points`, `coordinates`, `anchors`, labels/targets/importance and related
fields. It returns loss and prediction/metric entries including `loss`,
`cls_preds`, reduced cls/loc losses, `cared`, and optionally direction loss.
Inference calls the model's prediction path with an eval-shaped example. Do not
invent a tensor schema from the method name; route data batch preparation to the
data sub-skill.

## PointPillars and custom model classes

PointPillars is assembled through the same `VoxelNet` builder with these common
registry values:

```text
voxel_feature_extractor.module_class_name = PillarFeatureNet
middle_feature_extractor.module_class_name = PointPillarsScatter
rpn.module_class_name = RPNV2
```

The source classes expose these constructors:

```python
PillarFeatureNet(num_input_features=4, use_norm=True,
                num_filters=(64,), with_distance=False,
                voxel_size=(0.2, 0.2, 4), pc_range=(0, -40, -3, 70.4, 40, 1))
PillarFeatureNetOld(...same shape...)
PillarFeatureNetRadius(...same shape...)
PillarFeatureNetRadiusHeight(...same shape...)
PointPillarsScatter(output_shape, use_norm=True, num_input_features=64,
                    num_filters_down1=[64], num_filters_down2=[64, 64],
                    name='SpMiddle2K')
```

The exact default filter tuple is less important than the config values passed
by the builder; preserve checkpoint-compatible architecture.

`VoxelNetNuscenesMultiHead(*args, **kwargs)` is a registered subclass that
requires ten classes, an `RPNNoHead`, and class-order-compatible heads. Its
small/large head `forward` outputs are concatenated to match anchor/class
ordering. It is especially sensitive to config order and feature-map sizes.

## Optimizer and scheduler builders

```python
optimizer_builder.build(optimizer_config, net, name=None,
                        mixed=False, loss_scale=512.0)
lr_scheduler_builder.build(optimizer_config, optimizer, total_step)
```

The optimizer builder selects RMSProp, SGD with momentum, or Adam based on the
protobuf oneof, creates the historical `OptimWrapper`, assigns a unique
checkpoint name, and raises for moving-average mode. It has a source quirk:
its wrapper call uses a historical default learning rate while the schedule
controls learning-rate evolution; inspect the parsed optimizer config and log
actual values rather than assuming a modern optimizer contract.

The scheduler builder supports multi-phase, one-cycle, exponential-decay, and
manual-stepping learning-rate messages. The source-authoritative ordering is to
restore the optimizer before constructing its schedule. `total_step` is the
configured (possibly multi-GPU-adjusted) step count.

## Freeze and partial initialization

```python
freeze_params(params: dict, include=None, exclude=None) -> list
freeze_params_v2(params: dict, include=None, exclude=None) -> None
filter_param_dict(state_dict: dict, include=None, exclude=None) -> dict
```

These helpers use Python regular expressions with `match`, not glob syntax.
`freeze_params_v2` changes `requires_grad`; `filter_param_dict` filters state
keys. `train` then additionally checks matching keys and exact tensor shapes
before loading a pretrained state. Print or record the loaded-key list and
shape skips before trusting a partial initialization.

## Inference context

```python
class TorchInferenceContext(InferenceContext):
    __init__()
    _build()
    _restore(ckpt_path)
    _inference(example)
    _ctx()
```

The context is an internal adapter for the historical viewer rather than a
stable public inference API. `_build` is CUDA-only (`net.cuda().eval()`),
constructs an anchor cache, and optionally converts the network for fp16.
`_restore` requires a `.tckpt` suffix. The inspected source imports
`predict_to_kitti_label` from the training module, but that symbol is absent in
the inspected train source; therefore do not present this class as a verified
standalone inference route.

## Checkpoint API

The `torchplus.train` checkpoint functions are:

```python
latest_checkpoint(model_dir, model_name) -> str | None
save(model_dir, model, model_name, global_step,
     max_to_keep=8, keep_latest=True) -> None
restore(ckpt_path, model, map_func=None) -> None
try_restore_latest_checkpoints(model_dir, models, map_func=None) -> None
restore_latest_checkpoints(model_dir, models, map_func=None) -> None
restore_models(model_dir, models, global_step, map_func=None) -> None
save_models(model_dir, models, global_step,
            max_to_keep=15, keep_latest=True) -> None
```

Each model must expose a unique `.name`; checkpoints are `<name>-<step>.tckpt`
and `checkpoints.json` maps names to latest/all retained filenames. `save` uses
a delayed SIGINT handler to avoid incomplete index updates, but external storage
can still fail. Restore uses `torch.load` and ordinary `load_state_dict`; it is
not a config migration mechanism. Validate architecture, dtype/backend, and
checkpoint provenance first.

## Safe API evidence boundary

A Python signature or class listing can be inspected statically or with a
carefully isolated environment. It cannot establish that sparse kernels,
legacy NMS, CUDA, Apex, or a real dataset work. Keep those observations
separate in reports and user-facing answers.

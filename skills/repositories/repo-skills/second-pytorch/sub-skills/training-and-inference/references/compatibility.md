# Compatibility and guarded execution

## Status for this generated skill

The selected executable scope is CPU-safe/static guidance plus guarded legacy
detector routes. Full model import, construction, training, evaluation, and
inference are **not verified**.

| Surface | Source requirement | Current inspection implication | Claim allowed |
|---|---|---|---|
| PyTorch device | CUDA is selected automatically when available; inference context hard-codes `.cuda()` | A CUDA smoke path is available in the inspection context | Report CUDA availability only; do not infer detector success. |
| Sparse convolution | Source uses `spconv.SubMConv3d`, `SparseConv3d`, `SparseSequential`, `SparseConvTensor`, and old utility APIs | Modern spconv 2.x may import but has different compatibility surfaces | Require exact legacy symbol probe; no model execution claim. |
| Voxel generation | `second.builder.voxel_builder` imports `spconv.utils.VoxelGeneratorV2` | Current spconv 2.x inspection lacks `VoxelGeneratorV2` | Detector gate fails until a compatible stack is supplied. |
| NMS | source imports `spconv.utils.non_max_suppression`, `non_max_suppression_cpu`, and `rotate_non_max_suppression_cpu` through NMS modules | Current spconv inspection lacks the old legacy NMS symbols | Do not replace with a modern op without a separately verified port. |
| Numba | geometry, preprocessing, and legacy CUDA kernels use Numba decorators | Version/NumPy behavior can change compilation and old `np.bool` paths | Probe/import separately; do not call detector kernels as a smoke test. |
| Protobuf | text configs use generated proto modules and `text_format.Merge` | the schema is version-sensitive | Validate config parsing with the intended protobuf runtime. |
| torchvision | `rpn.py` imports `torchvision.models.resnet` | binary/version mismatch can fail before model construction | Probe import; record exact exception. |
| fp16 | source uses Apex `amp`, `opt_level="O2"`, and sparse voxel limit | Apex is optional and historical | Route only after explicit Apex/backend validation; not modern AMP. |
| NuScenes | optional `nuscenes-devkit` and local data/results | package alone does not supply data | Preserve guide advice as historical; no benchmark claim. |

The private inspection snapshot had Torch 2.3.1+cu121, spconv 2.3.8, Numba
0.57.1, NumPy 1.24.4, protobuf 3.20.3, Fire, TensorBoardX, NuScenes devkit,
scikit-image, Flask-CORS, and torchvision available; it also had an A100 CUDA
smoke pass. The same inspection found missing legacy spconv symbols and did not
accept old detector import/runtime. These are compatibility evidence, not
portable installation requirements or an execution guarantee.

## The required detector gate

Run the bundled helper before importing `second.pytorch.train` or
`second.pytorch.inference`:

```bash
python <training-skill-root>/scripts/check_legacy_backend.py --require-detector
```

The gate checks package imports and the exact sparse, voxel, NMS, and overlap
symbols referenced by this source without importing `second`, constructing a
model, launching Fire, compiling Numba kernels, or starting training. The most
important removed utilities are:

```text
spconv.utils.VoxelGeneratorV2
spconv.utils.non_max_suppression
spconv.utils.non_max_suppression_cpu
spconv.utils.rotate_non_max_suppression_cpu
```

The report also covers top-level legacy sparse classes (`SubMConv3d`,
`SparseConv3d`, `SparseSequential`, `SparseConvTensor`, `SparseModule`),
`spconv.ops.nms`, and the old `rbbox_iou` / `rbbox_intersection` utilities. If
any required name is absent, stop. Save the JSON-like report and
traceback/version data,
then choose one of these recovery paths:

1. supply a separately isolated, provenance-recorded historical environment
   that proves all symbols, the intended Torch/CUDA ABI, Numba behavior, and
   the relevant smoke checks;
2. narrow the task to static/config/CPU-safe operations and do not execute the
   detector;
3. migrate the experiment to the maintained OpenPCDet or MMDetection3D
   implementation recommended by the deprecated README, with an explicit
   checkpoint/config conversion plan.

Do not blindly install an arbitrary old wheel, monkey-patch missing symbols, or
claim that an import succeeded merely because a fallback shim was installed.

## Import layers and likely blocks

Failure can occur in layers:

1. `train.py` imports data, box, NMS, builder, and utility modules before Fire
   dispatch. A missing old spconv symbol can prevent even `--help`.
2. `voxel_builder` resolves `VoxelGeneratorV2` during import/build.
3. `second.pytorch.models.middle`, `resnet`, and `box_torch_ops` use legacy
   sparse APIs and NMS operations.
4. `VoxelNet` construction resolves registry names and compatible tensor
   dimensions.
5. real forward/evaluation additionally needs prepared dataset batches, CUDA,
   sparse kernels, Numba and evaluator behavior.

Keep the first failing layer; later errors may be consequences. In particular,
`torch.cuda.is_available()` does not skip layers 1-3.

## Source-specific caveats

- `second/pytorch/inference.py` imports `predict_to_kitti_label` from the train
  module, but the inspected train module has no such definition. Treat direct
  `TorchInferenceContext` use as blocked until the exact source revision is
  reconciled and independently tested.
- The train `evaluate` signature rejects unknown keyword arguments, while the
  README's historical usage mentions `--pickle_result`. Current source writes
  `result.pkl` itself; do not pass the stale flag.
- `mcnms_parameters_search` is an empty placeholder in the inspected source.
- The source imports `torchplus.train` utilities and uses a legacy optimizer
  wrapper. Do not assume current PyTorch optimizer/scheduler state is
  checkpoint-compatible.
- A CPU-safe protobuf parse tests syntax only. It does not test VoxelGenerator,
  sparse layers, NMS, dataset paths, checkpoint loading, or CUDA.

## What to record for a future compatible environment

Record package versions without machine-specific paths, the exact source commit,
CUDA/driver compatibility, the four required spconv symbols, Numba CUDA
availability, protobuf config parse, torchvision import, and a minimal model
construction/forward/evaluate result if and only if those were actually run.
Keep failed and skipped checks explicit. A new environment should not overwrite
a user's working environment without permission.

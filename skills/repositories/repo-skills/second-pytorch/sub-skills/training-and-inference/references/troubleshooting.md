# Training and inference troubleshooting

Use the narrowest applicable section, preserve the first traceback, and do not
claim a route recovered until the exact blocked operation has been rerun in a
compatible environment.

## Install and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: fire`, `torchplus`, or generated protobuf module | no package metadata; a separately supplied checkout is not importable; missing dependency | use an isolated environment, make the separately supplied checkout importable only for that run, and install only evidence-backed dependencies. Do not publish a private path or environment name. |
| `ImportError` for `VoxelGeneratorV2` | modern spconv does not expose the old voxel API | run `check_legacy_backend.py --require-detector`; stop the detector route and obtain a proven legacy stack or migrate. |
| `ImportError` for `non_max_suppression*` | old spconv NMS utilities removed | do not alias `spconv.ops.nms` without a port and numerical validation. Treat as a required detector-backend block. |
| `torchvision` binary/operator mismatch | torchvision and Torch ABI mismatch; `rpn.py` imports torchvision early | compare Torch/torchvision versions, repair only an isolated environment, then rerun the non-invasive probe. A torchvision import alone is not detector proof. |
| protobuf descriptor/text parse error | incompatible protobuf runtime or malformed config | use the intended generated-proto runtime, run the text-only parse in `configuration.md`, and report the first field/line error. Do not hand-edit generated modules. |
| Numba import or compilation error | unsupported NumPy/Numba pairing or old decorator behavior | keep the detector guarded; verify CPU-safe routines separately and test any Numba upgrade in a disposable environment. |
| `collections.Iterable` or deprecated NumPy alias error | old source assumptions under modern Python/NumPy | record the exact compatibility shim/patch required; do not present an unverified patch as a supported route. |

## Optional dependencies

- **Apex:** required only by the source's fp16 branch. If absent, keep
  `enable_mixed_precision` false and use a proven fp32 legacy backend. Do not
  substitute modern AMP without a dedicated sparse/loss/checkpoint validation.
- **NuScenes devkit:** required for NuScenes-specific data/evaluation surfaces,
  not for config syntax. Check the dataset version and local data separately.
  Installation does not provide `samples`, `sweeps`, metadata, or generated
  infos.
- **CUDA/Numba CUDA:** a visible GPU and `numba.cuda.is_available()` are
  necessary evidence for some kernels, but neither proves old spconv APIs.
- **TensorBoardX, Fire, scikit-image, Flask-CORS:** these support logging,
  CLI, visualization, or data surfaces. Missing optional packages should not be
  “fixed” by broad installation when the requested task is static guidance.

## Data and config validation

| Symptom | Check | Safe response |
|---|---|---|
| config parses but dataset build fails | dataset class, root, info path, database-info path, class names, and point feature count | route file generation/layout to `data-preparation`; show placeholders, not private paths. |
| `steps_per_eval` is zero or the loop never evaluates | inspect `train_config.steps_per_eval` and the actual parsed config | choose a positive cadence and preserve the original config; do not infer from a filename. |
| `KeyError`/registry assertion for VFE/middle/RPN/network | compare each `module_class_name` with the registered names in `configuration.md` | verify import order and exact spelling; do not silently substitute a different architecture for a checkpoint. |
| multi-head output/class mismatch | ten-class NuScenes class order differs from head concatenation order | restore the config's semantic order and ensure feature-map/class settings are complete. Revalidate predictions, not just construction. |
| shape mismatch at checkpoint restore | config architecture, class count, box code size, or filters differ from training | use the original pipeline config saved beside the checkpoint; partial loading requires explicit include/exclude and shape audit. |
| fp16 assertion about voxel count | `max_number_of_voxels * train batch_size >= 65535` | lower the per-GPU batch/voxel limit only with an accuracy/performance decision, or disable historical fp16. |
| NuScenes poor score | key-frame-only data, too few sweeps, high threshold, unsuitable augmentation, or untuned NMS | follow the guide's historical tuning notes (ten sweeps, mini split development, cautious augmentation) and report them as hypotheses, not guarantees. |

A protobuf parse is only a syntax check. Before running a detector, validate
that every referenced file exists and that the dataset returns the batch keys
expected by `VoxelNet.forward`.

## CLI and API misuse

- **Existing model directory:** `train` raises when `model_dir` exists and
  `resume=False`. Use a new output directory, `--create_folder=True`, or an
  explicit resume decision. Never delete a directory automatically.
- **Wrong Fire boolean:** verify `train.py --help`, then use explicit
  `--multi_gpu=True`, `--resume=True`, and `--measure_time=False`; do not rely
  on shell truthiness.
- **Stale `--pickle_result`:** current `evaluate` rejects unknown kwargs and
  writes `result.pkl` itself. Remove that flag and use dataset-specific label
  conversion only after API validation.
- **Missing `model_dir`:** although the `evaluate` signature defaults
  `model_dir=None`, its implementation resolves `Path(model_dir)` before
  restoring. Always pass a valid model directory; use `ckpt_path` to select an
  explicit checkpoint within the guarded route. A config alone is not weights.
- **Wrong checkpoint suffix:** the direct inference adapter asserts `.tckpt`.
  The checkpoint must also match the model's parameter names/shapes and backend.
- **Unintended default CUDA:** `example_convert_to_torch` defaults to
  `cuda:0`; pass `device=` explicitly for a conversion utility and do not call
  it on a CPU-only host expecting it to choose CPU.
- **Regex treated as glob:** freeze/load filters use regular-expression
  `match`, not shell wildcards. Print selected keys before training.
- **Timing confusion:** `measure_time` synchronizes CUDA and includes data or
  conversion timing differently in train/evaluate. Compare like with like.

## Multi-GPU and schedule failures

**Case: config requests multi-GPU but steps were not divided.**

1. Count visible GPUs from the intended `CUDA_VISIBLE_DEVICES` list.
2. Compare current `steps` and `steps_per_eval` to the single-GPU recipe.
3. If the values were authored for one GPU, apply integer division by the
   visible count once, as the README directs, and record the effective batch
   (`batch_size * GPU count`) and schedule.
4. If values were already scaled, do not divide again.
5. Re-run a config-only arithmetic check before any launch.

Symptoms include unexpectedly long training, evaluations at the wrong cadence,
or learning-rate schedule behavior unlike the reference. Multi-GPU support was
historically announced as needing testing; schedule correction does not prove
DataParallel correctness.

Other multi-GPU failures:

- `CUDA_VISIBLE_DEVICES` exposes fewer GPUs than expected: stop and reconcile
  the count; the loader and arithmetic depend on visible count.
- uneven final batch or collate errors: source uses a special multi-GPU collate
  and `drop_last=not multi_gpu`; inspect dataset lengths and batch shapes.
- out-of-memory: lower per-GPU config batch size, then reconsider total steps;
  do not change both without recording effective samples.
- NaN or inconsistent metrics: disable fp16 and timing, verify loss scaling,
  then reproduce with one visible GPU before attributing it to model code.

## Modern spconv 2.x / legacy symbol failure

**Case: modern spconv imports but legacy symbols are missing.**

This is the expected compatibility trap. A package version string beginning with
2.x is not the required API. The source needs `VoxelGeneratorV2` and legacy NMS
symbols, while model middle layers use older sparse layer conventions.

Recovery order:

1. run the safe helper and save its report;
2. do not import or start `train.py`, inference, or the viewer;
3. obtain a separate environment whose exact symbols and ABI are proven, or
   migrate to OpenPCDet/MMDetection3D;
4. if using a port, validate voxelization, sparse tensor coordinates, NMS,
   checkpoint loading, and a representative prediction against a reference;
5. only then widen the task's executable scope and update the skill evidence.

Do not monkey-patch `spconv.utils`, copy a modern `nms` call into old tensor
code, or claim that `spconv` import is enough.

## Workflow-specific failures

- **Model construction fails after the gate:** check registry names, output
  shape, target assigner class settings, channel/filter dimensions, and the
  first sparse-layer traceback. Keep the route blocked until a small model
  construction test passes in the exact environment.
- **Training fails after a checkpoint save:** preserve `checkpoints.json`, the
  `.tckpt` files, `pipeline.config`, and the first error. The source saves on
  exceptions but storage may still contain a partial file; verify file sizes
  and state-dict load in a copy before resuming.
- **Evaluation writes `result.pkl` but no metric:** inspect evaluator return,
  result format, class names, and dataset-specific paths. File existence is not
  evaluation success; route box/NMS/evaluation semantics to the geometry skill.
- **Direct inference fails:** the adapter is CUDA-only, requires `.tckpt`, and
  has an inspected symbol mismatch with the train module. Treat it as blocked
  until the exact revision and API are reconciled; do not route through viewer
  services to hide the failure.
- **Apex path fails:** revert to fp32 only if the legacy sparse backend gate is
  otherwise proven; otherwise stop the whole detector route. Apex absence is
  not fixed by toggling a config flag while claiming fp16 support.
- **NuScenes multi-head output looks shifted:** inspect class ordering and
  anchor groups before changing thresholds. The source concatenates large then
  small head predictions to match target-assignment order; a permutation can
  produce plausible shapes but invalid labels.

## Escalation record

For any unresolved failure record: config identity, source revision, package
versions, command shape with placeholders, first exception, backend probe
output, whether a checkpoint was written, and whether the operation was
import-only, construction, forward, evaluation, or service startup. Keep
hardware names, environment names, and private paths out of public skill text.

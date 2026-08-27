# Supervised-model troubleshooting

Use the first matching symptom; preserve the original config and exception in
an external run record before changing anything.

| Symptom | Likely cause | Safe next action |
| --- | --- | --- |
| `Your Model is Not Supported Yet!` | Wrong case/spelling | Use exact dispatch value: `Physnet`, `Tscan`, `iBVPNet`, `FactorizePhys`, `EfficientPhys`, `DeepPhys`, `BigSmall`, `PhysFormer`, `PhysMamba`, or `RhythmFormer`. |
| Model import fails before a run | Missing optional dependency | Run the smoke probe; install only in a user-approved prepared environment. For PhysMamba, missing Mamba/timm is a required backend block, not a CPU fallback. |
| `No data for train`, `valid`, or `test` | Empty loader, missing cache, or absent split | Route to data-preparation and inspect cache/file-list existence and split boundaries. Do not enable preprocessing just to suppress the error. |
| `Inference model path error` | `INFERENCE.MODEL_PATH` is empty or wrong | In `only_test`, set the user-controlled checkpoint path and verify it is the intended state dict. |
| Missing selected `_Epoch*.pth` | Save failed, wrong derived model directory, or wrong epoch policy | Recompute derived `MODEL.MODEL_DIR`; verify `TRAIN.MODEL_FILE_NAME`, zero-based index, and `USE_LAST_EPOCH`. Do not select a random file. |
| Missing/unexpected state-dict keys | Architecture or DataParallel mismatch | Compare model spelling, wrapper, frame count, channels, spatial size, and FSAM flags. Convert `module.` prefixes only in a separate user-approved utility. |
| Conv3d expected 5-D, got 4/5-D mismatch | Wrong `DATA_FORMAT` or model family | 3-D models need `N,C,T,H,W`; frame-wise models flatten `N,D,C,H,W` to `N*D,C,H,W`. Check the model catalog before transposing. |
| Linear layer size mismatch | Unsupported resize or model-specific spatial geometry | Use supported sizes: frame-wise models generally 36/72/96 (TSCAN also 128); BigSmall uses 144/9; 3-D transformer geometry must match its pooling/patch assumptions. |
| Output and label lengths differ | Missing final-frame padding or temporal truncation | iBVPNet and FactorizePhys difference time and need trainer padding; EfficientPhys differences flattened frames and pads one frame; TSM models discard incomplete groups. Recheck chunk/frame depth. |
| TSM reshape error | Flattened frame count is not divisible by `FRAME_DEPTH` | Make `N*D` a multiple of the configured depth or accept the trainer's explicit truncation and adjust output slicing. For BigSmall the segment is fixed at 3. |
| TSCAN/DeepPhys channels fail | Six-channel motion/appearance input missing | Use the expected first-three diff and last-three appearance channels; do not feed a three-channel raw clip to these constructors. |
| EfficientPhys normalization/difference is wrong | Precomputed diff data supplied to a model that diffs again | Use its intended three-channel input and let the model/trainer perform the difference; preserve the repeated final frame behavior. |
| `FactorizePhys` configuration key error | Custom YAML omitted a key read by trainer | State `TYPE`, `FRAME_NUM`, `CHANNELS`, all `MD_*` values, and `DROP_RATE` explicitly. `TYPE: Standard` and `TYPE: Big` select different spatial intents. |
| FactorizePhys FSAM tuple unpacking fails | `MD_FSAM`/`MD_INFERENCE` differs between model and trainer expectation | Keep FSAM flags and checkpoint architecture paired. Inspect whether the forward returns two or four values before writing an extension. |
| BigSmall `AttributeError: scheduler` | Current trainer logs a scheduler that it never creates | Treat stock training as blocked; user-owned extension must define a scheduler or remove the logging call, then re-run a tiny train-step test. |
| BigSmall `model_to_use` attribute error | Validation branch references an uninitialized selection policy | Define `best_epoch`/`last_epoch` policy in a user-owned trainer, or use a known checkpoint with `only_test`; do not infer selection. |
| BigSmall shape/label errors | Normal single-stream cache or wrong AU layout | Use the specialized two-stream cache, 3-frame segment, 144/9 geometry, pseudo-label setting, and BP4D+ label subset. Route cache details to data-preparation. |
| PhysFormer attention reshape error | Temporal patch or spatial token grid not divisible | Preserve common 160 frames, 128px geometry, patch 4, and a model-compatible `DIM`; check all three spatial pooling stages. |
| PhysFormer only-test geometry seems ignored | Trainer reads train-side resize defaults while constructing only-test model | State consistent train/test geometry and compare it to the checkpoint. Do not rely on an inference-only resize override. |
| RhythmFormer region assertion/top-k error | Wrong `N,D,C,H,W` layout or non-divisible temporal/spatial regions | Use `NDCHW`, common 160x128x128 clips, and the model's region-compatible geometry. Do not pass PhysFormer's `N,C,T,H,W` without a deliberate boundary conversion. |
| PhysMamba `No module named mamba_ssm` | Required CUDA extension is absent | Follow [mamba-backend.md](mamba-backend.md), verify versions and CUDA, and stop. Do not switch `DEVICE` to CPU and claim parity. |
| PhysMamba undefined CUDA symbol/ABI error | Compiled extension does not match torch/CUDA/ABI/compiler | Capture the full version tuple, inspect wheel tags/`nvcc`, and rebuild both Mamba dependencies together in an approved environment. |
| PhysMamba OOM or kernel error | Long/high-resolution clips, wrong device, or unsupported GPU | Smoke one CUDA device with a tiny block; reduce user-controlled batch/resolution only if it remains checkpoint-compatible. Never hide it by CPU fallback. |
| Loss is NaN or constant | Constant/short labels, wrong normalization, or invalid pseudo labels | Inspect finite values and temporal length in the cache; verify `FS`, label type, and normalization. Do not report metrics from invalid signals. |
| Validation is absent unexpectedly | `TEST.USE_LAST_EPOCH` is true | This is intentional last-epoch mode. Set it false only with a valid, subject-disjoint validation split and user approval for extra compute. |
| Validation is required unexpectedly | `TEST.USE_LAST_EPOCH` is false | Supply `VALID.DATA` and matching geometry, or explicitly choose last-epoch mode. |
| Prediction pickle missing | Output saving was not enabled or run stopped before evaluation | Inspect the derived test output setting and terminal error; use the evaluation sibling only after a complete test. |
| Metrics look shifted across datasets | Wrong test `FS`, label type, chunk slicing, or cross-dataset geometry | Preserve test sampling rate and label type, inspect per-chunk lengths, and use evaluation-and-visualization for metric semantics. |

## Minimal escalation record

When handing off a failure, include exact `MODEL.NAME`, `TOOLBOX_MODE`,
`DEVICE`, `NUM_OF_GPU_TRAIN`, train/valid/test `DATA_FORMAT`, chunk length,
model-specific frame/depth settings, label type, checkpoint basename, torch and
optional backend versions, and the first traceback. Do not include credentials,
private environment names, absolute source paths, or whole checkpoints.

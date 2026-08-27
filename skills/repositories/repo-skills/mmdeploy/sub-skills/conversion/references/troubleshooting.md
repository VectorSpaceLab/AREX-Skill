# Troubleshooting

This guide covers conversion-specific failures owned by the conversion sub-skill. It lists likely causes, recovery steps, and the point where the user should stop and hand off to another sub-skill.

## Quick decision rule

- If the failure is about missing Python packages or codebase imports, first confirm the target environment and installed backend stack.
- If the failure is about config shape, partition marks, checkpoint, or sample image/data, fix the user inputs or deploy config.
- If the failure is about backend libraries, plugins, optimization profiles, or device support, hand off to backend guidance after confirming the conversion inputs are correct.
- If the failure is about runtime inference after conversion, hand off to SDK or validation guidance unless the failure is clearly in the conversion pipeline.

## Failure table

| Surface | Symptom | Likely cause | Recovery steps | Stop / hand off when |
|---|---|---|---|---|
| Install/import | `ModuleNotFoundError` for `mmdeploy`, `mmengine`, `mmcv`, `torch`, `onnx`, or the target codebase | The inspection/runtime environment is incomplete or the wrong env is active. | Confirm the environment that can import MMDeploy and the upstream codebase, then reinstall only the missing package set. | Stop after the package list is identified; backend installation belongs to backend guidance. |
| Optional dependency | `ModuleNotFoundError` for `ppq`, `h5py`, `cv2`, or similar helper packages | A quantization/calibration helper is missing. | Install the missing helper only if the selected workflow needs it. `ppq` is needed for NCNN int8 quantization; `h5py` is needed for calibration HDF5 reads/writes. | Stop if the missing helper is a backend package or system library that belongs to another sub-skill. |
| Upstream codebase | Task processor construction fails with a missing codebase module or config import error | `model_cfg` points to a codebase package that is not installed or not importable. | Install or activate the correct upstream OpenMMLab codebase and verify that the config path matches the installed version. | Stop once the codebase mismatch is confirmed and hand off to the user or codebase maintainer. |
| Config path | `FileNotFoundError`, `_base_` resolution failure, or invalid deploy config loading | The deploy config path or model config path is wrong, or a base file reference is broken. | Re-check the config path, relative includes, and codebase/task folder. Use a deploy config whose backend and task match the model config. | Stop if the config comes from a repo/version that no longer matches the skill evidence. |
| Deploy config field | `KeyError` or assertion about `backend_config.type`, `onnx_config`, `ir_config`, `input_shape`, or `dynamic_axes` | The deploy config is missing a required field or uses an unsupported combination. | Add the missing field or switch to a config that already encodes the correct IR/backend/shape policy. | Stop if the user wants a new config design rather than a conversion fix. |
| Model checkpoint | Model build/load fails, or the exported model is obviously wrong | The checkpoint does not belong to the model config or task head. | Verify the model family, checkpoint URL/path, and class count. Try a known-good checkpoint for the same config family. | Stop if the checkpoint is corrupted or from a different model family and the user has no alternative. |
| Input image/data | The model builds but export/visualization fails at preprocessing or input creation | The input sample is missing, unreadable, or incompatible with the model pipeline. | Use a real representative sample in the format the model expects. For detection/segmentation, use an image that matches the preprocessing pipeline. | Stop if the task is not image-based or the chosen sample type is outside this sub-skill's scope. |
| Device/backend mismatch | TensorRT is invoked with `cpu`, or OpenVINO is given a CUDA device | `build_task_processor` rejects the backend/device pair. | Use `cuda:0`-style devices for TensorRT and CPU-style devices for CPU backends. Re-read backend guidance if the backend has special device rules. | Stop when the backend/device contract is valid but the backend runtime still fails. |
| Dynamic profile | TensorRT conversion fails with shape/profile mismatch or later inference rejects the input | `backend_config.model_inputs[].input_shapes` does not cover the real input size. | Update the min/opt/max profile, or switch to a static config whose spatial dimensions match the sample. | Stop if the user needs a backend-specific optimization profile design. |
| Backend conversion | `to_backend` fails, backend manager import fails, or backend file generation is incomplete | The backend runtime or plugin/toolchain is missing or incompatible. | Confirm IR export succeeded first, then hand off to backend guidance to resolve the backend runtime. | Stop immediately after verifying the conversion inputs and IR file are valid. |
| Partition marks | Missing mark names, `extract_model` cannot find the boundary, or extracted graph outputs are wrong | The ONNX graph was not marked correctly, or `partition_config.start/end` does not match the mark names. | Ensure the rewrite path actually calls `@mark`, then use exact `mark_name:input` / `mark_name:output` strings. Check that list outputs may appear as indexed names such as `pred_maps.0`. | Stop if the user needs help adding the mark points themselves; that is extensibility guidance. |
| Partition config | `get_partition_config` returns `None`, or predefined partition lookup fails | `apply_marks` is false, or the partition type is unsupported for that codebase/task. | Set `apply_marks=True` for explicit partition configs, and verify the partition type is valid for the selected codebase/task. | Stop if the partitioning policy needs a new rewriter implementation. |
| Calibration data | `calib_data.h5` is missing, empty, or has the wrong group layout | `calib_config` is absent, `create_calib` is false, or the dataset config has no usable validation dataloader. | Set `calib_config.create_calib=True`, ensure `calib_file` is writable, and provide a dataset config with a valid `val_dataloader`. | Stop when the calibration source is valid but the backend-specific PTQ recipe needs another sub-skill. |
| NCNN quantization | `--quant` run fails, PPQ import fails, or quant table generation aborts | NCNN int8 helper prerequisites are missing or the calibration image directory is invalid. | Install PPQ, pass a flat representative image directory to `--quant-image-dir`, and use the bundled NCNN quant helpers only after ONNX export succeeds. | Stop if the NCNN backend package itself is missing or the runtime toolchain needs installation. |
| VACC quantization | `shape_dict` parse fails or generated calibration tensors do not fit the model shape | The supplied model-shape literal is malformed or too small for calibration samples. | Pass a safe literal dictionary with NCHW shapes and ensure every calibration sample is no larger than the declared model shape. | Stop when the issue is backend/runtime specific rather than dataset-shape specific. |
| SDK metadata dump | `--dump-info` fails or JSON files are missing | The codebase/import path cannot be resolved, or the model/task metadata is inconsistent. | Recheck the model config, checkpoint, and deploy config. If the conversion itself already succeeded, the remaining failure belongs to SDK guidance. | Stop if the SDK runtime itself is missing or incompatible. |
| Visualization | Backend conversion succeeds but `visualize_model` fails or renders nothing useful | The backend model files are incomplete, the image cannot be read, or the backend runtime cannot infer. | Check the backend files in `--work-dir`, re-use a readable image, and confirm the backend runtime is available. | Stop if the failure is purely backend runtime or display-environment related. |
| CLI misuse | `argparse` reports missing positional arguments, unrecognized options, or `--test-img` consumes unexpected values | The deploy CLI positional order or option syntax is wrong. | Use positional order `deploy_cfg model_cfg checkpoint img`, then options. Keep `--test-img` values together because it accepts one or more image paths. Always provide an explicit `--work-dir` for reproducibility. | Stop if the user needs a new custom wrapper rather than the bundled deploy CLI. |
| API misuse | `TypeError`, wrong result type, or backend build sees a string where a sequence/config is expected | A direct API call skipped a stage or used CLI-style arguments where API objects/sequences are required. | Use `load_config` or pass `Config` objects where the signature requires them; pass `backend_files` as a list; call export before `to_backend`; use `visualize_model` for rendered outputs and `inference_model` for raw results. | Stop if the task is full end-to-end conversion; the deploy CLI is safer than stitching APIs manually. |
| Multiprocessing | Spawned process exits without a clear Python traceback | The CLI was launched from an interactive context, or a worker crashed before logging. | Re-run as a direct script command, lower the scope to a single stage, and use the API directly if the worker boundary is obscuring the error. | Stop if the issue is not reproducible outside multiprocessing. |

## Symptoms and fixes by workflow

### End-to-end `deploy.py`

Common symptoms:

- The script creates the work directory but no backend file appears.
- `deploy.json` / `pipeline.json` / `detail.json` are missing after `--dump-info`.
- The script exports IR successfully, then fails during partition extraction, calibration, or backend conversion.

Likely fixes:

- Confirm the deploy config backend matches the device.
- Confirm `img` and `--test-img` are readable and representative.
- Confirm the requested backend files are already installed.
- Confirm `partition_config` and `calib_config` are actually enabled.

When to stop:

- If IR export works and the failure is now backend file generation, hand off to backend guidance.
- If backend files exist but visualization fails, hand off to SDK/validation guidance.

### Partitioned ONNX export

Common symptoms:

- `extract_model` cannot find a start or end marker.
- The partitioned ONNX contains the wrong tensors at the boundary.
- The user only has a mark name from a rewriter comment and not an exact `mark_name:input/output` boundary string.

Likely fixes:

- Check that the mark was added in the code path actually used during export.
- Re-check the exact `@mark` name and whether the boundary is `input` or `output`.
- For list outputs, use indexed names such as `pred_maps.0` when defining `output_names`.
- Make sure `partition_config.apply_marks=True` and every partition entry has `save_file`, `start`, `end`, and `output_names`.

When to stop:

- If the user needs to modify source rewriters to insert the marks, hand off to extensibility guidance.

### Calibration and quantization

Common symptoms:

- The HDF5 file has no expected group layout.
- Calibration images are accepted but quantization later fails.
- A dataset config works for model evaluation but not calibration.

Likely fixes:

- Use validation-style data, not the held-out test set.
- Keep the calibration image directory flat and representative.
- Verify `val_dataloader` exists in the calibration source config.
- For NCNN int8, check that PPQ is installed and that `--quant-image-dir` points to real images.

When to stop:

- If the failure depends on a missing backend quantization package or a backend toolchain, hand off to backend guidance.

## Stop conditions

Stop conversion debugging when:

- the deploy config is valid, the model config and checkpoint match, the input image is readable, and IR export already succeeded; but backend conversion, runtime, or device support still fails;
- the issue requires adding marks or changing rewriter code;
- the issue requires installing or repairing a backend runtime stack;
- the issue requires SDK runtime debugging rather than conversion.

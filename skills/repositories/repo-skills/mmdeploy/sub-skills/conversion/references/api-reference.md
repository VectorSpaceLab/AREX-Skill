# API reference

The signatures below were verified against the installed MMDeploy package inspection for the current environment snapshot. Use them as the contract for conversion routing and for deciding whether to call the public API directly or go through the bundled CLI.

## Conversion APIs

| API | Verified signature | Primary use |
|---|---|---|
| `mmdeploy.apis.torch2onnx` | `(img: Any, work_dir: str, save_file: str, deploy_cfg: Union[str, mmengine.config.config.Config], model_cfg: Union[str, mmengine.config.config.Config], model_checkpoint: Optional[str] = None, device: str = 'cuda:0')` | Export a PyTorch/OpenMMLab model to ONNX IR. |
| `mmdeploy.apis.torch2torchscript` | `(img: Any, work_dir: str, save_file: str, deploy_cfg: Union[str, mmengine.config.config.Config], model_cfg: Union[str, mmengine.config.config.Config], model_checkpoint: Optional[str] = None, device: str = 'cuda:0')` | Export a PyTorch/OpenMMLab model to TorchScript IR. |
| `mmdeploy.apis.extract_model` | `(model: Union[str, onnx.onnx_ml_pb2.ModelProto], start_marker: Union[str, Iterable[str]], end_marker: Union[str, Iterable[str]], start_name_map: Optional[Dict[str, str]] = None, end_name_map: Optional[Dict[str, str]] = None, dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None, save_file: Optional[str] = None) -> onnx.onnx_ml_pb2.ModelProto` | Extract a marked ONNX subgraph. |
| `mmdeploy.apis.create_calib_input_data` | `(calib_file: str, deploy_cfg: Union[str, mmengine.config.config.Config], model_cfg: Union[str, mmengine.config.config.Config], model_checkpoint: Optional[str] = None, dataset_cfg: Union[str, mmengine.config.config.Config, NoneType] = None, dataset_type: str = 'val', device: str = 'cpu') -> None` | Create calibration data for PTQ/int8 workflows. |
| `mmdeploy.apis.utils.build_task_processor` | `(model_cfg: mmengine.config.config.Config, deploy_cfg: mmengine.config.config.Config, device: str) -> mmdeploy.codebase.base.task.BaseTask` | Build the codebase-specific task processor used for input creation, export, backend build, and visualization. |
| `mmdeploy.apis.utils.to_backend` | `(backend_name: str, ir_files: Sequence[str], work_dir: str, deploy_cfg: Optional[Any] = None, log_level: int = 20, device: str = 'cpu', **kwargs) -> Sequence[str]` | Convert IR files to backend files. |
| `mmdeploy.apis.visualize_model` | `(model_cfg: Union[str, mmengine.config.config.Config], deploy_cfg: Union[str, mmengine.config.config.Config], model: Union[str, Sequence[str]], img: Union[str, numpy.ndarray, Sequence[str]], device: str, backend: Optional[mmdeploy.utils.constants.Backend] = None, output_file: Optional[str] = None, show_result: bool = False, **kwargs)` | Run inference and optionally render outputs for a checkpoint or backend model. |
| `mmdeploy.apis.inference_model` | `(model_cfg: Union[str, mmengine.config.config.Config], deploy_cfg: Union[str, mmengine.config.config.Config], backend_files: Sequence[str], img: Union[str, numpy.ndarray], device: str) -> Any` | Run backend or PyTorch inference and return raw results without visualization. |

## Routing notes

### `torch2onnx`

- Load `deploy_cfg` and `model_cfg` first; the function internally resolves IR config, backend, dynamic axes, and model inputs.
- `work_dir` is created if needed.
- The device default in the API is `cuda:0`, but the bundled CLI defaults to `cpu` to keep conversions explicit and backend-agnostic.
- If the backend is NCNN, ONNX optimization is disabled inside the API to preserve blob counts.

### `torch2torchscript`

- Follows the same task-processor and input-creation flow as `torch2onnx`.
- Converts the created inputs to the requested device before tracing.
- TorchScript export is the only IR path here where dynamic shape is always treated as enabled by the config utility.

### `extract_model`

- `start_marker` and `end_marker` are exact mark names, usually written as `mark_name:input` or `mark_name:output`.
- `start_name_map` and `end_name_map` may rename boundaries when the source and extracted graph names differ.
- `dynamic_axes` can be passed through to keep symbolic batch/shape information on the extracted graph.
- Use this only after marks exist in the exported ONNX graph.

### `create_calib_input_data`

- Uses the validation dataloader from `dataset_cfg` when provided, otherwise the model config is reused as the calibration source.
- Internally forces the calibration dataloader batch size to 1.
- Builds the task processor, patches the model, and writes the HDF5 file used for PTQ.
- The file structure depends on whether the deploy config is end-to-end or partitioned. End-to-end creates `calib_data/end2end/input/...`; partitioned deploy configs create `calib_data/partition*/...` groups.

### `build_task_processor`

- Validates backend/device compatibility before building the task processor.
- Imports any codebase-specific external modules referenced in the deploy config.
- Returns the codebase task object used by input creation, model building, visualization, dataset loading, and backend handoff.

### `to_backend`

- Accepts a backend name string and one or more IR files.
- Delegates to the backend manager selected by the configured backend.
- Any backend-specific extra keyword arguments are forwarded unchanged.
- This is the handoff point when IR export succeeded but the backend conversion itself fails.

### `visualize_model` and `inference_model`

- `visualize_model` is used by the deploy CLI for smoke rendering of both backend files and the original checkpoint.
- `inference_model` returns the inference result list/structure and does not write rendered images by itself.
- Both rely on `build_task_processor` to create the correct model wrapper and input pipeline.
- `backend_files` must be a sequence, even when the backend uses a single file, because some backends return multiple files.

## Verified package facts

- `mmdeploy` package version: `1.3.1`
- `torch`: `2.3.1+cpu`
- `mmcv`: `2.2.0`
- `mmengine`: `0.10.7`
- `onnx`: `1.17.0`
- TorchScript backend was available in the inspected environment; accelerator backends were not installed in the inspected environment snapshot.

## Conversion-owned routing signals

- Use `torch2onnx` for ONNX export when `ir_config.type='onnx'` or the legacy `onnx_config` is present.
- Use `torch2torchscript` when the IR type is TorchScript.
- Use `extract_model` only when the deploy config enables partition marks.
- Use `create_calib_input_data` only when calibration data is requested by deploy config.
- Use `to_backend` after IR generation, partitioning, and calibration are complete.
- Use `visualize_model` for smoke rendering; use `inference_model` when only raw predictions are needed.

# API reference

## Top-level package

### `paddlecv.PaddleCV`

```python
PaddleCV(
    task_name=None,
    config_path=None,
    output_dir="output",
    run_mode="paddle",
    device="CPU",
)
```

- Use `task_name` for bundled task presets such as `PP-OCRv3`, `PP-ShiTu`, or `PP-Human`.
- Use `config_path` for explicit single-op or custom DAG YAML files.
- `output_dir` controls image/result output.
- `run_mode` accepts the package's inference modes (`paddle`, `trt_fp32`, `trt_fp16`, `trt_int8`, `mkldnn`).
- `device` accepts `CPU`, `GPU`, or `XPU`.

### `PaddleCV.__call__(input)`
- Accepts an image path, image directory, video path, or in-memory image data depending on the loaded config.
- Returns the pipeline result list/dict produced by the final output op.

### `PaddleCV.list_all_supported_tasks()`
- Prints the built-in `TASK_DICT` task names and their `paddlecv://` config targets.

### `PaddleCV.list_all_supported_models(filters=[])`
- Prints model names from the generated `MODEL_ZOO` catalog.
- Filters are substring filters; a filter must match every term in the list.

## Config and pipeline APIs

### `ppcv.engine.pipeline.Pipeline(cfg)`
- `cfg` is an argparse-style namespace with at least `config` and `input`.
- The pipeline parses config files, instantiates the operator DAG, then runs image or video inputs.

### `ppcv.core.config.ArgsParser`
- Adds `-o/--opt` overrides.
- `parse_args()` requires `--config`.
- `-o` values use `KEY=VALUE` pairs and nested dotted keys.

### `ppcv.core.config.ConfigParser(args)`
- Reads YAML config files, merges `ENV` and `MODEL` sections, and validates `Inputs` graph links.
- Raises when an input key does not match a previous output name or when the device is invalid.

## Registry and operator APIs

### `ppcv.core.workspace.register(cls)`
- Decorator for operator registration.
- Class names must be unique.

### `ppcv.core.workspace.create(cls_name, op_cfg, env_cfg)`
- Instantiates a registered operator by class name.

### `ppcv.core.workspace.get_global_op()`
- Returns the global operator registry dictionary.

### `ppcv.ops.base.create_operators(params, mod)`
- Creates pre/post-process operator instances from a YAML operator list.
- The supplied module must export the operator class names.

## Operator base classes
- `BaseOp`: shared input filtering and validation helpers.
- `ModelBaseOp`: model-loading base for preprocessing, predictor creation, and batch inference.
- `ConnectorBaseOp`: bridge op base for graph composition.
- `OutputBaseOp`: final result/visualization/save helper base.

## Common output keys
- Classification: `class_ids`, `scores`, `label_names`
- Detection: `dt_bboxes`, `dt_scores`, `dt_class_ids`, `dt_cls_names`
- Feature extraction: `dt_bboxes`, `feature`, `rec_score`, `rec_doc`
- Keypoint: `keypoints`, `kpt_scores`
- Segmentation: `seg_map`
- OCR / PP-Structure: `dt_polys`, `dt_scores`, `rec_text`, `structures`, `html`, `pred_ids`, `heads`, `tails`

## Model catalog helpers
- `ppcv.model_zoo.get_config_file(task)` resolves a built-in config path through `paddlecv://`.
- `ppcv.model_zoo.get_model_file(path)` resolves a built-in model path through `paddlecv://`.
- `ppcv.model_zoo.list_model(filters)` prints the generated model list file.

## Read this before editing workflows
If you are changing operator wiring, model order, or custom config graph behavior, also read `references/task-catalog.md` and the owning sub-skill reference for the workflow family.

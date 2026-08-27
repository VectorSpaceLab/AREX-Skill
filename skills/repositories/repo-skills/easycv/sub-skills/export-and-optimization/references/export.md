# Export workflows

## Main entry points

- `python -m easycv.tools.export CONFIG CKPT EXPORT_PATH`
- `easycv.tools.export(CONFIG, CKPT, EXPORT_PATH)`
- `easycv.apis.export.export(cfg, ckpt_path, filename, model=None, **kwargs)`

## Export types

| Export type | Output shape | Typical use |
| --- | --- | --- |
| `raw` | `.pth`-style checkpoint with metadata | Keep the checkpoint close to the training model and load it with a matching predictor. |
| `jit` | TorchScript `.jit` plus sidecar config | Use for portable inference with EasyCV predictors. |
| `blade` | Blade-optimized artifact plus config | Use when the Blade stack is installed and you want the optimized path. |
| `onnx` | ONNX model plus config sidecar | Use when the ONNX runtime path is the target. |

## Common config flags

- `export_type`
- `preprocess_jit`
- `static_opt`
- `batch_size`
- `use_trt_efficientnms`
- `blade_config`
- `export_neck`

## What to keep together

- The export artifact itself
- Any `.config.json` sidecar the export path writes
- Any `.preprocess` artifact if the export path saves one
- The original config or a distilled config copy that the predictor can load

## Model-family notes

Export logic specializes on model families such as classification, YOLOX, SWAV, MOCO, MoBY, BEVFormer, pose, and STGCN. If the model is not one of the specialized branches, EasyCV falls back to the common checkpoint export path.

## Safe first checks

- `python -m easycv.tools.export --help`
- `python -c "from easycv.apis.export import export; print(export)"`


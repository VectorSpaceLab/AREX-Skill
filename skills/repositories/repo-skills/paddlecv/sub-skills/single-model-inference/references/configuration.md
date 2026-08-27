# Configuration

## Single-op config layout
Single-op YAML files live under `paddlecv/configs/single_op/`. They describe a pipeline with a single model op plus its output op.

Typical sections:
- `ENV`: runtime options such as `device`, `run_mode`, `output_dir`, and output toggles.
- `MODEL`: a list of operators, usually one model op followed by one output op.

## Important fields
- `name`: unique operator name inside one config.
- `param_path` / `model_path`: local or `paddlecv://` model assets.
- `batch_size`: per-op batch size.
- `PreProcess` / `PostProcess`: operator lists that build the model pre/post pipeline.
- `Inputs`: graph edges in `{last_op}.{output_key}` form.

## Common runtime settings
- `device`: `CPU`, `GPU`, or `XPU`.
- `run_mode`: `paddle`, `trt_fp32`, `trt_fp16`, `trt_int8`, or `mkldnn`.
- `output_dir`: where visualizations and JSON outputs are written.
- `save_img`, `save_res`, `return_res`, `print_res`: output behavior toggles.

## Notes for single-op workflows
- Use `image_shape` when the config expects a fixed input size.
- Keep the `Inputs` chain simple: the first model usually reads `input.image`.
- `-o` overrides are useful for threshold tuning and other small edits without duplicating the full YAML.
- If the config references a label list or dict file, the path is usually resolved through `paddlecv://`.

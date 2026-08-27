# Batch prediction

`python -m easycv.tools.predict` is the batch front door for local files, URLs, and ODPS tables.

## Required dependency

- `easy_predict` must be installed for this command to work.

## File-list mode

Each line in the input file is usually a local image path or an image URL.

Example:

```bash
python -m easycv.tools.predict \
  --input_file predict/test.list \
  --output_file predict/output.txt \
  --model_type YoloXPredictor \
  --model_path export_dir/epoch_300.pt
```

## Table mode

The table path can be an ODPS table or another supported table source.
The input table must provide the image column named by `--image_col`.
The image column may contain either URLs or base64 strings.

Common table arguments:

- `--input_table`
- `--output_table`
- `--image_col`
- `--image_type` (`url` or `base64`)
- `--reserved_columns`
- `--result_column`
- `--odps_config`

## Predictor resolution

- `YoloXPredictor` has a special helper path that can auto-select raw / JIT / Blade assets from a model directory.
- Other predictor types usually need an explicit `model_path` and, when needed, a `config_file`.
- Exported directories should keep their model file and sidecar config together.

## Common batch inputs

- Local image list files
- URL list files
- ODPS tables with URL or base64 columns
- Optional `oss_prefix` / `local_prefix` replacement for mixed storage paths

## Common batch outputs

- A local or OSS output text file
- A table with reserved columns plus a result column
- One result row per input row after the process pipeline formats the prediction output

## Operational notes

- GPU mode requires the requested launcher when you spread work across processes.
- Image mode and preprocessing must match the predictor family.
- The output file / table schema depends on the predictor's result keys.


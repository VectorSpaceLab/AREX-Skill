# Module troubleshooting

## Wrong workflow: pipeline YAML vs module YAML

Symptoms:

- Training/evaluation flags do not exist.
- A config exported with `paddlex --get_pipeline_config` is used with `Global.mode=train`.
- The user asks to fine-tune a pipeline directly.

Actions:

1. Determine the underlying module/model family.
2. Start from a module config, not a pipeline config.
3. Use `pipelines/` only for pre-trained pipeline inference and pipeline composition.

## Model name or checkpoint confusion

Symptoms:

- `create_model` cannot find `model_name`.
- Prediction uses a training output path that is not exported.
- Evaluation/export cannot locate weights.

Actions:

- Confirm the model exists for the selected module family.
- Use official pretrained resolution only when downloads are allowed.
- Use `model_dir` for exported inference model directories.
- Use training checkpoint paths in `Evaluate`/`Export` sections, not as arbitrary `model_dir` values unless the config expects them.
- After training, export before deployment or Paddle2ONNX.

## Dataset check failures

Actions:

1. Run `check_dataset` with the exact module config.
2. Fix missing files, annotation paths, label maps, class ids, and split definitions.
3. For OCR/document tasks, check text encoding, special tokens, table/layout labels, and multi-page mapping.
4. For time-series, check timestamp order, target columns, grouping ids, and missing values.
5. For video/speech, check codec/decoder availability before blaming model code.

## Dependency errors

PaddleX separates PaddlePaddle from PaddleX extras/plugins. Common fixes:

- install CPU PaddlePaddle for baseline module checks.
- install a GPU PaddlePaddle wheel only when the user requests GPU and the driver/runtime is compatible.
- install domain extras for the selected family (`cv`, `ocr`, `ts`, `speech`, `video`, `multimodal`, or broader `base`).
- route serving/HPI/Paddle2ONNX/GenAI plugin failures to `../deployment/`.

## Long-running training risks

Do not start full training unless the user has supplied:

- dataset path and format.
- model/config selection.
- expected hardware/device plan.
- output directory and checkpoint retention preference.
- runtime/budget limits.

For unknown budgets, propose a dataset-check and tiny smoke run first.

## Distributed training failures

Checklist:

- visible GPU count equals the launch plan.
- all nodes can access dataset and output paths.
- IP/host list is consistent across nodes.
- SSH/firewall permits worker communication.
- single-device `check_dataset` and tiny training work first.

## Export and conversion failures

If export succeeds but deployment fails, distinguish:

- module export problem: missing/inconsistent Paddle model files or config.
- `pdparams2safetensors` problem: unsupported model name, missing `Pdparams2safetensors.input_path` or `Pdparams2safetensors.output_dir`, multiple `.pdparams` candidates, or the wrong checkpoint file.
- Paddle2ONNX problem: unsupported opset/op, plugin missing, or wrong input model dir.
- HPI/serving problem: backend plugin, TensorRT/CUDA, cache, or server config issue.

Use `../deployment/` for the second and third classes.

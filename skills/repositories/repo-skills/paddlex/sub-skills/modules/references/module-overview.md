# PaddleX module workflows

Use this reference for PaddleX module-level development: single-model prediction, dataset checking, training, evaluation, export, prediction, and checkpoint conversion.

## Choose API vs config mode

| User intent | Recommended route |
| --- | --- |
| Quick single-model prediction with an existing model name | `create_model(...)` |
| Validate a dataset before training | module config + `Global.mode=check_dataset` |
| Train/fine-tune a model | module config + `Global.mode=train` |
| Evaluate a trained checkpoint | module config + `Global.mode=evaluate` |
| Export an inference model | module config + `Global.mode=export` |
| Run prediction from a module config | module config + `Global.mode=predict` |
| Convert Paddle weights to safetensors | module config + `Global.mode=pdparams2safetensors` |

## Public API facts

Installed PaddleX 3.7.2 exposes:

```text
create_model(model_name, model_dir=None, *args, **kwargs)
build_dataset_checker(config: paddlex.utils.config.AttrDict) -> BaseDatasetChecker
build_trainer(config: paddlex.utils.config.AttrDict) -> BaseTrainer
build_evaluator(config: paddlex.utils.config.AttrDict) -> BaseEvaluator
```

The simplest API pattern is:

```python
from paddlex import create_model

model = create_model("PP-LCNet_x1_0")
for result in model.predict("demo.jpg", batch_size=1):
    result.print()
```

`model_dir` should point to a local inference model directory when you already have exported model artifacts. If you want official pretrained weights, omit `model_dir` and allow the package to resolve/download them in an environment that permits downloads.

## Config-driven lifecycle

Module configs usually have sections for global mode, dataset, train/evaluate/export/predict settings, and model-specific parameters. Names vary by module family; avoid editing unrelated fields blindly.

Typical lifecycle:

1. Start from a module config near the desired model family.
2. Set dataset paths and label/annotation files.
3. Run `check_dataset`.
4. Train only after the dataset check succeeds.
5. Evaluate the selected checkpoint.
6. Export the checkpoint to an inference directory.
7. Use the exported directory for API prediction, pipeline integration, deployment, Paddle2ONNX, or serving.

Command pattern:

```bash
python scripts/run_module_smoke.py --config module_config.yaml --mode check_dataset --override Dataset.dataset_dir=./dataset
python scripts/run_module_smoke.py --config module_config.yaml --mode train --override Global.output=./output
python scripts/run_module_smoke.py --config module_config.yaml --mode evaluate --override Evaluate.model_dir=./output/best_model
python scripts/run_module_smoke.py --config module_config.yaml --mode export --override Export.weight_path=./output/best_model/model.pdparams
python scripts/run_module_smoke.py --config module_config.yaml --mode pdparams2safetensors --override Pdparams2safetensors.input_path=./output/best_model/model.pdparams --override Pdparams2safetensors.output_dir=./output/safetensors
python scripts/run_module_smoke.py --config module_config.yaml --mode predict --override Predict.model_dir=./output/inference
```

The exact override keys can differ by module. When a command fails with an unknown key, inspect the chosen config and move the override to the matching section.

## Representative module families

Module config directories in PaddleX 3.7.2 include:

- CV: `image_classification`, `object_detection`, `semantic_segmentation`, `instance_segmentation`, `rotated_object_detection`, `small_object_detection`, `image_anomaly_detection`, `keypoint_detection`.
- OCR/document: `text_detection`, `text_recognition`, `table_structure_recognition`, `table_cells_detection`, `layout_detection`, `layout_analysis`, `formula_recognition`, `seal_text_detection`, `doc_text_orientation`, `textline_orientation`, `image_unwarping`.
- Retrieval/face/attributes: `image_feature`, `face_detection`, `face_feature`, `mainbody_detection`, `pedestrian_attribute_recognition`, `vehicle_attribute_recognition`, `vehicle_detection`.
- Time series: `ts_forecast`, `ts_anomaly_detection`, `ts_classification`.
- Speech/TTS: `multilingual_speech_recognition`, `text_to_speech_acoustic`, `text_to_speech_vocoder`, `text_to_pinyin`.
- Video: `video_classification`, `video_detection`.
- Multimodal/VLM/3D: `doc_vlm`, `chart_parsing`, `open_vocabulary_detection`, `open_vocabulary_segmentation`, `3d_bev_detection`.

## Checkpoint and export vocabulary

- **Official/pretrained weights**: resolved by model name when downloads are allowed.
- **Training checkpoint**: intermediate or best model under a training output directory; may include optimizer/state files.
- **Inference/exported model directory**: deployment-ready directory produced by export; this is the right input for `model_dir`, serving, HPI, or Paddle2ONNX-style workflows.
- **`pdparams2safetensors`**: conversion route for Paddle parameter files when a downstream workflow needs safetensors.

## Distributed training

Distributed training is a runtime execution plan layered on top of the module config. Before using it:

- confirm every worker can read the same data and output paths or has synchronized copies.
- confirm visible devices and GPU count match the launch command.
- verify IP/host lists and SSH/network connectivity for multi-node runs.
- keep a single-device `check_dataset`/small train smoke passing first.

## Hand off to deployment

After export, use `../deployment/` for:

- high-performance inference / HPI backend selection.
- serving / high-stability serving.
- Paddle2ONNX conversion.
- GenAI server/client configuration.
- hardware-specific runtime packaging.

## Generation notes (provisional)

- Current reconciliation targets: `references/data-formats.md`, `references/module-troubleshooting.md`, `scripts/run_module_smoke.py`, and `scripts/inspect_module_api.py`.
- Keep the module path self-contained through `scripts/run_module_smoke.py` / `paddlex.engine.Engine`; do not drift back to the pipeline-oriented `paddlex` CLI.
- Key facts to preserve: `create_model` signature, `model.predict` generator behavior, `build_*` `AttrDict` signatures, `pdparams2safetensors` registry limits, and `Train.dist_ips` for distributed runs.
- Troubleshooting surfaces: model-name/model-dir mismatch, invalid paths, unsupported dataset conversion, unsupported weight-conversion models, distributed peer setup, and `engine` / `engine_config` precedence.
- Source scripts to adapt or exclude: `main.py` (reference-only or wrap only as an engine entrypoint), `install_pdx.py` (exclude), `paddlex/paddlex_cli.py` (exclude), `tools/check_docs_github_links.py` and `tools/resolve_doc_github_refs.py` (exclude), `api_examples/pipelines/*.py` (exclude).
- Acceptance checklist: router-like `SKILL.md`, no runtime links back to the source checkout, safe helper scripts only, and explicit coverage for `pdparams2safetensors` plus distributed training.
- Hard cases to carry forward: conflicting `engine`/`engine_config`/`use_hpip` inputs, and `pdparams2safetensors` on an unsupported model or a directory with multiple `.pdparams` files.

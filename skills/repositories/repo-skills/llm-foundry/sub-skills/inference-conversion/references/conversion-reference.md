# Conversion Reference

This reference covers conversion from training-time or HF artifacts into inference-time formats. It does not describe how to train or resume training; route those tasks to `training-finetuning`.

## Composer checkpoint to Hugging Face folder

A Composer `Trainer` checkpoint contains full training state: model, tokenizer integration state, optimizer, scheduler, timestamp, metrics, and other trainer metadata. Inference usually needs only a Hugging Face-compatible folder containing config, tokenizer assets, model weights, and optional model code.

The Composer-to-HF converter accepts:

```bash
python convert_composer_to_hf.py \
  --composer_path <composer-checkpoint.pt-or-object-store-uri> \
  --hf_output_path <hf-output-folder-or-object-store-uri> \
  --output_precision bf16 \
  --trust_remote_code
```

Important flags:

- `--composer_path`: required full Composer checkpoint. It may be a local file or an object-store URI supported by the Composer object-store utilities.
- `--hf_output_path`: required output folder. It may be local or an object-store URI. The converter writes to a local parsed folder first and uploads files when the output target is remote.
- `--local_checkpoint_save_location`: optional local cache path for the downloaded checkpoint. If the input is local, this may become a local symlink target.
- `--output_precision`: `fp32`, `fp16`, or `bf16`; controls saved HF weight dtype.
- `--trust_remote_code`: allows tokenizer/model code outside core Transformers when extracting tokenizer state or loading MPT/custom artifacts.
- `--hf_repo_for_upload`: optional Hugging Face Hub model repo id. This creates or reuses a private model repo and uploads the output folder.
- `--test_uploaded_model`: after Hub upload, reloads the uploaded model/tokenizer and performs a tiny generation to compare model structure and dtype. This requires network, a valid Hub token, and enough memory to load the model again.

Expected local output resembles a standard `save_pretrained` folder:

```text
config.json
pytorch_model.bin or sharded pytorch_model-*.bin files
tokenizer.json / tokenizer_config.json / special_tokens_map.json
vocab/merge/tokenizer model files as applicable
modeling code for custom architectures when needed
```

Converter behavior to remember:

1. Creates the output folder before loading weights; avoid pointing at an existing non-empty folder unless you intend to manage conflicts.
2. Downloads or symlinks the Composer checkpoint to a local checkpoint path.
3. Loads the Composer state dictionary in CPU RAM.
4. Requires a `state` key and Hugging Face integration state for tokenizer extraction.
5. Builds an HF config from the Composer state, saves tokenizer files when available, strips the `model.` prefix from weight keys, casts tensor weights to the requested dtype, and saves `pytorch_model.bin`.
6. Reloads the local HF model/tokenizer as a validation step. For MPT, attention is forced to `torch` and init device to CPU during this local validation.
7. For MPT/custom code, edits files for Hugging Face compatibility before final save/upload.
8. If `--hf_repo_for_upload` is set, Hub API calls use `token=True`; the token must already be available through the Hugging Face login/cache or environment.

Use local conversion first when possible. Add Hub upload only after the local HF folder loads correctly.

## Relationship to `HuggingFaceCheckpointer`

There are two routes to an HF-format checkpoint:

- **During training:** configure `HuggingFaceCheckpointer` so Composer periodically writes HF-format checkpoints directly.
- **After training:** run the Composer-to-HF converter on an existing Composer checkpoint.

`HuggingFaceCheckpointer` is a Composer callback for `HuggingFaceModel` instances. It saves under a `huggingface/<folder-name>` subfolder beneath the configured save folder, can upload to remote save folders, and can register the final model to MLflow. Relevant settings include:

- `save_folder`: local or remote top-level folder, often matching the training save folder.
- `save_interval`: Composer time interval for HF checkpoint creation.
- `huggingface_folder_name`: format string such as `ba{batch}`.
- `precision`: `float32`, `float16`, or `bfloat16` for saved weights. Note the callback names differ from converter names (`float32` vs `fp32`).
- `overwrite`: whether remote uploaded checkpoint files may be overwritten.
- `flatten_imports`: import prefixes flattened when editing MPT files.
- `final_register_only`, `mlflow_registered_model_name`, and `mlflow_logging_config`: MLflow registration pathway.
- `LLM_FOUNDRY_SAVE_FOLDER_HF_MAX_SHARD_SIZE`: environment variable controlling Hugging Face shard size during save.

If the user wants to add or change training callbacks, route to `training-finetuning`; use this reference only to explain how the produced HF artifacts relate to inference and post-hoc conversion.

## Hugging Face to ONNX

The ONNX exporter loads a Hugging Face tokenizer/config/model, creates a random token batch, calls `torch.onnx.export`, and writes `model.onnx`.

Invocation shape:

```bash
python convert_hf_to_onnx.py \
  --pretrained_model_name_or_path <local-hf-folder-or-cached-hub-id> \
  --output_folder <local-folder-or-object-store-uri> \
  --export_batch_size 1 \
  --max_seq_len 2048 \
  --verify_export \
  --trust_remote_code true
```

Important flags:

- `--pretrained_model_name_or_path`: required local folder or Hub id. Prefer a local folder to avoid downloads.
- `--output_folder`: required local or object-store target. The exporter writes `model.onnx` to a parsed local path first and uploads files if the target is remote.
- `--export_batch_size`: batch size of the random sample input used for export; default is 8.
- `--max_seq_len`: sequence length of the random sample input. Required if the config does not provide `max_seq_len`.
- `--verify_export`: load the ONNX file, run ONNX checker, run ONNX Runtime, and compare logits against the PyTorch model with loose numerical tolerances.
- `--trust_remote_code`, `--use_auth_token`, `--revision`: forwarded to Hugging Face loaders.

ONNX export details:

- For configs with `attn_config`, attention implementation is forced to `torch` for export.
- The export uses opset 16 and input names `input_ids` and `attention_mask`.
- `--verify_export` requires `onnx` and `onnxruntime` and can use substantial CPU RAM for large sequence lengths.
- Object-store output requires credentials and write permissions for the target URI.

## Choosing precision and format

| Target | Precision options | Notes |
|---|---|---|
| Composer -> HF | `fp32`, `fp16`, `bf16` | Choose `bf16` for modern GPU inference when supported; choose `fp32` for CPU compatibility. |
| HF checkpointer callback | `float32`, `float16`, `bfloat16` | Used inside training configs, not as converter flags. |
| HF -> ONNX | Model load dtype follows the HF checkpoint/config path | Export itself does not expose a dtype flag; prepare the HF folder appropriately first. |
| FasterTransformer conversion | `fp32`, `fp16` | Advanced MPT-only path; see [backends-and-export.md](backends-and-export.md). |

## Conversion safety checklist

Before running a conversion:

1. Confirm the input path exists locally or that object-store credentials are configured.
2. Confirm available disk space for a full checkpoint copy plus output folder.
3. Confirm CPU RAM is sufficient to load the Composer checkpoint or HF model.
4. Decide whether custom code is trusted before setting `--trust_remote_code`.
5. Keep Hub upload separate from local conversion unless the user explicitly wants upload.
6. For ONNX verification, install/check `onnx` and `onnxruntime` first and reduce `--export_batch_size`/`--max_seq_len` for a bounded smoke.
7. Record output precision, source checkpoint identity, and whether the output was locally validated.

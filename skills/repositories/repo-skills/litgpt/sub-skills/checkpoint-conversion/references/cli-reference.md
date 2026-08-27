# Checkpoint CLI Reference

This reference distills LitGPT checkpoint command behavior verified from current CLI registration/help, source behavior, and tests. Commands can consume large checkpoints or use the network; dry-run with the bundled check scripts first when possible.

## `litgpt download`

Purpose: download Hugging Face Hub tokenizer/config/weight files and optionally convert weights into LitGPT format.

```bash
litgpt download REPO_ID
litgpt download REPO_ID --checkpoint_dir checkpoints --convert_checkpoint true
litgpt download REPO_ID --tokenizer_only true
litgpt download REPO_ID --model_name SUPPORTED_CONFIG_NAME
litgpt download list
```

Key arguments:

- `repo_id`: Hub repository id such as `org/name`; `list` prints supported LitGPT Hub repos.
- `--access_token`: optional token for restricted repositories; avoid writing tokens into logs.
- `--tokenizer_only true`: downloads tokenizer/config files without weights for pretraining or tokenizer inspection.
- `--convert_checkpoint false`: leaves downloaded `.bin` or `.safetensors` files unconverted for later `convert_to_litgpt`.
- `--dtype`: optional conversion dtype name used during conversion.
- `--checkpoint_dir`: parent output directory; downloaded files are placed under `CHECKPOINT_DIR/REPO_ID`.
- `--model_name`: use an existing LitGPT config for alternative weights with a compatible architecture.

Notes:

- Unsupported `repo_id` without `--model_name` is rejected with guidance to run `litgpt download list` or provide a compatible config name.
- The downloader looks for `.bin` or `.safetensors` weight files unless `--tokenizer_only true` is set.
- Gated or missing repos fail before conversion; fix access/token/repo id first.

## `litgpt validate`

Purpose: pre-flight check a LitGPT checkpoint directory without running generation or training.

```bash
litgpt validate CHECKPOINT_DIR
litgpt validate CHECKPOINT_DIR --model_filename lit_model.pth
litgpt validate CHECKPOINT_DIR --dtype bfloat16 --training true
```

Validation steps:

1. Directory structure: `model_config.yaml`, tokenizer files, and the requested model file.
2. Model config load with `Config`.
3. Tokenizer load and a small encode/decode check.
4. Checkpoint key and shape validation against `GPT(config)` on meta tensors.
5. Memory estimate for inference or training using the requested dtype.

Use `--model_filename lit_model.pth.lora` only for LoRA layout validation; use `merge_lora` before treating the checkpoint as normal merged weights.

## `litgpt convert_to_litgpt`

Purpose: convert Hugging Face Transformers weights into LitGPT `lit_model.pth` plus `model_config.yaml`.

```bash
litgpt convert_to_litgpt CHECKPOINT_DIR
litgpt convert_to_litgpt CHECKPOINT_DIR --model_name Llama-3-8B
litgpt convert_to_litgpt CHECKPOINT_DIR --dtype bfloat16
litgpt convert_to_litgpt CHECKPOINT_DIR --debug_mode true
```

Required input:

- HF weight files: `.bin` or `.safetensors`, optionally with `pytorch_model.bin.index.json` or `model.safetensors.index.json`.
- A supported LitGPT config name. By default, LitGPT uses the checkpoint directory basename; pass `--model_name` for alternate weights or non-matching directory names.

Output:

- `model_config.yaml`
- `lit_model.pth`
- Existing tokenizer/config files remain in the directory.

Common failure signals:

- `Expected ... to contain .bin or .safetensors files`: the directory is tokenizer-only, already converted, or not an HF checkpoint root.
- `ValueError` for unsupported config name: run `litgpt download list`, choose a compatible supported architecture, or add model support in LitGPT before converting.

## `litgpt convert_from_litgpt`

Purpose: convert merged LitGPT weights into a Hugging Face-style output directory.

```bash
litgpt convert_from_litgpt CHECKPOINT_DIR OUTPUT_DIR
```

Required input:

- `model_config.yaml`
- `lit_model.pth`
- Non-LoRA, non-adapter model state keys.

Output:

- `OUTPUT_DIR/model.pth` with Hugging Face-style key names for supported architectures.

Limitations:

- LoRA weights cannot be converted directly; run `litgpt merge_lora CHECKPOINT_DIR` first.
- Adapter or adapter-v2 checkpoints are not supported by this converter.
- Copy tokenizer/config files into the output if the downstream consumer requires them.

## `litgpt convert_pretrained_checkpoint`

Purpose: export a checkpoint produced by pretraining into a model-only LitGPT checkpoint usable by inference/evaluation/conversion.

```bash
litgpt convert_pretrained_checkpoint CHECKPOINT_DIR OUTPUT_DIR
```

Required input:

- `CHECKPOINT_DIR/lit_model.pth` containing a training checkpoint with a `model` state dict.
- Config/tokenizer files in the checkpoint directory if downstream loading needs them.

Output:

- `OUTPUT_DIR/lit_model.pth` with model weights only.
- Copied config/tokenizer files when present.

Caution: the output directory must be empty or absent; LitGPT refuses to overwrite a non-empty output directory.

## `litgpt merge_lora`

Purpose: merge LoRA adapter weights into base model weights and write a normal `lit_model.pth` in the LoRA checkpoint directory.

```bash
litgpt merge_lora LORA_CHECKPOINT_DIR
litgpt merge_lora LORA_CHECKPOINT_DIR --pretrained_checkpoint_dir BASE_CHECKPOINT_DIR
litgpt merge_lora LORA_CHECKPOINT_DIR --precision bf16-mixed
```

Required LoRA input:

- `model_config.yaml`
- `lit_model.pth.lora`
- tokenizer files
- `hyperparameters.yaml` with `lora_*` fields and `checkpoint_dir` metadata

Behavior:

- If `lit_model.pth` already exists in the LoRA directory, LitGPT reports that weights are already merged and exits.
- If `--pretrained_checkpoint_dir` is not supplied, LitGPT reads the base checkpoint path from `hyperparameters.yaml`.
- If `--precision` is not supplied, LitGPT uses precision from `hyperparameters.yaml` when available.

## Choosing commands by checkpoint state

| State | Signals | Next command |
| --- | --- | --- |
| Supported remote Hub model | `REPO_ID` appears in `litgpt download list` | `litgpt download REPO_ID` |
| Alternate compatible Hub weights | Hub repo not listed but architecture matches a supported config | `litgpt download REPO_ID --model_name CONFIG_NAME` |
| HF local checkpoint | `.bin`/`.safetensors`, tokenizer/config files, no `lit_model.pth` | `litgpt convert_to_litgpt CHECKPOINT_DIR --model_name CONFIG_NAME` |
| LitGPT ready checkpoint | `model_config.yaml`, tokenizer files, `lit_model.pth` | `litgpt validate CHECKPOINT_DIR` |
| LoRA output | `lit_model.pth.lora`, `hyperparameters.yaml` | `litgpt merge_lora CHECKPOINT_DIR` |
| Pretraining output | `lit_model.pth` contains training wrapper metadata | `litgpt convert_pretrained_checkpoint CHECKPOINT_DIR OUTPUT_DIR` |
| Merged LitGPT to HF export | ready LitGPT checkpoint, no LoRA/adapter keys | `litgpt convert_from_litgpt CHECKPOINT_DIR OUTPUT_DIR` |

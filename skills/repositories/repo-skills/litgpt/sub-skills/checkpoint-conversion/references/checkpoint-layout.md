# Checkpoint Layout Reference

LitGPT checkpoint tasks often fail because the path points to the wrong directory level or to a directory in the wrong format. Use this reference and `scripts/check_checkpoint_layout.py` before running heavyweight commands.

## LitGPT ready checkpoint

Minimum files for normal validation, inference, evaluation, or HF export:

```text
CHECKPOINT_DIR/
  model_config.yaml
  lit_model.pth
  tokenizer.json OR tokenizer.model
  tokenizer_config.json
```

Optional but common files:

- `generation_config.json`: tokenizer/generation metadata used by some models.
- `config.json`: original Hugging Face config retained from download/conversion.

Recommended check:

```bash
python scripts/check_checkpoint_layout.py CHECKPOINT_DIR --mode inference --json
litgpt validate CHECKPOINT_DIR
```

## Hugging Face checkpoint needing conversion

Common signals:

```text
CHECKPOINT_DIR/
  config.json
  tokenizer.json OR tokenizer.model
  tokenizer_config.json
  model-00001-of-00002.safetensors
  model.safetensors.index.json
```

or:

```text
CHECKPOINT_DIR/
  pytorch_model.bin
  tokenizer.json
  tokenizer_config.json
```

There is no `lit_model.pth` yet. Convert with:

```bash
litgpt convert_to_litgpt CHECKPOINT_DIR --model_name SUPPORTED_CONFIG_NAME
```

If the directory name is already a valid LitGPT config name, `--model_name` can be omitted. For alternative compatible weights, pass the matching supported config explicitly.

## Tokenizer-only directory

Signals:

```text
CHECKPOINT_DIR/
  tokenizer.json OR tokenizer.model
  tokenizer_config.json
```

No `.bin`, `.safetensors`, or `lit_model.pth` files exist. This is valid for tokenizer-only workflows such as pretraining from scratch, but it is not enough for inference, validation, merge, or conversion to HF.

## LoRA checkpoint directory

Expected files after `litgpt finetune_lora` final output:

```text
LORA_CHECKPOINT_DIR/
  model_config.yaml
  lit_model.pth.lora
  tokenizer.json OR tokenizer.model
  tokenizer_config.json
  hyperparameters.yaml
```

`hyperparameters.yaml` should include:

- `checkpoint_dir`: base checkpoint directory used for fine-tuning.
- `precision`: optional precision for merge.
- `lora_*`: LoRA configuration keys such as `lora_r`, `lora_alpha`, target module booleans, and dropout.

Check metadata without loading weights:

```bash
python scripts/check_lora_metadata.py LORA_CHECKPOINT_DIR --json
```

Merge with:

```bash
litgpt merge_lora LORA_CHECKPOINT_DIR
```

If the base checkpoint moved, add:

```bash
litgpt merge_lora LORA_CHECKPOINT_DIR --pretrained_checkpoint_dir BASE_CHECKPOINT_DIR
```

After merge, `LORA_CHECKPOINT_DIR/lit_model.pth` appears and the directory can be treated as a normal LitGPT checkpoint.

## Pretraining or training checkpoint

A pretraining checkpoint can have `lit_model.pth` that contains a wrapper with a `model` state dict plus training metadata. Export model-only weights before downstream loading when needed:

```bash
litgpt convert_pretrained_checkpoint CHECKPOINT_DIR OUTPUT_DIR
```

Then validate `OUTPUT_DIR` if config/tokenizer files were copied or supplied:

```bash
litgpt validate OUTPUT_DIR
```

## HF export output

`litgpt convert_from_litgpt CHECKPOINT_DIR OUTPUT_DIR` writes:

```text
OUTPUT_DIR/
  model.pth
```

Copy tokenizer/config files when the downstream Hugging Face consumer expects them. Do not feed LoRA or adapter state directly to this command.

## Directory-level mistakes

| Symptom | Likely path mistake | Fix |
| --- | --- | --- |
| Missing all required files | Parent directory such as `checkpoints/` passed instead of `checkpoints/org/model` | Pass the model leaf directory. |
| Missing `model_config.yaml` only | Raw HF directory not converted yet | Run `convert_to_litgpt` with a supported config name. |
| Missing tokenizer files | Weight-only directory or copied partial output | Copy tokenizer files from the matching download or redownload tokenizer-only. |
| Missing `lit_model.pth` but has `.bin`/`.safetensors` | HF format | Run `convert_to_litgpt`. |
| Missing `lit_model.pth` but has `lit_model.pth.lora` | LoRA output | Run `merge_lora` after metadata/base checkpoint checks. |
| Has `lit_model.pth.lora` but no `hyperparameters.yaml` | Incomplete or manually copied LoRA output | Recover metadata from the training command/logs, then pass `--pretrained_checkpoint_dir` if base path cannot be inferred. |

## Classification checklist

1. Is the path a directory? If not, stop and locate the checkpoint root.
2. Does it have `model_config.yaml` and `lit_model.pth`? It is probably LitGPT-ready.
3. Does it have `lit_model.pth.lora`? It is LoRA output; inspect metadata before merge.
4. Does it have `.bin` or `.safetensors` files? It is likely HF format needing `convert_to_litgpt`.
5. Does it only have tokenizer files? It is tokenizer-only, not model-ready.
6. Does `model_config.yaml` load but validation reports shape/key mismatches? The model config does not match the weights; use the correct `--model_name` or matching base checkpoint.

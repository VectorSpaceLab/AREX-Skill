# Model Configs and Support

LitGPT conversion and validation depend on matching the checkpoint weights to a supported `Config`. A layout can be complete but still fail if the config name or architecture is wrong.

## Config lookup APIs

Use these LitGPT APIs in Python plans or diagnostics:

```python
from litgpt import Config, GPT

config = Config.from_name("pythia-14m")
config = Config.from_file("model_config.yaml")
config = Config.from_checkpoint(checkpoint_dir)
model = GPT(config)
```

Behavior to rely on:

- `Config.from_name(NAME)` loads a built-in supported model config; unsupported names raise `ValueError`.
- `Config.from_file(PATH)` loads a YAML file into `Config`; empty or malformed config files fail early.
- `Config.from_checkpoint(DIR)` first reads `DIR/model_config.yaml`; if absent, it tries to match `DIR.name` to a built-in config name; otherwise it raises `FileNotFoundError`.
- `GPT(config)` builds the LitGPT model architecture for validation or loading; `litgpt validate` uses a meta-device construction path for key/shape checks.

## Supported-name strategy

Use CLI listing for user-facing support decisions:

```bash
litgpt download list
```

If a repo is listed, prefer:

```bash
litgpt download ORG/NAME
```

If a repo is not listed but is a fine-tune or alternate release of a supported architecture, choose the compatible LitGPT config:

```bash
litgpt download OTHER_ORG/ALT_WEIGHTS --model_name Mistral-7B-v0.1
litgpt convert_to_litgpt CHECKPOINT_DIR --model_name Mistral-7B-v0.1
```

Do not guess across architectures. A Llama-family fine-tune should use a matching Llama config, a Mistral fine-tune should use a matching Mistral config, and so on. When unsure, inspect the HF `config.json` architecture/model type and compare hidden size, layers, heads, vocab, rotary settings, and MLP style against the candidate LitGPT config.

## `model_config.yaml` essentials

A LitGPT `model_config.yaml` normally records fields needed to instantiate the architecture, including:

- `name`
- `n_layer`
- `n_embd`
- `n_head`
- `vocab_size`
- `padding_multiple` / padded vocab behavior
- `block_size`
- MLP, norm, rotary, query-group, and head-size fields as required by the architecture

When `litgpt validate` reports key or shape mismatches, suspect one of:

- wrong `--model_name` during `download` or `convert_to_litgpt`;
- mismatched base checkpoint for a LoRA merge;
- copied `model_config.yaml` from a different model size;
- unsupported HF architecture or a newer variant whose mapping is not implemented;
- converted training checkpoint that still contains wrapper metadata.

## Conversion support boundaries

`convert_to_litgpt` supports the architectures implemented by LitGPT's HF-to-LitGPT mapping. It reads `.bin` or `.safetensors` files, writes `model_config.yaml`, and writes `lit_model.pth`.

`convert_from_litgpt` supports merged LitGPT weights for implemented architecture families. It rejects:

- LoRA keys: merge with `litgpt merge_lora` first.
- Adapter or adapter-v2 keys: direct HF conversion is not supported.

`convert_pretrained_checkpoint` is for LitGPT pretraining outputs whose checkpoint contains training metadata and a nested `model` state dict. It writes a model-only LitGPT checkpoint, not a Hugging Face checkpoint.

## Tokenizer/config coupling

LitGPT tokenizer loading expects one of:

- `tokenizer.json` plus `tokenizer_config.json` for Hugging Face tokenizer backend; or
- `tokenizer.model` plus `tokenizer_config.json` for sentencepiece-style tokenizer backend.

`generation_config.json` can supply special-token metadata for some models. Tokenizer problems are separate from weight conversion: a checkpoint can have valid weights and still fail validation or generation because tokenizer files are missing, incompatible, or manually copied from a different model family.

## Safe support-check workflow

1. Run `python scripts/check_checkpoint_layout.py CHECKPOINT_DIR --json` to classify files.
2. If local Python with LitGPT is available, check config support without loading weights:

```bash
python - <<'PY'
from litgpt import Config
print(Config.from_name("pythia-14m"))
PY
```

3. For a local LitGPT directory, load config only:

```bash
python - <<'PY'
from pathlib import Path
from litgpt import Config
checkpoint_dir = Path("CHECKPOINT_DIR")
config = Config.from_checkpoint(checkpoint_dir)
print(config.name, config.n_layer, config.n_embd, config.n_head)
PY
```

4. Run `litgpt validate CHECKPOINT_DIR` only after layout and config support look correct.
5. If validation fails on memory only, the checkpoint layout/config may still be correct; route runtime choices to inference/training/evaluation guidance.

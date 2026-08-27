# Checkpoint Troubleshooting

Use this matrix after running `scripts/check_checkpoint_layout.py`, `scripts/check_lora_metadata.py`, or `litgpt validate`. Commands and messages are summarized from current LitGPT CLI behavior, source checks, and tests.

## Layout and path errors

| Symptom | Meaning | Fix |
| --- | --- | --- |
| `checkpoint_dir ... is not a checkpoint directory` | Path does not exist or points to a file/parent directory. | Pass the leaf checkpoint directory, often `checkpoints/org/model`. |
| Missing `model_config.yaml` | Directory is raw HF format, tokenizer-only, or incomplete. | Run `litgpt convert_to_litgpt CHECKPOINT_DIR --model_name CONFIG_NAME`, or copy the matching config from a valid LitGPT conversion. |
| Missing `tokenizer.json OR tokenizer.model` | Tokenizer files were not downloaded/copied. | Redownload with `litgpt download REPO_ID --tokenizer_only true` or copy tokenizer files from the matching model. |
| Missing `tokenizer_config.json` | Tokenizer metadata is incomplete. | Restore from the matching HF/LitGPT checkpoint; do not mix tokenizer configs across model families. |
| Missing `lit_model.pth` | Directory is raw HF, tokenizer-only, LoRA-only, or pre-merge output. | If HF weights exist, run `convert_to_litgpt`; if `lit_model.pth.lora` exists, run `merge_lora`; otherwise download/locate weights. |

## Download failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| Unsupported `repo_id` | Repo is not in LitGPT's supported Hub list. | Run `litgpt download list`; for compatible alternate weights, pass `--model_name SUPPORTED_CONFIG_NAME`. |
| Repository not found | Repo id is wrong or inaccessible. | Check spelling and Hub visibility. |
| Gated repo error without token | Model requires authentication. | Set `HF_TOKEN` securely or pass `--access_token` without logging it. |
| Gated repo error with token | Token lacks access or terms were not accepted. | Confirm access on the model page and retry with a token that has permission. |
| No `.bin` or `.safetensors` found | Repo lacks standard weight files or only tokenizer files were requested. | Check the Hub repo files; use `--tokenizer_only true` only when no weights are needed. |
| Network unavailable | Download cannot reach Hub. | Stop before conversion; retry in a networked environment or use an already downloaded local checkpoint. |

## HF-to-LitGPT conversion failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| Expected directory to contain `.bin` or `.safetensors` | Wrong directory or no HF weight files. | Point to the HF checkpoint root, not the parent; redownload weights if needed. |
| Invalid/unsupported config name | `Config.from_name` cannot find the model. | Use `litgpt download list` and pass a supported `--model_name`, or add LitGPT support before converting. |
| Shape/key mismatch after conversion | Config does not match weights. | Reconvert with the correct `--model_name`; verify model size, heads, layers, vocab, and architecture family. |
| Conversion runs out of memory or disk | Weight loading/conversion is large. | Use a machine with enough RAM/disk; try a smaller dtype when appropriate; avoid converting huge models during lightweight verification. |

## LitGPT validation failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| Config load fails | `model_config.yaml` is missing, empty, malformed, or incompatible. | Restore from conversion/download; verify YAML fields. |
| Tokenizer load fails | Missing or malformed tokenizer files. | Restore `tokenizer.json`/`tokenizer.model` and `tokenizer_config.json` from the same model. |
| Checkpoint key or shape validation fails | Weights do not match `GPT(config)`. | Use the correct config/base checkpoint; reconvert or remerge from matching inputs. |
| Memory estimate exceeds GPU memory | Layout may be valid but runtime hardware is insufficient. | Use lower precision/quantization or smaller model; route runtime planning to the appropriate inference/training/evaluation sub-skill. |
| No GPU detected | Validation skips memory fit check. | Treat as a CPU inspection result only; do not infer GPU readiness. |

## LoRA merge failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| Missing `lit_model.pth.lora` | Directory is not a LoRA output or the adapter file was not copied. | Locate the final LoRA checkpoint directory from training output. |
| Missing `hyperparameters.yaml` | Metadata needed to infer base checkpoint and LoRA settings is absent. | Recover from training logs/config; pass `--pretrained_checkpoint_dir BASE_CHECKPOINT_DIR` and recreate metadata when possible. |
| `checkpoint_dir` in metadata points to missing base | Base checkpoint was moved or path is not valid in this environment. | Run `litgpt merge_lora LORA_DIR --pretrained_checkpoint_dir BASE_CHECKPOINT_DIR`. |
| Missing `lora_*` keys | Metadata is incomplete or not from LitGPT LoRA training. | Recover original LoRA hyperparameters; do not merge until target modules/rank/alpha are known. |
| `lit_model.pth` already exists | LoRA directory has already been merged. | Validate the merged directory; avoid overwriting unless the user intentionally regenerates it. |
| Shape mismatch during merge | LoRA adapter and base checkpoint/config do not match. | Use the exact base model used for LoRA training and the matching `model_config.yaml`. |

## LitGPT-to-HF export failures

| Symptom | Meaning | Fix |
| --- | --- | --- |
| LoRA weights cannot be converted | `convert_from_litgpt` saw LoRA keys. | Run `litgpt merge_lora CHECKPOINT_DIR` first, then export. |
| Adapter conversion not supported | Adapter or adapter-v2 keys are present. | Do not use this converter for adapter checkpoints; use LitGPT inference paths or another export strategy. |
| Output lacks tokenizer files | Converter writes weights, not necessarily full HF packaging. | Copy tokenizer/config files from the matching checkpoint when downstream tools need them. |

## Difficult case playbooks

### LoRA directory has `lit_model.pth.lora` but no `hyperparameters.yaml`

1. Run `python scripts/check_lora_metadata.py LORA_DIR --json` to confirm missing metadata without loading weights.
2. Identify the base checkpoint used in training from the training command, logs, or recipe.
3. Reconstruct required LoRA fields (`lora_r`, `lora_alpha`, target booleans, dropout) from the same source if possible.
4. If only the base path moved but metadata can be recovered, run `litgpt merge_lora LORA_DIR --pretrained_checkpoint_dir BASE_CHECKPOINT_DIR` after restoring metadata.
5. If LoRA hyperparameters cannot be recovered, do not merge blindly; the adapter cannot be safely interpreted.

### Decide whether a directory is LitGPT, HF, or training/LoRA output

1. `model_config.yaml` + `lit_model.pth` + tokenizer files: LitGPT-ready; run `litgpt validate`.
2. `.bin`/`.safetensors` + tokenizer/config files + no `lit_model.pth`: HF format; run `convert_to_litgpt` with a supported config.
3. `lit_model.pth.lora`: LoRA output; inspect metadata and merge before normal use or HF export.
4. `lit_model.pth` contains nested training metadata or came from pretraining output: run `convert_pretrained_checkpoint` to export model-only weights.
5. Tokenizer files only: not enough for model loading; use only for tokenizer/pretraining-from-scratch tasks.

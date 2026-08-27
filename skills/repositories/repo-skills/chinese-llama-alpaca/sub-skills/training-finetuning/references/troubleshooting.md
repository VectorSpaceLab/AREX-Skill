# Training and Fine-Tuning Troubleshooting

Use this matrix before rerunning long jobs. Prefer validating data and command construction with the bundled helper and templates before changing model weights, caches, or output directories.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `invalid JSON` from the validator | SFT file is malformed JSON. | Fix the JSON and rerun `python scripts/validate_training_data.py --mode sft --input <file>`. Keep a top-level JSON list. |
| `top-level JSON value must be a list` | SFT data is a dict, object with nested data, or JSONL when a list is expected. | Convert to a JSON list of records with `instruction`, `input`, and `output`. |
| `missing required field 'instruction'`, `'input'`, or `'output'` | Record does not match the SFT schema used by `build_dataset.py`. | Add all three fields. Use `"input": ""` when no context exists. |
| `field 'output' must be a string` or similar | A field is a list, dict, number, `null`, or boolean. | Convert each field to a string before training; do not store structured answers directly. |
| Empty instruction or output | Record has blank supervision text. | Remove the record or provide meaningful task/answer text. |
| PT validator says text is empty, whitespace, or extremely short | Wrong file, wrong mode, or placeholder text. | Use UTF-8 `.txt` files with real raw training text under the PT data directory. |
| SFT script raises tokenizer vocab size must be `49954` | A LLaMA/Chinese LLaMA tokenizer was used for Chinese Alpaca SFT. | Use the Chinese Alpaca tokenizer matching the adapter/model family. Alpaca tokenizers differ from LLaMA tokenizers. |
| PT script rejects model/tokenizer vocabulary combination | Base model embedding size and tokenizer length are not one of the allowed PT combinations. | Recheck whether the task is original LLaMA continuation, Chinese LLaMA vocabulary expansion, Chinese LLaMA continuation, or Chinese Alpaca continuation. Use matching model/tokenizer assets. |
| `tokenizer.pad_token is None` or padding errors during SFT | Tokenizer lacks a pad token or model embeddings do not match after adding one. | The SFT script adds `[PAD]` and resizes embeddings when needed. Keep `modules_to_save=embed_tokens,lm_head` so embedding/head changes are saved. |
| Unexpected EOS/answer truncation | `tokenizer.eos_token` missing/changed or `--max_seq_length` too small. | Confirm tokenizer has the expected EOS token and increase `MAX_SEQ_LENGTH` only after GPU memory review. |
| Old examples appear after changing data or tokenizer | Stale datasets cache. | For PT, use a new `DATA_CACHE_DIR` or remove filename-derived cache folders. For SFT, remove filename-stem cache folders next to JSON files. |
| Datasets cache load fails or reports Arrow/corruption errors | Interrupted preprocessing or incompatible cached data. | Delete the affected processed cache directory and rerun preprocessing. Keep source JSON/TXT separate from caches. |
| `Output directory (...) already exists and is not empty` | `OUTPUT_DIR` has files and neither resume nor overwrite was selected. | Use a new output directory, set `RESUME_FROM_CHECKPOINT` to a valid checkpoint, or set `OVERWRITE_OUTPUT_DIR=true` only if replacing outputs is intended. |
| Training resumes unexpectedly | A last checkpoint was detected in `OUTPUT_DIR`. | Use a fresh `OUTPUT_DIR`, set `OVERWRITE_OUTPUT_DIR=true`, or explicitly set `RESUME_FROM_CHECKPOINT` so the behavior is intentional. |
| `deepspeed` command/module missing | DeepSpeed is not installed in the runtime environment. | Install a compatible DeepSpeed build for the approved environment or remove `--deepspeed` for a small debug run. Removing DeepSpeed changes memory behavior. |
| DeepSpeed JSON parse/config error | Edited config invalid or path points to the wrong file. | Validate [`templates/ds_zero2_no_offload.json`](../templates/ds_zero2_no_offload.json) as JSON and pass its path through `DEEPSPEED_CONFIG_FILE`. |
| CUDA out of memory | Model size, sequence length, batch size, LoRA target breadth, or worker count exceeds available memory. | Reduce `PER_DEVICE_TRAIN_BATCH_SIZE`, `BLOCK_SIZE`/`MAX_SEQ_LENGTH`, `NPROC_PER_NODE`, or LoRA target modules; keep gradient checkpointing; consider smaller model/adapters. |
| Training is very slow on CPU | Full training was launched without usable GPU. | Stop and confirm GPU availability/approval. CPU may validate scripts and data but is not a practical substitute for full 7B+ training. |
| `ModuleNotFoundError: datasets`, `peft`, `sentencepiece`, or `transformers` | Missing runtime dependencies. | Install the package requirements compatible with `torch`, `transformers`, PEFT, `datasets`, and `sentencepiece` before running training scripts. |
| PT script `--help` fails around `transformers.testing_utils` or pytest | Older Transformers testing utilities can be sensitive to pytest major versions. | Use a compatible pytest version such as `pytest<8` for parser/help inspection, or rely on static option tables in [`api-reference.md`](api-reference.md). |
| `--peft_path` does not resume optimizer state | `--peft_path` loads adapter weights only. | Use `RESUME_FROM_CHECKPOINT` / `--resume_from_checkpoint` for Trainer optimizer/scheduler state. Use both only when the intent is clear. |
| Final output does not contain full model weights | `SavePeftModelCallback` saves PEFT adapters/tokenizer, not original full LLaMA weights. | Expect `pt_lora_model` or `sft_lora_model`; merge/load adapters later through model-reconstruction or inference guidance. |
| `force_resize_embeddings` seems ineffective | The SFT dataclass parses `--force_resize_embeddings`, but this script version resizes embeddings automatically on tokenizer/model mismatch and does not branch on the flag. | Treat it as a compatibility option. Solve real resize issues by matching tokenizer/model family and keeping `modules_to_save=embed_tokens,lm_head`. |
| Missing model path or tokenizer path | Required environment variables were not set before running a template. | Set `MODEL_NAME_OR_PATH` and `TOKENIZER_NAME_OR_PATH` to user-provided model/tokenizer paths or model ids. Do not hard-code private checkout paths in templates. |
| Training command accidentally starts a large job | Template was executed after required variables were set. | Stop the job if not approved. Future agents should ask for explicit model/data/GPU/cost approval before executing `templates/run_pt.sh` or `templates/run_sft.sh`. |

## Quick Isolation Checklist

1. Run the validator in the correct mode on the exact file or directory.
2. Check model/tokenizer family and vocabulary size expectations.
3. Use a fresh output directory and fresh or intentionally reused cache directory.
4. Print the template command and inspect `--dataset_dir`, `--data_cache_dir`, `--output_dir`, `--block_size`/`--max_seq_length`, LoRA parameters, and DeepSpeed path.
5. Only then launch a bounded `MAX_STEPS` smoke run, and only with explicit approval.

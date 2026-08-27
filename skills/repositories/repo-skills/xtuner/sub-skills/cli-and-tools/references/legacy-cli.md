# Legacy XTuner CLI and tool reference

This reference covers the old top-level `xtuner MODE ...` router and adjacent legacy utilities. Treat these commands as distinct from XTuner V1 direct SFT/RL CLIs.

## Legacy vs V1 triage

| If the task mentions... | Use this sub-skill? | Action |
|---|---:|---|
| `xtuner list-cfg`, `copy-cfg`, `log-dataset`, `check-custom-dataset`, old config names such as `internlm_7b_qlora_alpaca_e3` | Yes | Use legacy config/tool guidance below. |
| `xtuner convert pth_to_hf`, `convert merge`, `convert split` | Yes | Plan from [model conversion](model-conversion.md); execute only with explicit local paths and resources. |
| `xtuner chat`, `mmbench`, `eval_refcoco`, `preprocess arxiv`, `preprocess refcoco` | Yes | Require model/data assets; see safety notes below. |
| Direct `sft.py` or `rl.py`, `--model-cfg`, `--chat_template`, V1 config classes, GRPO/Ray rollout, FSDP/TP/EP/HSDP | No | Route to the V1 sub-skills. |
| JSONL schema, media records, tokenization, packing, cache tags | Usually no | Route to `data-preparation`; use this only for old preprocess command shapes. |

## Entry router behavior

The legacy router accepted this shape:

```bash
xtuner MODE [MODE_ARG] [ARGS]
```

Recognized modes were:

```text
list-cfg, copy-cfg, log-dataset, check-custom-dataset, train, test, chat,
convert, preprocess, mmbench, eval_refcoco, list-dataset-format
```

Important packaging caveat: the current package metadata may not install a console script named `xtuner`. If `command -v xtuner` fails, do not assume the command is usable from an installed wheel. For V1 workflows, route to the V1 direct CLIs. For true legacy workflows, ask the user for an environment that exposes the legacy console command or use the bundled helpers in this generated skill for config discovery; do not rely on source-tree script paths.

The legacy router also inspected distributed environment variables. If `NNODES` or `NPROC_PER_NODE` indicated more than one process and `--launcher slurm` was not supplied, it wrapped the selected tool in `torchrun` and appended `--launcher pytorch`. For a local non-distributed dry run, make the single-process intent explicit:

```bash
NNODES=1 NPROC_PER_NODE=1 xtuner list-cfg -p qlora
```

## Command surface summary

| Mode | Command shape | Main inputs and notes |
|---|---|---|
| List configs | `xtuner list-cfg [-p PATTERN]` | Prints predefined legacy config names. `PATTERN` is a case-insensitive substring over config names. Prefer the bundled helper when the console entry point is missing. |
| Copy config | `xtuner copy-cfg CONFIG_NAME SAVE_DIR` | Copies the selected config into `SAVE_DIR` with `_copy` before the extension. The legacy implementation looked up `CONFIG_NAME` in its package config map. |
| Log dataset | `xtuner log-dataset CONFIG [--show text|masked_text|input_ids|labels|all]` | Builds the tokenizer and training dataset from a legacy config, then prints decoded text, masked text, token ids, and/or labels for the first item. Requires all dataset/model config imports to work. |
| Check custom dataset | `xtuner check-custom-dataset CONFIG` | Validates the custom SFT JSON/data mapping path in a legacy config, including standard conversation shape and map/template functions. Heavy imports and dataset loading are expected. |
| Train legacy config | `xtuner train CONFIG [--work-dir DIR] [--deepspeed JSON] [--resume PATH] [--seed N] [--cfg-options KEY=VALUE ...] [--launcher none|pytorch|slurm|mpi]` | Old training stack. Route V1 direct training to `training`; do not conflate this with V1 SFT. |
| Test legacy config | `xtuner test CONFIG [--checkpoint PATH] [--work-dir DIR] [--cfg-options KEY=VALUE ...] [--launcher none|pytorch|slurm|mpi]` | Old test/eval runner for legacy configs. Requires checkpoint and compatible config. |
| Chat | `xtuner chat MODEL [--adapter ADAPTER | --llava LLAVA] [--visual-encoder PATH] [--image IMAGE] [--prompt-template NAME] [--system TEXT | --system-template NAME] ...` | Loads a HuggingFace model or VLM stack. Can use 4/8-bit flags, plugins, lagent, generation settings, and offload folders. Requires local or downloadable assets. |
| Model conversion | `xtuner convert pth_to_hf ...`, `xtuner convert merge ...`, `xtuner convert split ...` | Reference-only here. See [model conversion](model-conversion.md). |
| Preprocess arXiv | `xtuner preprocess arxiv SRC_FILE DST_FILE [--categories CAT ...] [--start-date YYYY-MM-DD]` | Reads newline-delimited arXiv JSON records, filters by `categories` intersection and `update_date`, writes a JSON array. Defaults targeted CS AI/CL/CV categories from 2020-01-01. |
| Preprocess RefCOCO | `xtuner preprocess refcoco --ann-path ANN_DIR --image-path IMAGE_DIR --save-path OUT_DIR` | Converts RefCOCO/RefCOCO+/RefCOCOg annotations into a train JSON under `OUT_DIR`. Requires the annotation and image layout locally. |
| MMBench | `xtuner mmbench MODEL --llava LLAVA [--visual-encoder PATH] --data-path TSV [--work-dir DIR] ...` | Loads an LLM+LLaVA visual stack and a benchmark TSV with encoded images/questions. GPU/model assets are normally required. |
| RefCOCO eval | `xtuner eval_refcoco MODEL --llava LLAVA [--visual-encoder PATH] --data-path DATA [--work-dir DIR] ...` | Loads a VLM stack and RefCOCO data, then computes IoU-style results. Requires local benchmark data and images. |
| Dataset formats | `xtuner list-dataset-format` | Prints legacy dataset format mapping keys. For V1 JSONL schemas, route to `data-preparation`. |

## Safe legacy config discovery

The original config map scanned the package's config directory and mapped file stems to `.py` or `.json` paths, skipping hidden and underscore-prefixed files. The generated skill does not bundle that config zoo. Ask the user for an explicit config root, then use:

```bash
python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs qlora alpaca --limit 20
python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs --match-mode any reward dpo --format names
python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs --family internlm qlora oasst1
```

Copy only after the filters select exactly one config:

```bash
python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs --exact internlm_7b_qlora_alpaca_e3 --copy-to ./configs
```

Expected behavior:

- Matching is case-insensitive over config names, first-level families, and relative paths.
- Default token mode is `all`, which is useful for difficult searches such as `qlora alpaca`.
- The helper does not read config file bodies and does not import XTuner.
- If the root is unavailable, ask for an exported config-zoo directory or an installed package directory that actually contains the old configs.

## HuggingFace `Trainer` examples

XTuner also had example scripts that used XTuner API helpers inside the standard HuggingFace `Trainer` flow. These are legacy examples, not V1 engine launches.

| Example style | Builder used | Required high-level args |
|---|---|---|
| Full fine-tuning | `build_model` | `--model_name_or_path`, `--dataset_name_or_path`, plus normal HuggingFace training arguments. |
| LoRA fine-tuning | `build_lora_model` | Same argument pattern; model must support the LoRA setup used by the helper. |
| QLoRA fine-tuning | `build_qlora_model` | Same argument pattern; requires bitsandbytes/quantization support compatible with the local CUDA/runtime stack. |

A typical command shape was:

```bash
python train_qlora_hf.py --model_name_or_path MODEL_OR_PATH --dataset_name_or_path DATASET_OR_PATH --per_device_train_batch_size 1 --learning_rate 2e-5
```

Before recommending execution, confirm that the user has the example script, model assets, dataset assets, and a compatible `transformers`/`bitsandbytes` stack.

## Chat, evaluation, and preprocess safety checklist

- Confirm whether the path is a local model snapshot, a HuggingFace repo id, a checkpoint file, an adapter directory, or benchmark data.
- Do not start downloads or authenticated model access unless the user explicitly approves it.
- For LLaVA-style tasks, distinguish the base LLM path, LLaVA adapter path, optional visual encoder path, image/benchmark data path, and prompt/system template names.
- For benchmark tools, require local benchmark files and an output/work directory; avoid writing into ambiguous current directories.
- For old dataset inspection tools, expect imports of tokenizer, dataset builders, and optional dependencies. Prefer V1 data validators for V1 JSONL tasks.

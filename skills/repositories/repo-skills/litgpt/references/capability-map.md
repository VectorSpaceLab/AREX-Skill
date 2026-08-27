# LitGPT Capability Map

Use this reference to choose the nearest sub-skill and avoid mixing long-running workflows before prerequisites are checked.

## Primary Workflow Routes

| User task | Start here | Read next when needed | Safe first check |
| --- | --- | --- | --- |
| Generate text from a local checkpoint | `sub-skills/inference-chat/` | `sub-skills/checkpoint-conversion/` if layout is uncertain | `python sub-skills/inference-chat/scripts/check_inference_inputs.py --checkpoint-dir CHECKPOINT_DIR` |
| Chat interactively | `sub-skills/inference-chat/` | `sub-skills/checkpoint-conversion/` for tokenizer/prompt layout | `litgpt chat --help` and inference checker |
| Use Python `LLM` API | `sub-skills/inference-chat/` | `sub-skills/checkpoint-conversion/` for checkpoint readiness | Environment check plus API reference |
| Download or classify model files | `sub-skills/checkpoint-conversion/` | `sub-skills/inference-chat/` after ready checkpoint | `python sub-skills/checkpoint-conversion/scripts/check_checkpoint_layout.py CHECKPOINT_DIR` |
| Convert HF checkpoint to LitGPT | `sub-skills/checkpoint-conversion/` | `sub-skills/inference-chat/` or `sub-skills/evaluation-serving/` after validation | Layout checker, then `litgpt convert_to_litgpt --help` |
| Merge LoRA output | `sub-skills/checkpoint-conversion/` | `sub-skills/training-data/` if output origin is unclear | `python sub-skills/checkpoint-conversion/scripts/check_lora_metadata.py CHECKPOINT_DIR` |
| Fine-tune with LoRA/QLoRA/full/adapter | `sub-skills/training-data/` | `sub-skills/checkpoint-conversion/` for base checkpoint and post-training merge | JSON validator and command summarizer |
| Pretrain or continue pretraining | `sub-skills/training-data/` | `sub-skills/checkpoint-conversion/` for tokenizer/checkpoint export | `litgpt pretrain --help` and command summarizer |
| Run LM Harness evaluation | `sub-skills/evaluation-serving/` | `sub-skills/checkpoint-conversion/` for conversion/readiness | `python sub-skills/evaluation-serving/scripts/check_optional_eval_serve_deps.py --mode evaluate` |
| Serve HTTP/OpenAI endpoint | `sub-skills/evaluation-serving/` | `sub-skills/inference-chat/` for local generation alternatives | Optional dependency checker and curl builder |

## Optional Dependency Ownership

| Optional dependency or backend | Owner | Used for | Check before use |
| --- | --- | --- | --- |
| `bitsandbytes` | `inference-chat`, `training-data`, `evaluation-serving` | `bnb.*` quantized inference/training/serving | Environment check or sub-skill checker; confirm CUDA/Linux compatibility |
| `lm_eval` | `evaluation-serving` | `litgpt evaluate` tasks | `check_optional_eval_serve_deps.py --mode evaluate` |
| `litserve` | `evaluation-serving` | `litgpt serve` | `check_optional_eval_serve_deps.py --mode serve` |
| `jinja2` | `evaluation-serving` | OpenAI-compatible serving with chat templates | Optional dependency checker plus tokenizer config review |
| `litdata` | `training-data` | large pretraining data modules | Training data reference and environment check |
| `tensorboard`, `wandb`, `mlflow`, `litlogger` | `training-data` | training logs | Training troubleshooting before choosing logger |
| `transformers`, `datasets`, `sentencepiece`, `pandas`, `pyarrow`, `zstandard` | workflow-specific | conversion, datasets, tokenizers, data prep | Install only for the requested workflow |
| Thunder/XLA extensions | `training-data` with backend caveats | optional accelerated training/generation paths | Treat as backend-specific and verify separately |

## Safe Native Candidate Map

| Candidate | Type | Workflow | Safety | Expected signal | Owner |
| --- | --- | --- | --- | --- | --- |
| `litgpt --help` and subcommand `--help` | CLI help | all | safe-runnable | help exits 0 and lists commands/options | root and sub-skills |
| `scripts/check_litgpt_environment.py` | bundled helper | install/import | safe-runnable | JSON/text reports package and optional dependency status | root |
| `check_inference_inputs.py` | bundled helper | inference | tiny-fixture-runnable | catches invalid sampling/checkpoint layout without model loading | `inference-chat` |
| `validate_json_sft_data.py` | bundled helper | training data | tiny-fixture-runnable | validates JSON/JSONL schema and split layout | `training-data` |
| `summarize_training_command.py` | bundled helper | training command planning | safe-runnable | flags incompatible quantization/resume/data choices | `training-data` |
| `check_checkpoint_layout.py` | bundled helper | checkpoint classification | tiny-fixture-runnable | identifies LitGPT/HF/LoRA layout signals | `checkpoint-conversion` |
| `check_lora_metadata.py` | bundled helper | LoRA merge planning | tiny-fixture-runnable | checks `hyperparameters.yaml` and base checkpoint hints | `checkpoint-conversion` |
| `check_optional_eval_serve_deps.py` | bundled helper | evaluation/serving | safe-runnable | reports optional imports, batch-size, port, and layout hints | `evaluation-serving` |
| `build_curl_examples.py` | bundled helper | serving request planning | safe-runnable | prints simple/streaming/OpenAI curl examples | `evaluation-serving` |

## Expensive Or Skipped Native Candidates

- Real `litgpt download`, HF conversion, checkpoint validation with full weights, LoRA merge, and `LLM.load` can require network, large disk I/O, model weights, or GPU memory.
- Real finetuning/pretraining runs can require downloads, GPUs, long runtime, and user data; use `--print_config`, validators, and tiny fixtures first.
- Real `litgpt evaluate` can download tasks or run large benchmarks; use `--limit` only after optional dependencies and checkpoint layout are ready.
- Real `litgpt serve` starts a long-running process and loads weights; build curl examples and check ports/dependencies before starting it.

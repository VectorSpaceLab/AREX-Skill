# Axolotl Operational Flows

These flows help future agents choose and sequence Axolotl commands safely. They describe command usage only; they do not prove that the local machine has GPUs, optional kernels, vLLM, model weights, datasets, credentials, or enough memory.

## Start With Install and Help Checks

For an unknown environment, run lightweight checks before model work:

```bash
python scripts/check_axolotl_install.py
axolotl --help
axolotl agent-docs --list
axolotl config-schema --field base_model
```

Interpretation:

- Package metadata plus top-level import proves Python can find the package, not the full ML runtime stack.
- `axolotl --help` proves the console entry point is on `PATH` and can import the Click CLI.
- `config-schema` may expose dependency/import problems earlier than training because it imports the config schema.

## Fetch Examples or Docs

Use fetch for examples, DeepSpeed configs, or docs in a user workspace:

```bash
axolotl fetch examples
axolotl fetch examples --dest my-examples
axolotl fetch deepspeed_configs
axolotl fetch docs
```

`fetch` downloads from the public Axolotl repository. Do not run it when the user requires offline-only operation. It writes files under the destination directory or the matching default directory name.

## Preprocess Before Training

Use preprocessing when the task involves dataset shape, tokenization, sample packing, label masking, EOS/EOT behavior, or a new config:

```bash
axolotl preprocess config.yml
axolotl preprocess config.yml --debug
axolotl preprocess config.yml --debug --debug-num-examples 5
```

Operational rules:

- Use `--debug` to inspect tokenized examples before long training.
- Use `--debug-text-only` when the user needs readable text samples rather than token details.
- Deprecated `--iterable` should be replaced by `streaming: true` in YAML or `--streaming` on `axolotl train`.
- Route dataset field decisions such as `datasets.type`, `chat_template`, `field_messages`, and masking to `data-and-configs`.

## Train

Basic training:

```bash
axolotl train config.yml
```

Override config fields from the CLI:

```bash
axolotl train config.yml --learning-rate 1e-4 --micro-batch-size 2 --num-epochs 3
```

Choose a launcher:

```bash
axolotl train config.yml --launcher python
axolotl train config.yml --launcher torchrun -- --nproc_per_node=2 --nnodes=1
axolotl train config.yml --launcher accelerate -- --config_file=accelerate_config.yml
```

Resume or sweep:

```bash
axolotl train config.yml --resume-from-checkpoint path/to/checkpoint
axolotl train config.yml --sweep path/to/sweep.yaml
```

Operational rules:

- The default launcher is `accelerate`.
- `--launcher python` is useful for debugging single-process behavior.
- Put Axolotl overrides before `--`; put `torchrun` or `accelerate launch` args after `--`.
- When Ray is enabled through config/overrides, Axolotl bypasses the launcher wrapper and uses its Python path.
- Route DeepSpeed/FSDP topology, `num_processes`, NCCL, memory budget, and backend performance details to `distributed-and-performance` when present.

## Cloud Runs

Cloud mode uses a separate cloud YAML:

```bash
axolotl preprocess config.yml --cloud cloud_config.yml
axolotl train config.yml --cloud cloud_config.yml
axolotl lm-eval config.yml --cloud cloud_config.yml
```

Operational rules:

- Keep the training config and cloud config distinct.
- Cloud support currently routes through configured providers such as Modal and Baseten; unsupported provider names fail before remote execution.
- Cloud configs can reference environment variables and secrets. Do not print, persist, or synthesize secret values.
- Check path assumptions carefully: cloud execution may mount the config at a provider-specific path inside the remote runtime.

## Evaluate

Use Axolotl's dataset/model evaluation path:

```bash
axolotl evaluate config.yml
axolotl evaluate config.yml --launcher torchrun -- --nproc_per_node=2
```

Use LM Evaluation Harness when the config has `lm_eval_tasks` and related fields:

```bash
axolotl lm-eval config.yml
```

Operational rules:

- `evaluate` loads the Axolotl config, datasets, and model path implied by the config.
- `lm-eval` reads raw YAML fields such as `lm_eval_tasks`, `lm_eval_model`, `lm_eval_batch_size`, and `output_dir` and shells out to `lm_eval`.
- Missing `lm_eval` executable or task names are environment/integration issues, not CLI syntax issues.

## Inference and Chat

Use the same training config for inference and merging:

```bash
axolotl inference config.yml --lora-model-dir ./outputs/lora-out
axolotl inference config.yml --base-model ./completed-model
cat prompt.txt | axolotl inference config.yml --base-model ./completed-model
```

Interactive modes:

```bash
axolotl inference config.yml --chat
axolotl inference config.yml --gradio
```

Operational rules:

- `--chat` and `--gradio` are mutually exclusive.
- Chat mode expects an interactive terminal and a chat template; it does not support legacy `--prompter` mode.
- `/save` in chat writes `chat_template`-format JSONL samples that can become future training data.
- For tokenization mismatches, compare `axolotl preprocess config.yml --debug` against inference prompt formatting.

## Merge LoRA and FSDP Weights

Merge LoRA/QLoRA adapters:

```bash
axolotl merge-lora config.yml
axolotl merge-lora config.yml --lora-model-dir ./outputs/lora-out/checkpoint-100
CUDA_VISIBLE_DEVICES="" axolotl merge-lora config.yml
```

Merge sharded FSDP weights:

```bash
axolotl merge-sharded-fsdp-weights config.yml
axolotl merge-sharded-fsdp-weights config.yml --launcher torchrun -- --nproc_per_node=2
```

Operational rules:

- LoRA merge needs the base model and adapter files referenced by config/CLI.
- CPU merge can avoid GPU memory pressure but may be slower.
- FSDP merge is launcher-aware because checkpoint shards may need distributed context.
- Route adapter target choices and quantization interactions to `model-loading-and-adapters`.

## vLLM Serve for GRPO or EBFT

Start the server and training in separate terminals or process managers:

```bash
CUDA_VISIBLE_DEVICES=0 axolotl vllm-serve grpo_config.yaml
CUDA_VISIBLE_DEVICES=1 axolotl train grpo_config.yaml
```

Multi-GPU server example:

```bash
CUDA_VISIBLE_DEVICES=2,3 axolotl vllm-serve grpo_config.yaml
CUDA_VISIBLE_DEVICES=0,1 axolotl train grpo_config.yaml --num-processes 2
```

Operational rules:

- The vLLM server must serve the same `base_model` as the training config.
- `vllm:` settings control host, port, dtype, tensor/data parallelism, model length, and serve module.
- Axolotl defaults to its LoRA-aware serve module when no `serve_module` is specified.
- Restart vLLM between training runs, after crashes, or when changing the base model.
- Health endpoints differ by serve module; check both `/health/` and `/health` when unsure.
- Route GRPO/EBFT reward and method decisions to `rl-and-rewards`; route GPU topology and performance to `distributed-and-performance`.

## Quantize

Run post-training quantization when the config includes `qat:` or `quantization:` settings:

```bash
axolotl quantize config.yml
axolotl quantize config.yml --base-model ./completed-model --output-dir ./quantized-out
```

Operational rules:

- `quantize` loads model/tokenizer/processor objects and may require GPU/CPU memory, optional torchao support, and model files.
- It rejects configs that specify both QAT and post-training quantization settings.
- It saves the quantized model under the configured output directory.
- Route quantization field choices and model compatibility to `model-loading-and-adapters`.

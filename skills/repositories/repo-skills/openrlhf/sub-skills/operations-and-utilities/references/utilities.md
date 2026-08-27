# Utilities

Use this reference for operational OpenRLHF utility CLIs and scripts. Treat these as runtime actions: they may load large models, start services, require GPUs, modify checkpoint trees, or consume significant disk space.

## Reward Model Serving

OpenRLHF provides `openrlhf.cli.serve_rm`, a FastAPI/uvicorn reward model server. It loads a sequence-regression reward model with `get_llm_for_sequence_regression()`, builds a tokenizer, and exposes:

```text
POST /get_reward
```

The request JSON should include `query`; `prompts` is accepted by the handler but the implementation scores `query` strings. The response contains `rewards`, `scores`, and `extra_logs.dummy_scores`.

Repository example distilled from `examples/scripts/serve_remote_rm.sh`:

```bash
python -m openrlhf.cli.serve_rm \
  --reward.model_name_or_path OpenRLHF/Llama-3-8b-rm-700k \
  --port 5000 \
  --host 0.0.0.0 \
  --ds.param_dtype bf16 \
  --ds.attn_implementation flash_attention_2 \
  --reward.normalize_enable \
  --data.max_len 8192 \
  --batch_size 16
```

Useful options from `openrlhf/cli/serve_rm.py`:

| Option | Default | Notes |
| --- | --- | --- |
| `--reward.model_name_or_path` | `None` | HuggingFace model id or local model path; required for practical use. |
| `--reward.normalize_enable` | off | Enables reward normalization during model construction. |
| `--ds.value_head_prefix` | `score` | Must match the reward model head prefix. README recommends `score` for reward models intended for `AutoModelForSequenceClassification`. |
| `--data.max_len` | `2048` | Tokenization max length for scored query strings. |
| `--port` / `--host` | `5000` / `0.0.0.0` | Service bind address. |
| `--ds.load_in_4bit` | off | Quantized load path if dependencies/hardware support it. |
| `--ds.param_dtype` | `bf16` | Choices are `bf16` and `fp16`. |
| `--ds.attn_implementation` | `flash_attention_2` | Use `eager` when flash attention is unavailable or troubleshooting. |
| `--ds.experts_implementation` | `None` | MoE expert computation strategy; choices include `eager`, `batched_mm`, `grouped_mm`, and `deepgemm`. |
| `--data.disable_fast_tokenizer` | off | Forces slow tokenizer. |
| `--ds.packing_samples` | off | Passed to model construction. |
| `--batch_size` | `None` | If unset, scores all received queries as one batch. |
| `--use_ms` | off | Patches HuggingFace hub access through ModelScope. |

Minimal local request check after server startup:

```bash
curl -s http://127.0.0.1:5000/get_reward \
  -H 'Content-Type: application/json' \
  -d '{"query":["User: hello\nAssistant: hi"],"prompts":["User: hello"]}'
```

If a training run uses a remote reward server, OpenRLHF examples refer to `--reward.remote_url http://host:5000/get_reward` on the training command.

## LoRA Adapter Merging

OpenRLHF provides `openrlhf.cli.lora_combiner` for merging LoRA/QLoRA adapter weights into a base HuggingFace model. It uses:

- `AutoModelForCausalLM` by default.
- `AutoModelForSequenceClassification` when `--is_rm` is passed.
- `PeftModel.from_pretrained()` followed by `merge_and_unload()`.
- Base tokenizer saved with the merged model.

Repository README example:

```bash
python -m openrlhf.cli.lora_combiner \
  --model_path meta-llama/Meta-Llama-3-8B \
  --lora_path ./checkpoint/llama3-8b-rm \
  --output_path ./checkpoint/llama-3-8b-rm-combined \
  --is_rm \
  --ds.param_dtype bf16
```

Use `--is_rm` for reward models so the base class is `AutoModelForSequenceClassification`. Omit `--is_rm` for normal causal language model adapters.

Before merging:

1. Confirm `--model_path` is the same base model used to train the adapter.
2. Confirm `--lora_path` contains PEFT adapter files, not a DeepSpeed checkpoint directory that still needs export/consolidation.
3. Confirm enough CPU/GPU memory and output disk space are available for the full merged model.
4. Use `--ds.param_dtype fp16` only when the target environment expects fp16; otherwise keep `bf16` if that matches training/deployment.
5. For reward models, confirm the value head prefix expected by downstream loading, commonly `score` in OpenRLHF docs.

## DeepSpeed ZeRO to Universal Checkpoint Conversion

The repository script `examples/scripts/ckpt_ds_zero_to_universal.sh` wraps DeepSpeed's converter:

```bash
python -m deepspeed.checkpoint.ds_to_universal --inject_missing_state \
  --input_folder "$CHECKPOINT_DIR/$LATEST_TAG" \
  --output_folder "$CHECKPOINT_DIR/${LATEST_TAG}_uni" \
  ...extra args...
```

The script expects a DeepSpeed checkpoint root containing a `latest` file. For PPO, it automatically checks `_actor` and `_critic` subdirectories and converts each if present; otherwise it converts the provided root. It writes `latest_universal` next to `latest` with the converted tag name.

Distilled direct conversion pattern for one resolved checkpoint tag:

```bash
python -m deepspeed.checkpoint.ds_to_universal --inject_missing_state \
  --input_folder /path/to/checkpoint/root/global_step123 \
  --output_folder /path/to/checkpoint/root/global_step123_uni
```

For PPO checkpoint roots, apply the same pattern separately to resolved `_actor/<latest-tag>` and `_critic/<latest-tag>` folders. Conversion may rewrite marker files when wrapped by helper scripts and can create large output directories, so require a real DeepSpeed checkpoint tree and user approval.

Safety checklist:

1. Back up or snapshot the checkpoint directory before conversion.
2. Verify `latest` points to the intended source tag.
3. For PPO, inspect whether `_actor/latest` and `_critic/latest` exist.
4. Ensure `deepspeed` is installed and importable in the active environment.
5. Ensure output storage can hold converted universal checkpoints.

## Docker and NVIDIA Helper Scripts

The repository helper scripts are operational examples, not safe generic commands:

- `examples/scripts/docker_run.sh` starts an NVIDIA container, mounts the checkout to `/openrlhf`, mounts `$HOME/.cache`, and uses `--shm-size="10g"` plus `--cap-add=SYS_ADMIN`.
- `examples/scripts/nvidia_docker_install.sh` mutates the host by removing Docker packages, installing Docker, adding NVIDIA toolkit repositories, configuring runtime, and editing user groups.

When helping a user, summarize what these scripts do and ask for explicit approval before running or adapting host-mutating steps.

## Lightweight Native Checks

Safe native candidate:

```bash
pytest tests/test_ray_env_vars.py
```

This test file mocks Ray and verifies OpenRLHF preserves user-provided `NCCL_DEBUG`, `TOKENIZERS_PARALLELISM`, and `RAY_ENABLE_ZERO_COPY_TORCH_TENSORS` when constructing Ray runtime env vars.

Conditional native candidate:

```bash
pytest tests/test_loss_aggregation.py
```

This requires `torch` and is useful for checking loss aggregation behavior, but it is not a general runtime readiness test.

# GRPO configuration reference

This file summarizes the command-line and trainer behavior needed to adapt VLM-R1 GRPO launches without reopening source evidence.

## Entrypoint shape

The training entrypoint is `src/open_r1/grpo_jsonl.py` from the open-r1-multimodal package root. It combines three parser groups:

1. Script/data arguments from `GRPOScriptArguments`.
2. Training and GRPO arguments from `GRPOConfig`, which extends Hugging Face `TrainingArguments`.
3. Model and PEFT arguments from `GRPOModelConfig`, which extends TRL `ModelConfig` and adds `freeze_vision_modules`.

The core command form is:

```bash
torchrun --nproc_per_node N --nnodes M --node_rank R --master_addr HOST --master_port PORT \
  src/open_r1/grpo_jsonl.py \
  --model_name_or_path MODEL \
  --data_file_paths DATA1:DATA2 \
  --image_folders IMAGES1:IMAGES2 \
  --output_dir OUTPUT \
  --run_name RUN \
  --task_type TASK \
  --reward_funcs accuracy format \
  --deepspeed local_scripts/zero3.json
```

Use `../scripts/launch_grpo_jsonl.sh` to render this safely.

## Script/data flags

| Flag | Meaning | Practical notes |
| --- | --- | --- |
| `--data_file_paths` | Colon-separated JSONL files. | Count must match `--image_folders`. |
| `--image_folders` | Colon-separated image roots. | Each JSONL `image` value is joined to its matching image root. For multi-image rows, each item in the list is joined to the same root. |
| `--reward_method` | Optional colon-separated accuracy sub-methods. | If absent, every data file uses `default`. If present, count must match `data_file_paths`. Examples include `all_match`, `math`, `weighted_sum`, `od_ap`, `od_ap50`, `odLength`, `mcq`, `yes_no`, and `llm`. Route semantics to data-and-rewards. |
| `--task_type` | Task prompt/reward context. | Common values: `rec`, `gui`, `gui_defect`, `odLength`, or a custom task handled by a VLM module/reward. |
| `--is_reward_customized_from_vlm_module` | Route reward function names through the selected VLM module. | Use `true` for Qwen/InternVL REC IoU rewards; use `false` for generic rewards such as GUI `all_match`. |
| `--reward_funcs` | Reward function names consumed by the trainer. | Source launchers use `accuracy format`. Generic registry also contains `length` and `repetition`. |
| `--max_pixels`, `--min_pixels` | Qwen image processor pixel bounds. | Lower `max_pixels` to reduce memory at the cost of resolution. |
| `--max_anyres_num` | InternVL dynamic image patch limit. | Lower this to reduce InternVL image memory. Source InternVL recipe uses `6`. |
| `--val_split_ratio` | Optional train/validation split. | If greater than zero and `eval_strategy` is active, eval batch divisibility by `num_generations` also applies. |
| `--arrow_cache_dir` | Dataset cache location. | Not central in the JSONL loader; prefer explicit data paths. |

## GRPO and training flags

| Flag | Default or source pattern | Notes |
| --- | --- | --- |
| `--use_vllm` | Source launchers pass `False`. | If `True`, vLLM needs an available generation GPU and vLLM installed. Do not enable casually on all-GPU training jobs. |
| `--per_device_train_batch_size` | REC source pattern `8`; GUI source pattern `2`. | Major CUDA memory lever and part of the `num_generations` divisibility rule. |
| `--gradient_accumulation_steps` | Source pattern `2`. | Increases effective batch without increasing per-step memory as much. |
| `--gradient_checkpointing` | Source pattern `true`. | Trainer disables model cache. InternVL has custom checkpointing behavior. |
| `--num_train_epochs` | Source pattern `2`. | Use `--max_steps` for bounded tests or fixed-step recipes. |
| `--max_steps` | GUI source pattern `1200`. | Overrides epoch-based length when positive. |
| `--logging_steps` | Source pattern `1`. | Can produce heavy logs with debug mode and W&B. |
| `--save_steps` | REC source pattern `100`; GUI source pattern `400`. | Pair with `--save_total_limit` for long runs. |
| `--num_generations` | Default/source pattern `8`. | Must divide global train batch: `nproc_per_node * nnodes * per_device_train_batch_size`. |
| `--max_completion_length` | Source pattern `2048`. | Reducing this is a direct memory/time lever. |
| `--beta` | `0.04`. | KL coefficient. `0.0` removes the reference model but may affect stability. |
| `--num_iterations` | `1`. | Number of GRPO iterations per batch. |
| `--epsilon` | `0.2`. | Lower clipping bound. |
| `--epsilon_high` | `epsilon` if absent; source example `0.28`. | Upper clipping bound; DAPO-style recipe uses `0.28`. |
| `--reward_weights` | `None`. | If provided, count must match reward functions. |
| `--report_to` | Source launchers use `wandb`. | Use `none` plus `WANDB_DISABLED=true` when no W&B logging is desired. |
| `--log_completions` | `false`. | Can log sample prompt/completion pairs when rich/W&B support exists. |

The trainer ignores unsupported `max_prompt_length` by setting it to `None` and warning. Do not rely on prompt truncation in this implementation.

## Model, LoRA, and freeze flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--model_name_or_path` | Model id or checkpoint path. | Model routing is name-based: names containing `qwen`, `internvl`, or `glm` choose the module family. GLM has a known import mismatch in the verified environment. |
| `--attn_implementation` | Source pattern `flash_attention_2`. | Qwen receives this as a model-init argument; InternVL converts it to `use_flash_attn`. |
| `--use_peft` | Enable PEFT/LoRA. | Source LoRA recipe uses `true`. |
| `--lora_r` | LoRA rank. | Source LoRA recipe uses `64`. |
| `--lora_alpha` | LoRA alpha. | Source LoRA recipe uses `128`. |
| `--lora_dropout` | LoRA dropout. | Source LoRA recipe uses `0.05`. |
| `--lora_task_type` | PEFT task type. | Source LoRA recipe uses `CAUSAL_LM`. |
| `--freeze_vision_modules` | Freeze VLM visual tower parameters. | The trainer matches model-specific vision keywords: Qwen uses `visual`; InternVL uses `vision_model`. |

When PEFT is enabled, the trainer finds all linear modules except those under vision-module keywords, then applies LoRA to those language-side modules. With PEFT, the trainer can disable the adapter to obtain reference-model behavior, so a separate reference model may not be needed.

## Model-family behavior

| Family | Routing trigger | Important behavior |
| --- | --- | --- |
| Qwen2-VL / Qwen2.5-VL | `model_name_or_path` contains `qwen`. | Uses Qwen processors, custom multimodal keys `pixel_values` and `image_grid_thw`, pixel bounds from `max_pixels` and `min_pixels`, and REC custom rewards that resize generated bboxes back to image size. |
| InternVL | `model_name_or_path` contains `internvl`. | Uses remote-code AutoModel/AutoProcessor, maps FlashAttention flag to `use_flash_attn`, drops `use_cache`, uses `pixel_values` and `image_flags`, and uses `max_anyres_num` for dynamic preprocessing. |
| GLM | `model_name_or_path` contains `glm`. | Present in routing but blocked by a Transformers symbol mismatch in the verified package set. Treat as not ready unless the user has repaired the compatible Transformers/model stack. |

## DeepSpeed configs

VLM-R1 source configs use Hugging Face/DeepSpeed `auto` values so `TrainingArguments` supplies batch, optimizer, and gradient settings.

| Config type | Key settings | When to use |
| --- | --- | --- |
| ZeRO-2 JSON | `zero_optimization.stage: 2`, no optimizer offload, auto batch fields. | LoRA/freeze or smaller runs where ZeRO-3 overhead is not needed. |
| ZeRO-3 JSON | `zero_optimization.stage: 3`, no optimizer/param offload, auto bucket fields, gather 16-bit weights on model save. | Full fine-tuning, larger reference-model memory, Qwen source full recipe. |
| ZeRO-3 offload JSON | `zero_optimization.stage: 3`, optimizer and parameter offload to CPU. | Last resort for GPU memory pressure; expect slower training and higher CPU memory/bandwidth demand. |
| Accelerate YAML | `distributed_type: DEEPSPEED`, `num_processes: 8`, `mixed_precision: bf16`. | Useful for accelerate-based launches, but root scripts use direct `torchrun` plus DeepSpeed JSON. |

DeepSpeed import may require a valid `CUDA_HOME` with `nvcc`, especially when building or loading fused ops. Keep this as an environment prerequisite rather than embedding machine-specific paths in commands.

## Torchrun and distributed settings

Single-node defaults:

- `--nproc_per_node`: number of local GPU worker processes.
- `--nnodes 1`, `--node_rank 0`.
- `--master_addr 127.0.0.1` with an unused `--master_port`.

Multi-node rules:

- `--nnodes` is the total node count and must be identical on all nodes.
- `--node_rank` must be unique and range from `0` to `nnodes - 1`.
- `--master_addr` must resolve from every node to rank 0.
- All nodes need the same code, compatible Python packages, model/data accessibility, and rendezvous port reachability.
- Use the renderer to avoid rank/address mismatch.

## Debug and logging environment

The training code checks two environment variables:

- `DEBUG_MODE=true` enables extra reward/format/completion logs.
- `LOG_PATH=...` tells reward helpers where to append debug text.

The bundled launcher sets these only when `--debug true` is selected. With W&B disabled, use `--no-wandb` to both export `WANDB_DISABLED=true` and pass `--report_to none`.

## Resume and saving behavior

- The source launchers pass `--resume_from_checkpoint True`, but the entrypoint actually resumes if `output_dir` already contains `checkpoint-*` and otherwise starts fresh.
- The trainer saves the model into `output_dir` at the end and pushes only if `push_to_hub` is enabled.
- Pair frequent `save_steps` with `save_total_limit` if disk capacity is limited.

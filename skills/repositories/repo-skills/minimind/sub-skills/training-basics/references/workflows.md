# MiniMind core training workflows

This reference provides self-contained operating routes for tokenizer validation, pretraining, full SFT, LoRA, checkpoint resume, DDP, logging, mixed precision, gradient accumulation, and tiny safety checks.

## Before any full training run

1. Confirm the task stage: tokenizer experiment, pretrain, full SFT, or LoRA.
2. Validate the input JSONL with the bundled validator:

   ```bash
   python scripts/validate_minimind_jsonl.py --schema pretrain <pretrain.jsonl>
   python scripts/validate_minimind_jsonl.py --schema sft <sft-or-lora.jsonl>
   ```

3. If using a local tokenizer directory, validate tokenizer/chat-template compatibility:

   ```bash
   python scripts/validate_minimind_jsonl.py --schema sft --tokenizer-dir <tokenizer-dir> --max-seq-len 768 <sft-or-lora.jsonl>
   ```

4. Run the bounded model smoke before expensive training or after changing model knobs:

   ```bash
   python scripts/tiny_training_smoke.py --device cpu
   python scripts/tiny_training_smoke.py --device cuda:0
   ```

5. Choose a device. CUDA is preferred for real training. CPU can validate plumbing and may be practical for very small LoRA experiments, but full pretrain/SFT on CPU is not a realistic throughput target.
6. Ensure the required dataset and input weights already exist locally. The bundled helpers do not download data or weights.

## Tokenizer workflow

Default policy: do not retrain the MiniMind tokenizer for normal model training. A new vocabulary changes weight compatibility, data formatting, prompt templates, inference behavior, and token-level metric comparability.

If a controlled tokenizer experiment is explicitly required, preserve the MiniMind settings:

| Setting | Value |
|---|---|
| Model | BPE |
| Pre-tokenizer | ByteLevel with `add_prefix_space=false` |
| Vocabulary size | `6400` unless intentionally experimenting |
| Main special tokens | `<|endoftext|>`, `<|im_start|>`, `<|im_end|>` |
| Tool/thinking tokens | `<tool_call>`, `</tool_call>`, `<tool_response>`, `</tool_response>`, `<think>`, `</think>` |
| Buffer count | keep reserved buffer tokens through `<|buffer9|>` when using the default `36` added-token plan |
| Chat template | Must support system/user/assistant/tool roles, `tools`, `tool_calls`, `reasoning_content`, and `open_thinking` |

Validation route after generating a tokenizer directory:

```bash
python scripts/validate_minimind_jsonl.py --schema sft --tokenizer-dir <new-tokenizer-dir> --max-seq-len <target-len> <tiny-sft-fixture.jsonl>
```

Treat any tokenizer experiment as a new model family unless all downstream weights, data, and inference/export routes are regenerated against it.

## Pretraining route

Use pretraining to train next-token continuation from `{"text": ...}` JSONL. For quick reproduction, use the mini pretrain data; for full main-branch reproduction, use the full pretrain data.

Single-process route:

```bash
cd <training-entrypoint-dir>
python train_pretrain.py \
  --data_path ../dataset/pretrain_t2t_mini.jsonl \
  --save_dir ../out \
  --save_weight pretrain \
  --from_weight none \
  --hidden_size 768 \
  --num_hidden_layers 8 \
  --use_moe 0 \
  --max_seq_len 340 \
  --epochs 2 \
  --batch_size 32 \
  --learning_rate 5e-4 \
  --accumulation_steps 8 \
  --dtype bfloat16 \
  --save_interval 1000
```

Notes:

- The script default `--max_seq_len` is `340`; project README evidence recommends approximately `768` for `pretrain_t2t_mini.jsonl` and approximately `380` for `pretrain_t2t.jsonl`. Choose based on data length distribution, VRAM, and truncation tolerance.
- Default output weight is `../out/pretrain_768.pth` for dense `hidden_size=768`.
- With `--use_moe 1`, output names gain `_moe` and loss logs include auxiliary router loss.
- `--from_weight none` starts from scratch; use a prefix only when intentionally continuing from an existing output weight.

DDP route:

```bash
torchrun --nproc_per_node <num-gpus> train_pretrain.py <same-flags-as-above>
```

Use `torchrun` from the training entrypoint directory. DDP uses `nccl` and assigns each process to `cuda:<LOCAL_RANK>`.

## Full SFT route

Use full SFT to train dialogue, thinking tags, and tool-call formatting from `{"conversations": ...}` JSONL. Full SFT normally starts from a pretraining weight.

Single-process route:

```bash
cd <training-entrypoint-dir>
python train_full_sft.py \
  --data_path ../dataset/sft_t2t_mini.jsonl \
  --save_dir ../out \
  --save_weight full_sft \
  --from_weight pretrain \
  --hidden_size 768 \
  --num_hidden_layers 8 \
  --use_moe 0 \
  --max_seq_len 768 \
  --epochs 2 \
  --batch_size 16 \
  --learning_rate 1e-5 \
  --accumulation_steps 1 \
  --dtype bfloat16 \
  --save_interval 1000
```

Notes:

- Default input weight is `../out/pretrain_768.pth` for dense `hidden_size=768`.
- Default output weight is `../out/full_sft_768.pth`.
- SFT labels supervise assistant spans only; user/system/tool context remains masked.
- `sft_t2t_mini.jsonl` is suited to a quick Zero-style dialogue model; `sft_t2t.jsonl` is suited to fuller reproduction and includes mixed tool-call samples.
- If no pretraining weight exists and the task intentionally trains from scratch, set `--from_weight none`; expect weaker results and make that explicit in the experiment record.

DDP route:

```bash
torchrun --nproc_per_node <num-gpus> train_full_sft.py <same-flags-as-above>
```

## LoRA route

Use LoRA when the goal is lightweight domain adaptation on SFT-format conversations while preserving the base full-SFT model.

Single-process route:

```bash
cd <training-entrypoint-dir>
python train_lora.py \
  --data_path ../dataset/lora_domain.jsonl \
  --save_dir ../out \
  --lora_name lora_domain \
  --from_weight full_sft \
  --hidden_size 768 \
  --num_hidden_layers 8 \
  --use_moe 0 \
  --max_seq_len 340 \
  --epochs 10 \
  --batch_size 32 \
  --learning_rate 1e-4 \
  --accumulation_steps 1 \
  --dtype bfloat16 \
  --use_compile 0 \
  --save_interval 1000
```

Notes:

- Default input weight is `../out/full_sft_768.pth`.
- Default output for `--lora_name lora_domain` is `../out/lora_domain_768.pth`.
- LoRA data uses the same SFT conversation schema. Validate it with `--schema sft`.
- The native LoRA route attaches low-rank branches only to square linear layers and freezes all non-LoRA parameters.
- `torch.compile` is disabled for LoRA because LoRA monkey-patches `forward` methods.
- To use or merge LoRA weights for inference/export, hand off to `inference-serving` after training.

DDP route:

```bash
torchrun --nproc_per_node <num-gpus> train_lora.py <same-flags-as-above>
```

## Checkpoint resume

All core training scripts support resume with `--from_resume 1`:

```bash
python train_pretrain.py --from_resume 1 <same-stage-flags>
python train_full_sft.py --from_resume 1 <same-stage-flags>
python train_lora.py --from_resume 1 <same-stage-flags>
```

Resume checklist:

- Use the same stage prefix: `--save_weight` for pretrain/full SFT, `--lora_name` for LoRA.
- Use the same `--hidden_size` and `--use_moe` values.
- Keep the checkpoint directory available; resume files are keyed as `{prefix}_{hidden_size}{_moe}_resume.pth`.
- Keep the output directory available if the stage also loads `--from_weight`.
- If GPU count changes, MiniMind rescales the saved step by old/new world size. This is supported but can change exact batch ordering.
- Resume preserves logging run id when available, so `--use_wandb` can continue the same SwanLab/WandB-compatible run.

## Logging with SwanLab/WandB interface

The training flags use `--use_wandb`, but the current implementation imports `swanlab as wandb`.

Example:

```bash
python train_full_sft.py --use_wandb --wandb_project MiniMind-Full-SFT <other-flags>
```

Guidance:

- Leave `--use_wandb` off for offline, CI, smoke, or credential-free environments.
- If network access or login fails, rerun without `--use_wandb`; training itself does not require online logging.
- Resume can reuse the stored run id when logging is enabled and the previous checkpoint contains it.

## Mixed precision and optimizer behavior

Common flags:

| Flag | Default by stage | Meaning |
|---|---|---|
| `--dtype` | `bfloat16` | CUDA autocast dtype; CPU uses a null autocast context. `float16` enables GradScaler. |
| `--grad_clip` | `1.0` | Gradient norm clip before optimizer step. |
| `--learning_rate` | pretrain `5e-4`, full SFT `1e-5`, LoRA `1e-4` | Initial LR used by cosine decay helper. |
| `--accumulation_steps` | pretrain `8`, full SFT `1`, LoRA `1` | Number of micro-batches per optimizer step. |
| `--batch_size` | pretrain `32`, full SFT `16`, LoRA `32` | Per-process micro-batch size. |

Effective batch size is approximately:

```text
batch_size * accumulation_steps * world_size
```

The trainers perform one final optimizer step at epoch end if the number of batches is not divisible by `accumulation_steps`.

## `torch.compile`

- Pretraining and full SFT accept `--use_compile 1` and wrap the model with `torch.compile` after optimizer/scaler setup and before DDP wrapping.
- Keep compile off for first-run debugging, tiny smokes, CPU validation, and any run where compilation overhead exceeds expected training time.
- LoRA disables compile because monkey-patched LoRA forwards are incompatible with the native compile route.

## Tiny validation route

Use the bundled tiny smoke for model plumbing, not for quality claims:

```bash
python scripts/tiny_training_smoke.py \
  --device cpu \
  --hidden-size 32 \
  --num-hidden-layers 2 \
  --seq-len 16 \
  --vocab-size 128
```

CUDA variant:

```bash
python scripts/tiny_training_smoke.py --device cuda:0 --dtype bfloat16
```

LoRA variant:

```bash
python scripts/tiny_training_smoke.py --device cpu --lora
```

Expected coverage:

- imports MiniMind source modules from the active package/source environment;
- builds a tiny config without loading real weights;
- runs forward loss, backward, one optimizer step, and optional short generation;
- optionally applies LoRA and verifies that trainable parameters are LoRA-only.

The tiny smoke does not read training datasets, save checkpoints, download tokenizers, or prove convergence.

## Verification cases to plan later

After the whole repo skill is integrated, plan at least these native-backed or synthetic usability checks for this sub-skill:

1. A tiny SFT JSONL fixture containing `system.tools`, assistant `tool_calls`, a `tool` response, and assistant `reasoning_content`; validate it with the bundled validator and a local tokenizer directory.
2. A tiny dense and LoRA smoke on the same MiniMind config, verifying that dense training has all parameters trainable while LoRA training only exposes `.lora.` parameters.

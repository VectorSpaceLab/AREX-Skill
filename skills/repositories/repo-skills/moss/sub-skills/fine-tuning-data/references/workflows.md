# MOSS fine-tuning workflow

## Purpose

Read this when planning MOSS SFT data preparation or training commands. Full
training is expensive and backend-dependent; safe validation should happen
before tokenizer/model work.

## Data preparation flow

1. Prepare a data directory containing `train.jsonl` and `val.jsonl` in the
   conversation schema described in [data-formats.md](data-formats.md).
2. Run the bundled schema validator on a sample or full file:

   ```bash
   python sub-skills/fine-tuning-data/scripts/validate_sft_json.py train.jsonl --sample-limit 100
   ```

3. Only after structural validation, run tokenizer-based preprocessing through
   `SFTDataset`. The loader will create `train_data`, `train_no_loss_spans`,
   `val_data`, and `val_no_loss_spans` cache files in the data directory.
4. Keep records within the 2048-token context limit. The loader truncates by
   dropping later turns when adding a turn would exceed 2048 tokens.

## Training command shape

The source training script exposes these important arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name_or_path` | `./ckpts/moss-16B-base` | Base checkpoint used with `AutoTokenizer` and `AutoModelForCausalLM`. |
| `--data_dir` | `./data/sft` | Directory with train/val JSONL or cached tensors. |
| `--output_dir` | `./ckpts/moss-16B-sft` | Checkpoint output. |
| `--log_dir` | `./train_logs/moss-16B-sft` | TensorBoard logs. |
| `--max_seq_len` | 2048 | Intended context length. |
| `--train_bsz_per_gpu` | 4 | Per-GPU training batch size. |
| `--eval_bsz_per_gpu` | 4 | Per-GPU evaluation batch size. |
| `--weight_decay` | 0.1 | AdamW weight decay for non-bias/non-LN weights. |
| `--learning_rate` | `9e-6` | Learning rate. |
| `--warmup_rates` | 0.05 | Warmup fraction; source argparse marks it as int, so verify before reuse. |
| `--n_epochs` | 2 | Epoch count. |
| `--save_step` | 3000 | Checkpoint interval. |
| `--eval_step` | 5 | Eval interval. |
| `--seed` | 42 | Random seed. |

Use the bundled planner to create an Accelerate/DeepSpeed config and a reviewed
training-launch command without running training:

```bash
python sub-skills/fine-tuning-data/scripts/plan_finetune_command.py \
  --model-name-or-path OpenMOSS-Team/moss-moon-003-base \
  --data-dir /path/to/sft-data \
  --output-dir /path/to/output \
  --log-dir /path/to/logs \
  --write-config /path/to/moss_sft_accelerate.yaml
```

The planner only writes config/command text and checks whether expected data
files exist. Do not run the printed launch as a smoke test; full MOSS SFT loads
a large model, prepares distributed training, and writes checkpoints/logs.

## Accelerate/DeepSpeed config

The bundled planner can emit an Accelerate config equivalent to the source evidence. It uses:

- local machine compute environment;
- `distributed_type: DEEPSPEED`;
- mixed precision `fp16`;
- `num_processes: 8`;
- DeepSpeed ZeRO stage 3;
- gradient accumulation steps 1;
- gradient clipping 1.0;
- no optimizer/parameter offload;
- `zero3_init_flag: true` and `zero3_save_16bit_model: true`.

Adjust `num_processes`, GPU ids, batch sizes, and ports for the target host.

## Training-loop behavior

- `Accelerator(mixed_precision='fp16')` wraps model, optimizer, dataloaders, and
  scheduler.
- The script enables `model.transformer.gradient_checkpointing = True`.
- `SFTMetric` computes token accuracy/loss and all-reduces across distributed
  workers.
- The tokenizer maps EOS to `<eom>` id 106068 for SFT.
- Loss labels use `-100` for the meta instruction and masked tool-response
  spans.

## Safe versus unsafe checks

Safe:

- JSON/JSONL schema validation.
- YAML/config key inspection.
- `python sub-skills/fine-tuning-data/scripts/plan_finetune_command.py --help`.

Unsafe by default:

- Full training.
- Loading 16B checkpoints just to test data format.
- Writing checkpoints/logs into a shared path.
- Running with all GPUs on a multi-tenant machine without coordination.

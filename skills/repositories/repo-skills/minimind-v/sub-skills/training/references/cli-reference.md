# Training CLI Reference

## Common flags

Both training stages expose these common flags: `--save_dir`, `--save_weight`, `--epochs`, `--batch_size`, `--learning_rate`, `--device`, `--dtype`, `--num_workers`, `--accumulation_steps`, `--grad_clip`, `--log_interval`, `--save_interval`, `--hidden_size`, `--num_hidden_layers`, `--max_seq_len`, `--use_moe`, `--data_path`, `--from_weight`, `--from_resume`, `--freeze_llm`, `--use_compile`, `--use_wandb`, and `--wandb_project`.

## Pretrain defaults

- `--save_dir ../out`
- `--save_weight pretrain_vlm`
- `--epochs 2`
- `--batch_size 16`
- `--learning_rate 4e-4`
- `--max_seq_len 450`
- `--data_path ../dataset/pretrain_i2t.parquet`
- `--from_weight llm`
- `--freeze_llm 2`

## SFT defaults

- `--save_dir ../out`
- `--save_weight sft_vlm`
- `--epochs 2`
- `--batch_size 4`
- `--learning_rate 5e-6`
- `--max_seq_len 768`
- `--data_path ../dataset/sft_i2t.parquet`
- `--from_weight pretrain_vlm`
- `--freeze_llm 1`

## Safe command builder

Use `build_training_command.py` to construct command strings and optionally check files. It never launches training.

```bash
python path/to/build_training_command.py sft --from-weight llm --dry-check-files
python path/to/build_training_command.py pretrain --ddp-gpus 4 --use-moe 1
```

If the user approves a run, execute the printed command from a MiniMind-V checkout.

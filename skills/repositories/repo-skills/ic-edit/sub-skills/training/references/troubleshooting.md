# Troubleshooting

## Common failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `AssertionError: Please set the XFL_CONFIG environment variable` | The launcher did not export `XFL_CONFIG` | Use the bundled helper or export the config path before launch |
| `KeyError: 'train'` / `KeyError: 'dataset'` / missing config keys | Malformed YAML | Add the missing section before any real run; the helper can catch this in dry-run mode |
| No parquet files found | `train.dataset.path` does not match any files from the training working root | Fix the glob or provision the shards first |
| Hub or download errors on `osunlp/MagicBrush` | Offline machine, missing cache, or dataset access problem | Pre-cache the dataset or use a machine with network access |
| `WANDB_API_KEY` missing | Wandb logging is intentionally disabled | Safe to ignore unless you want logs; then export the key |
| Wandb import failure | Package missing or broken environment | Install the training requirements and retry |
| `torch.cuda.set_device` or `invalid device ordinal` | CUDA unavailable or `CUDA_VISIBLE_DEVICES` does not match the visible GPU count | Fix the GPU mapping before launching |
| `ModuleNotFoundError: train` | `PYTHONPATH` or CWD is wrong | Use the bundled helper; it runs from `<checkout>/train` with `<checkout>/train/src` on `PYTHONPATH` |
| MoE imports do not use the vendored fork | The repo-root `icedit/` directory is missing or not on `sys.path` | Verify the ICEdit checkout; the standalone helper does not include this vendored package |
| `accelerate` spawns the wrong shape of job | `accelerate` config and visible GPUs are inconsistent | Reconfigure `accelerate` or adjust `CUDA_VISIBLE_DEVICES` |
| `NotImplementedError` from LoRA resume | `lora_path` resume is not implemented | Treat saved LoRA folders as exports only unless you extend the code |

## What to check first

1. `XFL_CONFIG` points at the intended YAML.
2. The YAML has a `train.dataset` section.
3. The parquet glob resolves from the training working root.
4. `CUDA_VISIBLE_DEVICES` matches the machine.
5. `WANDB_API_KEY` is present only if you want wandb logging.

## When to stop and revise

- If the config is malformed, fix the YAML rather than starting a job.
- If the dataset needs to be downloaded, stop and provision it deliberately.
- If CUDA or accelerate disagrees with the visible devices, do not keep retrying the same launch command.

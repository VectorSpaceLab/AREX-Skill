# Troubleshooting

Use this page when a config parses but the run behaves unexpectedly.

## Fast triage table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `JSONDecodeError` or strange comment-related parse failure | You used a strict JSON parser on a comment-bearing config. | Parse through `core.logger.parse` or this sub-skill's `inspect_config.py`; both strip `//` comments first. |
| The run ignores your stored `phase` | The CLI `-p/--phase` flag overrides the JSON field. | Check the launch command, not just the file. |
| The run seems to ignore `gpu_ids` | The CLI `-gpu/--gpu_ids` override won, or the effective GPU string is not what you expected. | Inspect the logger's `export CUDA_VISIBLE_DEVICES=...` line. |
| `DataParallel` appears when you expected a single-GPU run | The effective GPU string contains more than one id. | Pass a single id explicitly and recheck the CLI override. |
| A single GPU id with multiple digits behaves oddly | `core.logger.parse` decides distribution from the raw GPU string length. | Verify the actual rendered GPU string and keep ids explicit. |
| `RuntimeError` around the first convolution or channel mismatch | `conditional` and `unet.in_channel` disagree. | Use `in_channel=6` for conditional SR and `in_channel=3` for unconditional generation. |
| `GroupNorm` complains that channels are not divisible by groups | `norm_groups` does not divide one of the UNet stage widths. | Choose a divisor of every stage width, or fall back to the default `32` when it is valid. |
| Resume loading appends the suffix twice | `path.resume_state` already included `_gen.pth` or `_opt.pth`. | Set the value to the checkpoint stem only. |
| W&B import or login fails | `wandb` is not installed or `-enable_wandb` was omitted. | Install `wandb` and pass `-enable_wandb`; add `-log_wandb_ckpt`, `-log_eval`, or `-log_infer` only when the matching script supports them. |
| Validation looks like HR-only data when you expected LR inputs | The dataset `mode` is `HR`, so `need_LR` is false. | Use `mode=LRHR` for conditional validation. |
| The sampled family does not match the checkpoint family | `which_model_G` or `conditional` changed without switching checkpoints. | Load a checkpoint produced by the same family and conditioning mode. |

## Known config quirks

- The current configs all keep `diffusion.channels=3` and `unet.out_channel=3`.
- `sr3` conditional configs use `in_channel=6`.
- `ddpm` conditional configs also use `in_channel=6`, but the internal embedding path differs.
- The 64→512 config uses `img` directories, `gpu_ids=[0,1]`, `norm_groups=16`, no attention blocks, and a smaller learning rate.
- `--debug` mutates several runtime values after parsing: train/val data length, print frequency, validation frequency, checkpoint frequency, and the diffusion timesteps.

## If the config still looks wrong

Run `scripts/inspect_config.py` on the file and compare the summary against the intended task family. If the summary is correct but the runtime still fails, the problem is usually checkpoint compatibility or a mismatch between the config family and the launch script.

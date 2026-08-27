# Super-Resolution Training Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Config fails to parse | The config is JSON with `//` comments. Remove unsupported JSON syntax such as dangling commas, or use the bundled command builder, which strips comments before parsing. |
| The command uses the wrong GPU | `--gpu-ids` overrides the config's `gpu_ids` field. `sr.py` exports the selected ids through `CUDA_VISIBLE_DEVICES` and then uses them for model placement. |
| You expected a CPU run but got a CUDA error | The bundled SR configs assume GPU ids. To force CPU-only execution you must edit the config to remove `gpu_ids` and accept a much slower run. |
| Resume training cannot find the checkpoint | `path.resume_state` must point to the checkpoint prefix, not to the `_gen.pth` or `_opt.pth` file itself. `load_network` appends those suffixes automatically. |
| Validation-only runs look untrained or random | `phase=val` still needs a real checkpoint prefix in `path.resume_state`. Without one, the model has no useful generator weights. |
| A short training run never validates | `val_freq` is step-based and defaults to 10k iterations in the bundled configs. Lower `train.val_freq` or use debug mode for a quick smoke run. |
| A short training run never saves a checkpoint | `save_checkpoint_freq` is also step-based and defaults to 10k iterations. Lower the frequency or run longer. |
| Validation output is missing LR images | The validation dataset must use `mode: LRHR` and include the LR layout or LMDB keys. If you only have HR/SR pairs, switch the validation mode accordingly. |
| `datatype: img` loading fails | The image layout must contain exact directories such as `sr_<L>_<R>`, `hr_<R>`, and, when needed, `lr_<L>`, each with readable image files. |
| `datatype: lmdb` loading fails | The LMDB must contain `length`, `hr_<R>_<index>`, `sr_<L>_<R>_<index>`, and, when needed, `lr_<L>_<index>` keys with zero-padded indices. |
| GroupNorm shape errors appear | `norm_groups` must divide every channel width visited by the U-Net. Lower `norm_groups` or adjust the channel widths together. |
| The model or validation path looks mismatched to the image size | Keep `model.diffusion.image_size`, dataset `r_resolution`, and the checkpointed config aligned. The 64→512 config also uses a smaller learning rate and a different `norm_groups` setting. |
| W&B import or login fails | Install the `wandb` package and log in before using `-enable_wandb`. `-log_wandb_ckpt` and `-log_eval` only do anything when W&B is enabled. |
| No W&B checkpoint or validation table is written | Make sure `-enable_wandb` is set, then add `-log_wandb_ckpt` for training artifacts or `-log_eval` for validation tables. |
| The run is too slow or runs out of memory | Use `-d`, lower batch size, reduce resolution, or switch to the smaller 16→128 config. The 64→512 setup is much heavier. |
| Validation results are incomplete during training | `sr.py` only validates every `val_freq` optimizer steps and, in train phase, clamps validation `data_len` to 3. Use the validation phase for a full pass. |

## Safe recovery checklist

1. Confirm the command targets the intended phase: `train` for new or resumed training, `val` for evaluation-only.
2. Confirm the GPU ids in the command match the intended device list.
3. Confirm `path.resume_state` is the checkpoint prefix, not a suffixed file name.
4. Confirm the train and validation layouts match the config's `datatype`, `mode`, `l_resolution`, and `r_resolution` fields.
5. Confirm W&B prerequisites only when the command enables W&B.

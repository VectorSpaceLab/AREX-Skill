# Translation workflow troubleshooting

Start with the observable symptom. Verify the dataset layout first, then the command, then the checkpoint architecture, then the device/runtime.

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `RuntimeError: Error(s) in loading state_dict` | Test command does not match the saved generator architecture or checkpoint key names. Common mismatches: `--netG`, `--norm`, dropout, `--model`, `--model_suffix`, channel counts, or epoch/load-iter suffix. | Reconstruct the training command options from the saved `*_opt.txt` and set them explicitly in the test command. For pix2pix Facades-style checkpoints, include `--netG unet_256 --norm batch --direction BtoA` when appropriate. For one-sided CycleGAN, use `--model test` and the correct `--model_suffix` only when the checkpoint filename includes that suffix. |
| `No such file or directory` for `latest_net_G*.pth` | `--name`, `--checkpoints_dir`, `--epoch`, `--load_iter`, or `--model_suffix` points to the wrong checkpoint path. | Check expected path: `checkpoints/<name>/<epoch>_net_<model_name>.pth`. For pretrained helpers the directory is usually `checkpoints/<asset>_pretrained/latest_net_G.pth`. |
| `ModuleNotFoundError: No module named 'wandb'` during training import | Current `util.visualizer` imports W&B at module import time even if `--use_wandb` is not supplied. | Install `wandb` in the runtime environment, or patch the checkout deliberately if the task is repo maintenance. Omit `--use_wandb` when credentials/network are unavailable. |
| `torch.cuda.is_available()` false or CUDA initialization errors | CPU-only PyTorch build, driver/container GPU passthrough issue, incompatible CUDA wheel, or no visible GPU. | The current parser has no `--gpu_ids` flag. Use a CPU-only PyTorch build or prefix a Linux command with `CUDA_VISIBLE_DEVICES=` for CPU, or install a compatible CUDA build and verify a tiny CUDA tensor allocation before training. Do not treat a CPU import as proof of CUDA readiness. |
| DDP command fails around normalization or process setup | Current source/docs have naming and guard inconsistencies around synchronized normalization. The parser accepts `syncbatch`; prose may use `sync_batch`; `BaseModel.setup` contains a contradictory guard. | Reproduce a tiny DDP parser/setup smoke before a long run. Keep a single-process command ready. If maintaining the repo, inspect and fix the DDP normalization guard before relying on `torchrun`. |
| `ValueError: empty range for randrange()` or crop errors | Some images are smaller than `--crop_size` when using `crop`, or `--load_size < --crop_size`. | Use `resize_and_crop` or `scale_width_and_crop`, ensure `--load_size >= --crop_size`, or resize data before training. |
| Output/input image size mismatch with `--preprocess none` | Generator down/up-sampling expects dimensions divisible by a small factor, usually 4 for ResNet paths. | Use dimensions divisible by 4 or let the loader adjust with the documented preprocessing path. For U-Net 128/256, use compatible sizes for the selected U-Net depth. |
| Out of memory | CycleGAN holds two generators and two discriminators during training; high-resolution crops or large batch sizes are expensive. | Reduce `--batch_size`, `--crop_size`, or `--load_size`; use cropped training and one-sided test (`--model test`) for high-resolution inference; try CPU only for command/debug but not for full training throughput. |
| Loss curves oscillate or do not monotonically decrease | GAN objectives are minimax games; losses alone are weak convergence signals. | Inspect generated samples in HTML/W&B, use task-specific metrics or human review, and treat exploding losses/NaNs differently from ordinary oscillation. |
| Colorization output has channel or Lab/RGB errors | Colorization model/dataset defaults were overridden inconsistently. | Keep `--model colorization --dataset_mode colorization --input_nc 1 --output_nc 2 --direction AtoB`; use natural RGB image folders, not A/B combined images. |
| Pix2pix output direction is reversed | A/B halves or `--direction` do not match the intended task. | Confirm side-by-side image orientation. The loader splits left half as A and right half as B; `BtoA` maps right-to-left. |
| `--model test` loads the wrong data | `--model test` selects `single`; `--dataroot` must point directly to a folder of input images, not a paired/unpaired dataset parent. | Validate with `data-preparation/scripts/validate_layout.py --mode single --dataroot INPUT_IMAGES`. |

## Fast triage commands

```bash
python sub-skills/translation-workflows/scripts/build_command.py --help
python sub-skills/data-preparation/scripts/validate_layout.py --mode aligned --dataroot DATASET_ROOT --check-open --check-aligned-width
python test.py --help
python train.py --help
```

Use `--num_test 1`, a tiny local fixture, and either a CPU-only PyTorch environment or `CUDA_VISIBLE_DEVICES=` for bounded CPU debugging. Do not start network downloads or long training runs as a first diagnostic step.

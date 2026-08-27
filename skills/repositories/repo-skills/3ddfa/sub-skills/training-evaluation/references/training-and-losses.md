# Training and losses

## Train entrypoint

The bundled recipes in `training/train_wpdc.sh`, `training/train_vdc.sh`, and `training/train_pdc.sh` are shell templates that call `./train.py` from inside the `training/` directory.

`train.py` is a CUDA-first trainer. The important facts are:

- It creates the model from `mobilenet_v1` and wraps it with `nn.DataParallel(...).cuda()`.
- It calls `torch.cuda.set_device(args.devices_id[0])` before wrapping the model.
- It moves training targets to CUDA inside the loop.
- The training loop saves checkpoints after every epoch, then runs validation.

## Key CLI fields

| flag | purpose |
|---|---|
| `--arch` | MobileNet variant to build (`mobilenet_2`, `mobilenet_1`, `mobilenet_075`, `mobilenet_05`, `mobilenet_025`). |
| `--loss` | Selects the loss family: `wpdc`, `vdc`, or `pdc`. |
| `--opt-style` | Loss mode: `resample` or `all`. WPDC uses `resample` in the shipped recipe. |
| `--root` | Image root directory joined with each filelist entry. |
| `--filelists-train` / `--filelists-val` | Ordered image lists for training and validation. |
| `--param-fp-train` / `--param-fp-val` | Ordered parameter arrays or pickles matching the filelists. |
| `--snapshot` | Checkpoint prefix. The parent directory is created automatically. |
| `--resume` | Warm-start checkpoint path. Only model weights are loaded. |
| `--devices-id` | Comma-separated CUDA device ids. The first id becomes the primary device. |
| `--batch-size`, `--epochs`, `--milestones`, `--base-lr`, `--workers` | Standard training schedule and loader controls. |
| `--resample-num` | Present in the CLI and recipes, but not forwarded into the current loss constructors. |

## Loss semantics

- **PDC**: plain parameter-distance training via `nn.MSELoss` on the whitened 62-d parameter vector.
- **VDC**: `VDCLoss`, which reconstructs geometry from the whitened parameters and compares vertices.
- **WPDC**: `WPDCLoss`, a weighted parameter-distance loss that uses the model basis and keypoints.

### Loss-specific caveats

- `WPDCLoss` in the bundled code only implements the `resample` path.
- `VDCLoss` supports both `all` and `resample`.
- The current `train.py` does not pass `--resample-num` into either loss constructor, so changing that flag alone does not change the sampling count.

## Bundled recipes

- `training/train_wpdc.sh`
  - Uses `--loss=wpdc`.
  - Uses `--opt-style=resample`.
  - Sets a large batch size and a multi-GPU device list.
  - Good baseline when you want the standard first-stage WPDC setup.

- `training/train_vdc.sh`
  - Uses `--loss=vdc`.
  - Uses `--opt-style=resample`.
  - Sets a very small base LR and a larger GPU list.
  - Matches the later-stage vertex-distance recipe.

- `training/train_pdc.sh`
  - The shipped template currently passes `--loss=vdc`.
  - If you want a plain PDC/MSE baseline, switch that flag to `--loss=pdc` and keep the rest of the template aligned with your data layout.

## Checkpoint and resume behavior

- Checkpoints are written as `snapshot_prefix_checkpoint_epoch_<epoch>.pth.tar`.
- Only `state_dict` and the epoch number are saved.
- `--resume` reloads model weights only; optimizer momentum and scheduler state are not restored.
- Because the optimizer state is not saved, a resumed run is a weights warm-start, not a true full-state continuation.
- Set `--start-epoch` explicitly if you want the printed epoch numbers to continue from a prior run.

## One-GPU or custom-root adaptation

- To adapt a multi-GPU recipe to one GPU, reduce `--devices-id` to a single visible CUDA id and lower `--batch-size` to fit memory.
- Keep `--root` aligned with the image tree referenced by the filelists.
- Keep the filelist order identical to the parameter file order.
- If you need CPU-only execution, this code path is not ready without patching out the `.cuda()` and `DataParallel` calls.

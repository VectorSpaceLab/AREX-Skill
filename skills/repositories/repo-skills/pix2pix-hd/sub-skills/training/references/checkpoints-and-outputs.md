# Checkpoints and outputs

All training artifacts live under `checkpoints/<name>/` unless you override `--checkpoints_dir`.

## Directory map

| Path | What it stores | Created by |
|---|---|---|
| `checkpoints/<name>/opt.txt` | Saved option snapshot for the run | `BaseOptions.parse()` when `save=True` and `--continue_train` is off.
| `checkpoints/<name>/iter.txt` | Resume cursor: epoch and in-epoch iteration | `train.py` when saving latest checkpoints and at epoch boundaries.
| `checkpoints/<name>/loss_log.txt` | Console-style loss log | `util/visualizer.py`.
| `checkpoints/<name>/web/index.html` | Training preview page | `Visualizer.display_current_results()` unless `--no_html` is set.
| `checkpoints/<name>/web/images/` | Saved preview images | `Visualizer.display_current_results()`.
| `checkpoints/<name>/logs/` | TensorBoard summaries | `Visualizer.__init__()` when `--tf_log` is enabled and TensorFlow is installed.
| `checkpoints/<name>/*_net_G.pth` | Generator weights | `BaseModel.save_network()` via `Pix2PixHDModel.save()`.
| `checkpoints/<name>/*_net_D.pth` | Discriminator weights | `BaseModel.save_network()` via `Pix2PixHDModel.save()`.
| `checkpoints/<name>/*_net_E.pth` | Encoder weights for feature runs | `BaseModel.save_network()` via `Pix2PixHDModel.save()` when `--instance_feat` or `--label_feat` creates `netE`.

## File naming rules

- `save('latest')` writes `latest_net_G.pth`, `latest_net_D.pth`, and, when applicable, `latest_net_E.pth`.
- `save(epoch_number)` writes `<epoch_number>_net_*.pth`.
- The epoch save path uses the experiment name as the directory and the epoch label as the filename prefix.
- `save_network()` saves the state dict on CPU first and moves the network back to GPU if one is available.

## Save and resume behavior

- Iteration-level saves happen when `total_steps % save_latest_freq` matches the initial offset computed at startup.
- Epoch-level saves happen when `epoch % save_epoch_freq == 0`.
- At epoch end, the script saves both `latest` and the numeric epoch label, then rewrites `iter.txt` to the next epoch and iteration `0`.
- `--continue_train` reads `iter.txt`; if it is missing or malformed, training falls back to epoch 1 / iter 0.
- `--load_pretrain <dir>` is for bootstrapping a new run from another checkpoint directory.
- `--which_epoch` selects the label inside that directory; the default is `latest`.
- `load_network()` tries a normal state-dict load first, then a partial load if the key set or tensor shapes do not match exactly.

## What to expect from a smoke run

- `--debug` does **not** guarantee a checkpoint because it only shortens the loop and increases print/display cadence.
- If you need to prove save/load behavior in a tiny run, explicitly lower the save cadence, for example `--save_latest_freq 1 --save_epoch_freq 1`.
- `--no_html` only suppresses the web preview tree; it does not affect checkpoint `.pth` files.
- `results/` is an inference/test directory, not a training output directory.

## Practical checkpoint checks

1. Confirm `checkpoints/<name>/` exists.
2. Confirm `opt.txt` matches the intended recipe.
3. Confirm the expected `latest_net_*.pth` or epoch-labeled files are present.
4. Confirm `iter.txt` matches the resume point if you intend to continue training.
5. For feature runs, confirm the encoder file exists when `--load_features` or feature conditioning is enabled.

# Feature Workflows

This page distills the feature-conditioned paths from `encode_features.py`, `precompute_feature_maps.py`, `models/pix2pixHD_model.py`, `models/ui_model.py`, and the `scripts/*feat*.sh` recipes.

## Workflow table

| Workflow | Source recipe | Required inputs | Main outputs | Use when | Notes |
| --- | --- | --- | --- | --- | --- |
| 512p feature encoder training | `scripts/train_512p_feat.sh` | `train_label/`, `train_inst/`, `train_img/`; a CUDA-capable run | `checkpoints/<name>/latest_net_G.pth`, `latest_net_D.pth`, `latest_net_E.pth` | You want the source feature checkpoint that later stages will encode from | The source script only adds `--instance_feat`; `--label_feat` is supported by the model but is not part of the stock recipe. |
| Feature-map precompute | `precompute_feature_maps.py` | A source checkpoint with `netE`; `train_label/` and `train_img/` | `datasets/<dataroot>/train_feat/*.png` | You need dense feature maps for the 1024p `--load_features` recipes | The helper always uses `instance_feat=True` internally and writes by replacing `/train_label/` with `/train_feat/` in the source path. |
| 1024p feature training, 12G | `scripts/train_1024p_feat_12G.sh` | Source checkpoint `checkpoints/<source>/`, `train_feat/`, CUDA | `checkpoints/<target>/latest_net_G.pth`, `latest_net_D.pth` | You need the lower-memory 1024p feature-conditioned training path | This recipe crops to `fineSize 896`, uses `--load_features`, and does not build `netE` for the target run. |
| 1024p feature training, 24G | `scripts/train_1024p_feat_24G.sh` | Source checkpoint `checkpoints/<source>/`, `train_feat/`, CUDA | `checkpoints/<target>/latest_net_G.pth`, `latest_net_D.pth` | You have enough VRAM for the full-resolution feature-conditioned path | This recipe keeps `resize_or_crop none` and changes the schedule to `niter 50`, `niter_decay 50`, `niter_fix_global 10`. |
| Feature cache encoding and clustering | `encode_features.py` | Source checkpoint with `netE`; `scikit-learn` / `KMeans`; training data | `features.npy` and `features_clustered_%03d.npy` in `checkpoints/<name>/` | You need the clustered feature bank for test-time sampling or interactive editing | `n_clusters` is capped per label by available rows, and rows with small object area are filtered before KMeans. |
| Feature-conditioned test | `scripts/test_512p_feat.sh`, `scripts/test_1024p_feat.sh` | Cluster cache under `checkpoints/<name>/`; `latest_net_G.pth`; CUDA | HTML results under `results/<name>/<phase>_<epoch>/` | You want sampled feature inference without reopening the source repository | `test.py --instance_feat` samples from the clustered bank; `latest_net_E.pth` is optional for this branch. `test_1024p_feat.sh` has a typo in the source repo (`---netG`); the bundled builder corrects it to `--netG`. |
| Encoded-image test path | `test.py --use_encoded_image` | Feature checkpoint with `netE`; real image inputs | HTML results | You want to encode the current image instead of sampling cluster centers | This path is feature-conditioned but different from the cluster-sampling branch. |

## Model codepaths that matter

| Codepath | What it does | Practical effect |
| --- | --- | --- |
| `Pix2PixHDModel.use_features = instance_feat or label_feat` | Enables the feature branch | Both switches activate feature conditioning; `instance_feat` takes precedence when both are set. |
| `Pix2PixHDModel.gen_features = use_features and not load_features` | Decides whether `netE` exists | `--load_features` switches the model to cached feature-map inputs and disables encoder creation for that run. |
| `Pix2PixHDModel.sample_features(inst)` | Loads `checkpoints/<name>/<cluster_path>` and samples a cluster per object | This is the default feature-inference branch for `test.py --instance_feat`. |
| `Pix2PixHDModel.encode_features(image, inst)` | Extracts per-object feature rows | It returns a label-keyed dict with `feat_num + 1` columns, where the last column is a normalized size score. |
| `UIModel.load_image(...)` | Loads the same clustered bank for interactive edits | `instance_feat` indexes object regions by instance id; `label_feat` indexes them by semantic label. |

## Workflow order

1. Confirm the data layout in `../setup-and-data/`.
2. Confirm the checkpoint and memory assumptions in `../training/`.
3. For 1024p feature training, precompute `train_feat/` before launching the target `--load_features` run.
4. For feature inference, build or validate `features_clustered_*.npy` before asking `test.py` or `UIModel` to sample features.
5. Use `--use_encoded_image` only when you want the real image encoded at inference time rather than sampled cluster centers.

## Important cache facts

- `features.npy` and `features_clustered_*.npy` are dict-shaped `.npy` files.
- The cluster filename default is `features_clustered_010.npy` because the default `n_clusters` is 10.
- `feat_num` changes the feature width everywhere: checkpoint, cache, and precomputed feature-map outputs must all agree.
- Labels with no qualifying samples are omitted from the clustered cache.

# CLI Reference

This page summarizes the feature-sensitive flags and the repo-maintained command shapes that matter for feature-conditioned pix2pixHD workflows.

## Feature-sensitive flags

| Flag | Defined in | Meaning | Practical note |
| --- | --- | --- | --- |
| `--instance_feat` | `options/base_options.py` | Add encoded instance features as generator input | This is the stock feature recipe used by the bundled shell scripts. |
| `--label_feat` | `options/base_options.py` | Add encoded label features as generator input | Useful for label-conditioned variants and `UIModel`; the stock shell recipes do not use it. |
| `--load_features` | `options/base_options.py` | Read precomputed feature maps from `phase_feat/` | When this is set, the model skips building `netE` for that run. |
| `--feat_num` | `options/base_options.py` | Feature vector width | Default is `3`; changing it invalidates the encoder checkpoint and all feature caches. |
| `--n_clusters` | `options/base_options.py` | KMeans clusters per label | Default is `10`, which maps to the default cluster filename suffix `010`. |
| `--n_downsample_E` | `options/base_options.py` | Encoder depth | Advanced architecture knob; keep it aligned with the checkpoint that produced the cache. |
| `--nef` | `options/base_options.py` | Encoder filter width | Advanced architecture knob; changing it also changes the checkpoint shape. |
| `--cluster_path` | `options/test_options.py` | Cluster cache filename under `checkpoints/<name>/` | Defaults to `features_clustered_010.npy`. |
| `--use_encoded_image` | `options/test_options.py` | Encode the real image at test time | This is the alternate feature-inference branch; it needs a feature encoder checkpoint. |
| `--load_pretrain` | `options/train_options.py` | Load weights from another checkpoint directory | Used by the 1024p feature training recipes to bootstrap from the 512p feature checkpoint. |
| `--continue_train` | `options/train_options.py` | Resume from the current experiment directory | `encode_features.py` and `precompute_feature_maps.py` set this internally. |
| `--which_epoch` | `options/train_options.py` / `options/test_options.py` | Which checkpoint epoch to load | Defaults to `latest`. |

## Supported feature recipes

| Recipe | Printed by the helper | Main command shape |
| --- | --- | --- |
| 512p feature training | `python scripts/build_feature_command.py --recipe train_512p_feat` | `python train.py --name <name> --instance_feat ...` |
| 1024p feature training, 12G | `python scripts/build_feature_command.py --recipe train_1024p_feat_12G` | `python precompute_feature_maps.py --name <source> ... ; python train.py --name <target> --load_pretrain <source-checkpoint> --instance_feat --load_features ...` |
| 1024p feature training, 24G | `python scripts/build_feature_command.py --recipe train_1024p_feat_24G` | Same as above, but with the full-resolution schedule from the source shell recipe. |
| 512p feature cache + test | `python scripts/build_feature_command.py --recipe test_512p_feat` | `python encode_features.py --name <name> --n_clusters <n> ... ; python test.py --name <name> --instance_feat --cluster_path features_clustered_<n>.npy ...` |
| 1024p feature cache + test | `python scripts/build_feature_command.py --recipe test_1024p_feat` | Same structure as above, plus the local-enhancer flags required by the 1024p test recipe. |
| Cache inspection | `python scripts/check_feature_cache.py --repo-root . --name <name> --mode full --check-generator --check-encoder` | Validate `*_feat/` folders, clustered `.npy` outputs, and selected checkpoint files without launching training or inference. |

## Script-internal overrides

- `encode_features.py` forces `instance_feat=True`, `continue_train=True`, `batchSize=1`, `nThreads=1`, `serial_batches=True`, and `no_flip=True` before encoding.
- `precompute_feature_maps.py` forces the same single-item, non-shuffled settings and writes dense feature PNGs to `train_feat/`.
- Both helper scripts expect CUDA tensors and a model checkpoint that owns the feature encoder.
- The stock test shell recipes are feature-sampling recipes, not plain label-only inference commands.
- `test_1024p_feat.sh` contains a typo in the source repo (`---netG`). The bundled builder prints the corrected flag spelling.

## Manual variant notes

- `--label_feat` is supported by the model and the interactive `UIModel`, but it is not part of the stock feature shell recipes.
- `--use_encoded_image` is the only test-time feature branch that actively uses `netE` to encode the current image.
- `--load_features` and `--instance_feat` are not interchangeable: `--load_features` changes the data path to `phase_feat/`, while `--instance_feat` changes the object granularity used by the feature bank.

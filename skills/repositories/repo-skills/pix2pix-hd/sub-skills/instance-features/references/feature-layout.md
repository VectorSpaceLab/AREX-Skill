# Feature Layout

This page records the paths, file formats, and shape conventions used by the feature-conditioned pix2pixHD workflows.

## Directory tree

```text
checkpoints/<name>/
  latest_net_G.pth
  latest_net_D.pth
  latest_net_E.pth        # only when the encoder was actually trained
  features.npy
  features_clustered_010.npy

datasets/<dataroot>/
  train_label/
  train_inst/
  train_img/
  train_feat/              # created by precompute_feature_maps.py
  test_label/
  test_inst/
  test_img/                # present only when the dataset provides it
  test_feat/               # optional; supported by the loader if present
```

## What each artifact means

| Artifact | Produced by | Consumed by | Meaning |
| --- | --- | --- | --- |
| `latest_net_G.pth` | `train.py` | `test.py`, `precompute_feature_maps.py`, `encode_features.py` | Generator checkpoint for the feature-conditioned run. |
| `latest_net_D.pth` | `train.py` | resume / continued training | Discriminator checkpoint; not needed for sampled inference, but needed for a faithful resumed training run. |
| `latest_net_E.pth` | `train.py` when feature generation is enabled | `precompute_feature_maps.py`, `encode_features.py`, `test.py --use_encoded_image` | Feature encoder checkpoint. |
| `train_feat/*.png` | `precompute_feature_maps.py` | `train.py --load_features` | Dense 3-channel feature maps stored as images and reloaded with the normal image transform pipeline. |
| `features.npy` | `encode_features.py` | cache inspection / clustering | Dict keyed by class label; each row has `feat_num + 1` columns. The last column is the normalized size score. |
| `features_clustered_%03d.npy` | `encode_features.py` + KMeans | `test.py --instance_feat`, `UIModel` | Dict keyed by class label; each value is an array of cluster centers with width `feat_num`. |

## Shape reminders

- `feat_num` is the channel count of the feature vector, not the spatial size.
- `precompute_feature_maps.py` upsamples the encoder output by a factor of 2 before saving the PNG, so the saved map is spatially aligned with the 1024p training recipe.
- `encode_features.py` keeps one feature row per instance object and appends the area score in the last column before clustering.
- `features_clustered_*.npy` stores only cluster centers; labels with no qualifying objects are omitted.
- When you inspect the `.npy` files manually, treat them as dict-like object caches and load them with pickle enabled if your NumPy defaults are strict.

## Alignment rules

1. `AlignedDataset` loads `phase_label`, `phase_inst`, `phase_img`, and `phase_feat` using the same sorted file order.
2. The feature folder name must match the phase name exactly: `train_feat` goes with `train_label`, `test_feat` goes with `test_label`.
3. `precompute_feature_maps.py` derives the output filename by replacing `/train_label/` with `/train_feat/` in the source path.
4. `check_feature_cache.py` compares filename stems so it can catch a missing or misordered feature map before training starts.
5. Changing `feat_num`, `n_clusters`, or the source checkpoint invalidates the cache pair and requires regeneration.

## Checkpoint requirements by stage

| Stage | Must exist | Optional / tolerated | Why |
| --- | --- | --- | --- |
| `train.py --instance_feat` (512p feature source) | `latest_net_G.pth`, `latest_net_D.pth`, `latest_net_E.pth` | none | This is the checkpoint that later encode/precompute steps consume. |
| `precompute_feature_maps.py` | Source checkpoint with `latest_net_E.pth` | `latest_net_D.pth` after the model is already loaded | The script calls `netE` directly to build `train_feat/`. |
| `train.py --load_features` (1024p feature target) | Source checkpoint for `--load_pretrain`, plus `train_feat/` | Target `latest_net_E.pth` is not created in this mode | The target run consumes cached feature maps instead of building `netE`. |
| `encode_features.py` | Source checkpoint with `latest_net_E.pth` | `latest_net_D.pth` after loading | The script extracts per-object feature rows before running KMeans. |
| `test.py --instance_feat` | `latest_net_G.pth`, `features_clustered_*.npy` | `latest_net_E.pth` if you are only sampling clusters | The sampled-feature inference branch uses the cluster bank and the generator checkpoint. |
| `test.py --use_encoded_image` | `latest_net_G.pth`, `latest_net_E.pth` | `features_clustered_*.npy` | This branch encodes the real image instead of sampling cluster centers. |

## Cache regeneration rules

- If `feat_num` changes, regenerate `train_feat/`, `features.npy`, and `features_clustered_*.npy` together.
- If `n_clusters` changes, regenerate the clustered cache and update the `--cluster_path` passed to test-time commands.
- If the source checkpoint changes, treat both the feature maps and clustered `.npy` files as stale.
- If a label is absent from `features_clustered_*.npy`, first check whether all of its objects were filtered out by the object-size threshold in `encode_features.py`.

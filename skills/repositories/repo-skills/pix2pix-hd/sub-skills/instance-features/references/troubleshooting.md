# Troubleshooting

## Fast failure map

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: No module named sklearn` or `cannot import name KMeans` | You are running the clustering stage without `scikit-learn` installed. Only `encode_features.py` needs it. | Install `scikit-learn` in the feature workflow environment, or skip clustering and reuse an existing `features_clustered_*.npy` file. The bundled command builder will warn when the encode stage is requested without KMeans. |
| `FileNotFoundError: checkpoints/<name>/features_clustered_010.npy` | The cluster cache is missing or the experiment name is wrong. | Regenerate the cache with `encode_features.py --name <correct-experiment> --n_clusters 10`, or pass `--cluster_path` so `test.py` points at the file that actually exists. |
| `FileNotFoundError: checkpoints/<name>/latest_net_E.pth` | You pointed `encode_features.py` or `precompute_feature_maps.py` at a checkpoint that never trained the feature encoder, or you used the wrong experiment name. | Use the checkpoint that actually saved `netE` (usually the 512p feature source checkpoint), or retrain with feature generation enabled so `latest_net_E.pth` exists. |
| `train_feat` missing, `feat_paths[index]` out of range, or the target training run cannot find feature maps | You started a `--load_features` run before running `precompute_feature_maps.py`, or the folder names do not follow the `train_label` / `train_feat` convention. | Run `precompute_feature_maps.py` first and keep the standard phase naming intact. |
| `test.py --instance_feat` produces a traceback about the feature cache path | The clustered file is missing or the `cluster_path` does not match the `n_clusters` used during encoding. | Regenerate the cluster file and pass the matching `--cluster_path`, for example `features_clustered_010.npy` for the default `n_clusters=10`. |
| `Shape mismatch`, odd colors, or stale-looking feature maps | `feat_num` changed, or you mixed caches from different checkpoints / cluster counts. | Regenerate `train_feat/`, `features.npy`, and `features_clustered_*.npy` together whenever `feat_num`, `n_clusters`, or the source checkpoint changes. |
| Some labels never appear in the cluster bank | `encode_features.py` filters out tiny objects and caps clusters by the number of surviving rows per label. | This is normal. If the omission is unexpected, inspect the object-size threshold and the source dataset before rebuilding the cache. |
| `TypeError: Object arrays cannot be loaded when allow_pickle=False` while inspecting caches manually | Modern NumPy is being stricter than the legacy repo helpers. | Use `check_feature_cache.py` or load the `.npy` dicts with `allow_pickle=True`. |
| `CUDA` / `.cuda()` failures | The feature scripts are CUDA-oriented; they call `.cuda()` directly and assume a GPU-backed checkpoint. | Run on the verified CUDA host or switch to a non-feature workflow. CPU-only execution is not a supported path for these helpers. |
| `test_1024p_feat.sh` copies with `---netG` and fails immediately | The source shell recipe has a typo. | Use `build_feature_command.py`; it prints the corrected `--netG` flag. |

## Ordering mistakes to watch for

- `--load_features` and `--instance_feat` are not interchangeable. `--load_features` switches the data path to `phase_feat/`; `--instance_feat` only changes how the feature bank is indexed.
- `encode_features.py` and `precompute_feature_maps.py` hardcode `instance_feat=True` internally. If you want a `label_feat` variant, build that command manually instead of relying on the bundled helper script.
- `test.py --use_encoded_image` is a different feature-inference branch from cluster sampling. It needs the feature encoder checkpoint and is the only test path that actively uses `netE` at inference time.
- For 1024p feature training, the target run consumes cached `train_feat/` maps and does not need to build a new encoder checkpoint.

## Optionality reminder

- Plain label-only training and plain inference are still valid pix2pixHD workflows.
- Only use this sub-skill when the task explicitly needs feature encoding, clustering, cached feature maps, or feature-conditioned inference/editing.

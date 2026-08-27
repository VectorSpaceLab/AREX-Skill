---
name: instance-features
description: "Use pix2pixHD's instance-aware feature encoding, clustering,
  feature caches, and feature-conditioned train/test workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Instance Features

Use this sub-skill when a pix2pixHD task depends on encoded instance features, label-level feature variants, precomputed feature maps, or the clustered `.npy` cache that drives feature-conditioned training and inference.

## Route Here For
- `encode_features.py` and `precompute_feature_maps.py`
- `--instance_feat`, `--label_feat`, `--load_features`, `--feat_num`, `--n_clusters`
- `features.npy`, `features_clustered_*.npy`, and `*_feat/` dataset folders
- checkpoint requirements for source encoders and feature-conditioned inference
- KMeans / `scikit-learn` availability
- safe construction of the feature-aware commands from `scripts/*feat*.sh`
- UIModel-style interactive feature editing that reuses the same clustered feature bank

## Route Elsewhere
- Dataset layout, label/instance pairing, and basic preprocessing: [setup-and-data](../setup-and-data/SKILL.md)
- Plain training, VRAM planning, or checkpoint resume behavior: [training](../training/SKILL.md)
- Plain test-time synthesis, HTML output, or non-feature inference: [inference](../inference/SKILL.md)

## Core Rules
1. `instance_feat` and `label_feat` both enable the feature path. The published helper recipes default to `instance_feat`; `label_feat` redirects the feature source to labels in the encoder path and is mainly relevant when you are reasoning about the model/UI code.
2. `load_features` means the dataset supplies precomputed feature maps from `phase_feat/` and the model does not build `netE`.
3. `feat_num` is the channel width of the feature vectors. Changing it invalidates old `features.npy`, `features_clustered_*.npy`, and `train_feat/` caches.
4. `n_clusters` controls the per-label KMeans count and the cluster filename suffix. The test-time default is `features_clustered_010.npy`.
5. Use the bundled helper scripts first; they print commands and validate caches without launching long jobs.

## Fast Path
From this sub-skill directory, pass the actual pix2pixHD checkout as `--repo-root`:

```bash
python scripts/check_feature_cache.py --repo-root <repo-root> --name label2city_512p_feat --mode full --check-generator --check-encoder
python scripts/build_feature_command.py --repo-root <repo-root> --recipe train_1024p_feat_24G
```

## Boundaries
- Do not use this sub-skill for label-only training or plain inference without feature conditioning.
- Do not route TensorRT, vendor runtimes, or other accelerator deployment paths here.
- Do not promise an encode/clustering step unless the required feature checkpoint and `scikit-learn` / `KMeans` are available.

## References
- [Workflows](references/workflows.md): read for encode, precompute, feature-train, and feature-test sequences.
- [CLI reference](references/cli-reference.md): read for feature flags and defaults.
- [Feature layout](references/feature-layout.md): read for cache files, `*_feat/` folders, and checkpoint expectations.
- [Troubleshooting](references/troubleshooting.md): read for missing KMeans, cache, checkpoint, and CUDA failures.

## Bundled Scripts
- [build_feature_command.py](scripts/build_feature_command.py): run to print feature workflow commands without launching long jobs.
- [check_feature_cache.py](scripts/check_feature_cache.py): run to validate feature caches and precomputed feature-map folders.

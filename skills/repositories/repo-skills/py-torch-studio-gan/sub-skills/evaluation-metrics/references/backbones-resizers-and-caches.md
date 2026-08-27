# Backbones, resizers, and reference caches

StudioGAN separates the metric formula from the feature network and resize convention. Future agents should record all three when reporting a score: metric name, `--eval_backbone`, and `--post_resizer`.

## Evaluation backbones

| `--eval_backbone` value | Feature resolution | Weight/cache behavior | Best-fit use |
| --- | --- | --- | --- |
| `InceptionV3_tf` | 299 | Loads the PyTorch port of the TensorFlow FID Inception weights through the standard PyTorch model cache mechanism. | Default StudioGAN convention for IS/FID/PRDC and clean/friendly comparisons using an Inception-style network. |
| `InceptionV3_torch` | 299 | Uses `torch.hub.load` from the torchvision hub tag and pretrained torchvision Inception weights. | PyTorch-native Inception comparison; not numerically identical to the TensorFlow-FID port. |
| `ResNet50_torch` | 224 | Uses `torch.hub.load` from the torchvision hub tag and pretrained ResNet-50 weights. | Architecture-friendly metrics with an ImageNet classifier backbone. |
| `SwAV_torch` | 224 | Uses `torch.hub.load` for a SwAV ResNet-50 and additionally downloads/loads a linear classifier state dict. | Architecture-friendly metrics based on SwAV features. |
| `DINO_torch` | 224 | Builds a ViT-small DINO model and loads DINO teacher plus linear weights through PyTorch URL cache helpers. | Architecture-friendly metrics with DINO features. |
| `Swin-T_torch` | 224 | Builds the bundled Swin transformer class and loads a public Swin checkpoint through PyTorch URL cache helpers. | Architecture-friendly metrics with Swin transformer features. |

Network/cache implications:

- The first use of a backbone may download weights. In offline runs, pre-populate the relevant PyTorch cache or choose a backbone whose weights are already available.
- A backbone can fail before any image metrics are computed if hub access, URL downloads, certificate validation, or cache permissions fail.
- Switching backbones changes feature dimensionality and metric semantics. Do not reuse moments/features created with another backbone.

## Post-resizer choices

| `--post_resizer` value | Implementation intent | Practical guidance |
| --- | --- | --- |
| `legacy` | PyTorch bilinear resize inside the metric path. | Default. Use when matching StudioGAN's historical/default benchmark behavior. |
| `clean` | PIL bicubic resize following clean-FID style resizing. | Use for clean metric comparisons; keep preprocessing and reporting explicit. |
| `friendly` | Backbone-specific PIL filter: InceptionV3_tf/ResNet50/SwAV/DINO use bilinear, InceptionV3_torch uses lanczos, Swin-T uses bicubic. | Use for architecture-friendly metric experiments; always report the backbone too. |

Preprocessing mismatch caution:

- `--post_resizer` is not the same as training/data `--pre_resizer` from `src/main.py`.
- Folder evaluation assumes images in `--dset1` and `--dset2` are already the intended images. It then applies the post-resizer to feed the evaluation network.
- If training used a particular pre-resizer and folder evaluation uses a different post-resizer protocol, document both. Do not silently compare against old cached moments/features from another protocol.

## Feature and moment caches

StudioGAN creates and consumes two different cache types for the real/reference dataset:

| Cache type | Needed by | Required arrays | Created by StudioGAN training-time preparation | Standalone flag |
| --- | --- | --- | --- | --- |
| Moments | FID | `mu`, `sigma` | The moment-preparation path saves a `.npz` file under the run's moments area. | `--dset1_moments` |
| Features | PRDC | `real_feats`; training-time cache may also include `real_probs`, `real_labels` | The real-feature preparation path saves a `.npz` file under the run's features area. | `--dset1_feats` |

Rules for cache reuse:

- Cache provenance must match the real dataset split, image preprocessing, post-resizer, evaluation backbone, and StudioGAN version/protocol.
- `--dset1_feats` is not enough for FID; `--dset1_moments` is not enough for PRDC.
- If a user has only one cache and requests both `fid` and `prdc`, either supply `--dset1` as well or compute/acquire the missing cache.
- The source help text says `*.npy` for some cache paths, but the current implementation indexes named arrays from `np.load(...)`; use StudioGAN-style `.npz` caches for robust operation.

Use [check_metric_inputs.py](../scripts/check_metric_inputs.py) to validate cache suffixes and keys without loading full arrays.

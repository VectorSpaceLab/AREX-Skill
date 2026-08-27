# Repository provenance

- **Schema:** `disco.repo-provenance.v1`
- **Repository:** NVlabs/VoxFormer
- **Source commit:** `63da92415447c2e97654bad977254c907f5ce703`
- **Branch:** `main`
- **Source package version:** not declared; this is an application/plugin checkout.
- **Source state used:** the tracked source at the commit above. Generated
  review artifacts and transient bytecode/build outputs are not runtime
  evidence.
- **Primary evidence:** `README.md`, `docs/install.md`,
  `docs/prepare_dataset.md`, `docs/getting_started.md`, `preprocess/README.md`,
  `preprocess/label/`, `preprocess/utils/`, `projects/`,
  `projects/configs/voxformer/`, `tools/`, and `deform_attn_3d/`.
- **Excluded evidence:** datasets, calibration corpora, checkpoints, teaser
  media, generated/platform-specific binaries, the embedded MobileStereoNet
  implementation, caches, and full training/evaluation outputs.
- **Documented dependency family:** Python 3.8; PyTorch 1.9.1/cu111;
  torchvision 0.10.1; mmcv-full 1.4.0; mmdet 2.14.0; mmsegmentation 0.14.1;
  mmdetection3d v0.17.1; timm; plus CUDA native extensions for the selected
  runtime variants.
- **Freshness rule:** if configs, dataset classes, custom-op wrapper, tool
  parsers, or dependency pins change, treat this skill as potentially stale;
  refresh it from a new source commit before relying on exact field behavior.

The skill deliberately uses user-supplied placeholders for checkout, data,
checkpoint, and environment paths. It does not depend on the source checkout
remaining available after generation.

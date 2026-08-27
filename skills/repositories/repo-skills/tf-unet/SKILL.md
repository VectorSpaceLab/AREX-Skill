---
name: tf-unet
description: "Build, train, and inspect tf_unet TensorFlow 1.x
  image-segmentation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# tf_unet

Use this skill when the task names `tf_unet`, `tf-unet`, TensorFlow U-Net, image segmentation with this package, or the bundled toy/demo launchers.

This is a legacy TensorFlow 1.x package. Keep `tf.Session`, `tf.placeholder`, and `tf.reset_default_graph` in mind. Read `references/installation-and-compatibility.md` before changing environments.

## Quick start

1. Run `scripts/check_tf_unet_env.py` to confirm the install, TensorFlow 1.x import, and a tiny model build.
2. Read `references/troubleshooting.md` when import errors, protobuf mismatches, or shape problems show up.
3. Route to a sub-skill:
   - `sub-skills/training-and-inference/SKILL.md` for `Unet`, `Trainer`, losses, save/restore, prediction, and visualization.
   - `sub-skills/data-providers-and-launchers/SKILL.md` for `BaseDataProvider`, `ImageDataProvider`, `GrayScaleDataProvider`, `RgbDataProvider`, and launcher notebooks/scripts.
4. Use `references/repo-provenance.md` to compare this skill with the source snapshot.

## Installation

A compatible baseline is Python 3.7 plus TensorFlow 1.15.5 and protobuf 3.20.3. Add `click`, `Pillow`, `matplotlib`, `scipy`, and `h5py` when you need the launcher workflows. Install the distribution that exposes `tf_unet` in your environment, then run the root smoke helper.

```bash
python -m pip install tensorflow==1.15.5 protobuf==3.20.3 click Pillow matplotlib scipy h5py
python scripts/check_tf_unet_env.py
```

## What this skill covers

- Toy circle segmentation and generic image-segmentation experiments.
- Checkpoint creation, restore, prediction, and output image composition.
- TIFF/HDF5/NumPy data-provider patterns and the bundled launcher workflows.
- Safe inspection only; do not assume the original checkout is available at runtime.

## Routing cues

- A request about the network graph, optimizer, loss, or prediction output belongs in `training-and-inference`.
- A request about image files, one-hot labels, HDF5 chunks, or dataset-specific launcher patterns belongs in `data-providers-and-launchers`.
- A request about install or runtime compatibility belongs in the root references.
- A request about docs/build automation or binder bootstrap is out of scope unless it is needed to explain a user-facing workflow.

## Bundled references

- `references/installation-and-compatibility.md` — read for package/dependency versions, Python guidance, and the protobuf pin that keeps TF 1.15.x importable.
- `references/troubleshooting.md` — read for TensorFlow 1.x, shape, file layout, and launcher pitfalls.
- `references/repo-provenance.md` — read to compare this skill with the source snapshot.
- `references/repo-routing-metadata.json` — consumed by the repo-skills router during import.

## Bundled scripts

- `scripts/check_tf_unet_env.py` — run when you need a tiny import/build/save/restore smoke before touching a workflow.
- `sub-skills/training-and-inference/scripts/smoke_train_restore.py` — run when you need a tiny training/predict smoke tied to the model graph.
- `sub-skills/data-providers-and-launchers/scripts/smoke_data_providers.py` — run when you need to validate provider shapes and image/mask pairing on synthetic fixtures.

## Common safety notes

- Keep training smoke tiny; this package was validated with a small synthetic model, not a long training job.
- Do not tell future agents to run original repo notebooks or scripts from the source checkout. If a workflow matters, use the bundled references and scripts in this skill tree.
- Treat external datasets as optional evidence, not as runtime dependencies.

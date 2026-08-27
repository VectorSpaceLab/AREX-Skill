# PointCNN repository provenance

Schema: `disco.repo-provenance.v1`

- **Repository:** `yangyanli/PointCNN`
- **Source commit:** `dcb1355eeddb514fea289e9350d50ffa85c4115a`
- **Branch:** `master`
- **Snapshot state at extraction:** source checkout clean; generated skill and review artifacts are untracked under `skills/` and are not source evidence.
- **Latest source commit subject:** `Link to PointCNN++`
- **Public project version:** no package version or release tag is declared in the checkout.
- **Framework baseline:** README documents TensorFlow 1.6-era graph-mode code and says TensorFlow before 1.5 is not recommended; the private inspection snapshot imported TensorFlow 1.15.0. Treat this as a compatibility baseline, not a universal lock.
- **Declared dependencies:** matplotlib, plyfile, python-mnist, requests, scipy, svgpathtools, tensorflow-gpu >= 1.6.0, tqdm, and transforms3d. `requirements.txt` is not a complete legacy compatibility lock.

## Evidence paths

Core graph and operators: `pointcnn.py`, `pointcnn_cls.py`, `pointcnn_seg.py`,
`pointfly.py`, `sampling/tf_sampling.py`, `sampling/tf_sampling.cpp`, and
`sampling/tf_sampling_g.cu`.

Workflows: `train_val_cls.py`, `train_val_seg.py`, `test_general_seg.py`,
`test_shapenet_seg.py`, `pointcnn_cls/`, and `pointcnn_seg/`.

Data and artifacts: `data_utils.py`, `data_conversions/`, and `evaluation/`.

Public intent and command examples: `README.md`,
`data_conversions/README.md`, `evaluation/README.md`, and `requirements.txt`.

## Refresh signals

Refresh this skill when the source commit changes, TensorFlow compatibility or
custom-op registration changes, setting modules are renamed, HDF5 keys or
prediction formats change, or dataset/evaluation workflows gain new supported
backends. Compare the current relative paths and setting tuples before reusing
this guide for a newer checkout.

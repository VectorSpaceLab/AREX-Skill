# Repository provenance

- Schema: `disco.repo-provenance.v1`.
- Source repository: `amdegroot/ssd.pytorch`.
- Public remote URL: `https://github.com/amdegroot/ssd.pytorch.git`.
- Source commit: `5b0b77faa955c1917b0c710d770739ba8fbff9b7`.
- Branch at generation: `master`.
- Exact tag at generation: none detected.
- Package/distribution version: none detected; repository has no `pyproject.toml`, `setup.py`, `setup.cfg`, or requirements metadata in the inspected tree.
- License evidence: `LICENSE`.
- Working-tree state: source checkout was clean before generated skill files were created; after generation, the `skills/` tree contains this skill and review artifacts.

## Evidence paths

Primary evidence used to build this skill:

- `README.md`
- `ssd.py`
- `layers/box_utils.py`
- `layers/functions/prior_box.py`
- `layers/functions/detection.py`
- `layers/modules/l2norm.py`
- `layers/modules/multibox_loss.py`
- `data/__init__.py`
- `data/config.py`
- `data/voc0712.py`
- `data/coco.py`
- `data/coco_labels.txt`
- `utils/augmentations.py`
- `train.py`
- `eval.py`
- `test.py`
- `demo/live.py`
- `demo/demo.ipynb`
- `data/scripts/VOC2007.sh`
- `data/scripts/VOC2012.sh`
- `data/scripts/COCO2014.sh`

## Refresh cues

Refresh this repo skill when:

- `build_ssd`, `Detect`, prior-box configs, or `MultiBoxLoss` changes.
- The repository adds packaging metadata, requirements, console entry points, or modern PyTorch compatibility patches.
- Dataset layout, label-map handling, training/evaluation flags, or pretrained-weight locations change.
- Demo dependencies or notebook workflows change.

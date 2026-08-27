# Repo provenance

## Source repository state

- Repository: `MrGiovanni/UNetPlusPlus`
- Current commit: `db124279549ed983b9dbce1ef50831aaeecf6452`
- Branch: `master`
- Exact tag at HEAD: none
- Remote URL: `https://github.com/MrGiovanni/UNetPlusPlus.git`
- Working tree state at capture time: dirty
- Dirty evidence: generated runtime skill output under `skills/`

## Package version anchors

- PyTorch / nnU-Net package version: `1.6.4` from `pytorch/setup.py`
- Keras segmentation model bundle version: `0.1.2` from
  `keras/segmentation_models/__version__.py`

## Evidence paths used to generate this skill

- `README.md`
- `pytorch/README.md`
- `pytorch/setup.py`
- `pytorch/setup.cfg`
- `pytorch/nnunet/**`
- `pytorch/tests/test_steps_for_sliding_window_prediction.py`
- `keras/README.md`
- `keras/requirements.txt`
- `keras/helper_functions.py`
- `keras/BRATS2013_application.py`
- `keras/segmentation_models/**`

## Staleness check hints

Future agents should refresh or re-verify this skill if:

- The source commit changes.
- The nnU-Net entry points or trainer classes move.
- The Keras segmentation model exports change.
- The repo layout under `pytorch/` or `keras/` changes.
- The generated skill tree diverges from the listed evidence paths.

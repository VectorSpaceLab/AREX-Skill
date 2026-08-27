# Repository provenance

This operating skill was distilled from the following public repository
snapshot:

- Repository: `osmr/imgclsmob`
- Remote: `https://github.com/osmr/imgclsmob.git`
- Commit: `c1a844dde061f6d72f25011dc1af9a2e35b1bdfc`
- Branch: `master`
- Exact tag: none recorded at the snapshot
- Working tree: clean at evidence capture
- Snapshot date: 2024-09-06 commit date

## Package/version anchors

- `gluoncv2`: `0.0.64`
- `tf2cv`: `0.0.18`
- `tensorflowcv`: `0.0.38`
- `kerascv`: `0.0.40`
- `chainercv2`: `0.0.62`
- PyTorch model provider: external `pytorchcv`; the repository-local
  `pytorchcv/` directory is empty at this snapshot and is not treated as the
  provider implementation.
- Separate CPU inspection environment (not the repository snapshot or a bundled runtime): MXNet `1.9.1`, PyTorch `2.5.1+cpu`, torchvision `0.20.1+cpu`, and external `pytorchcv` `0.0.74`.

The package anchors above describe the published snapshot. The CPU inspection
versions are separate evidence from the inspection environment; they are not
installation requirements and do not verify optional backends.

## Relative evidence paths

The paths below are **upstream-snapshot evidence paths**, relative to the
`osmr/imgclsmob` checkout at the commit above. They are not links into this
skill bundle and must not be resolved relative to an installed skill directory.
If that checkout is unavailable, treat these names as provenance pointers only,
not as bundled files or runnable entry points.

- Public orientation: `README.md`, `gluon/README.md`,
  `tensorflow2/README.md`, `tensorflow_/README.md`, `keras_/README.md`,
  `chainer_/README.md`
- Model providers: `gluon/gluoncv2/model_provider.py`,
  `tensorflow2/tf2cv/model_provider.py`,
  `tensorflow_/tensorflowcv/model_provider.py`,
  `keras_/kerascv/model_provider.py`,
  `chainer_/chainercv2/model_provider.py`
- Verified utilities: `gluon/utils.py`, `pytorch/utils.py`,
  `tensorflow2/utils.py`, `tensorflow_/utils.py`, `keras_/utils.py`,
  `chainer_/utils.py`
- Dataset contracts: `gluon/dataset_utils.py`, `pytorch/dataset_utils.py`,
  `tensorflow2/dataset_utils.py`, and the corresponding `datasets/` trees
- Workflow CLIs: `train_gl.py`, `eval_gl.py`, `train_pt.py`, `eval_pt.py`,
  `train_tf2.py`, `eval_tf2.py`, `train_tf.py`, `eval_tf.py`, `train_ke.py`,
  `eval_ke.py`, `train_ch.py`, `eval_ch.py`
- Preparation/conversion: `load_model.py`, `prep_model.py`,
  `convert_models.py`
- Examples and conversion evidence: `examples/`, `tests/convert_gl2pt_*`,
  `tests/convert_gl2tf2_*`, and `tests/convert_gl2tf_*`
- Metadata: framework `setup.py` files, `requirements.txt`, and `.travis.yml`

## Refresh signal

Refresh this skill when model-provider registration, utility signatures,
dataset metainfo names/layouts, conversion dispatch, CLI flags, or framework
package versions change. The optional framework rows are intentionally
bounded-unverified in this production snapshot; a future refresh should not
promote them to verified without a matching backend smoke.

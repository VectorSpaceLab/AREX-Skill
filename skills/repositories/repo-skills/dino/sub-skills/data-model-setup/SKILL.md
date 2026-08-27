---
name: data-model-setup
description: "Prepare and validate DINO's COCO-style inputs, model/config
  shapes, and CUDA deformable-attention backend before training or evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DINO data and model setup

Use this route before a DINO training or evaluation run when the dataset,
model configuration, or compiled backend is new, changed, or suspect. It
builds no dataset and does not launch training, inference, or evaluation.

## Route and gates

1. **Environment gate.** Run
   [`scripts/check_dino_environment.py`](scripts/check_dino_environment.py)
   with the strict requirements appropriate to the requested run. For the
   standard CUDA DINO path, use:

   ```bash
   python scripts/check_dino_environment.py --require-cuda \
     --require-extension --require-coco --require-runtime --pip-check --json
   ```

   It checks package imports, PyTorch/CUDA visibility, `CUDA_HOME`/`nvcc`
   observations, the `MultiScaleDeformableAttention` import, and optionally
   `pip check`. Add `--require-panoptic` only for the panoptic branch. Use
   `--smoke-cuda` and `--smoke-extension` only when a free visible GPU is
   available; import/symbol success is not the repository's numerical
   operator gate.
2. **Data gate.** Run
   [`scripts/validate_coco_layout.py`](scripts/validate_coco_layout.py) against
   an existing COCO root. Validate only the requested split(s); add the
   optional panoptic root only when panoptic data is actually needed.
3. **Target gate.** Confirm the dataset yields the fields and coordinate
   conventions in [data formats](references/data-formats.md), including the
   `num_classes`/category-ID convention and transformed `size` versus
   `orig_size`.
4. **Model gate.** Compare the selected config with the backbone, returned
   feature levels, hidden dimension, attention heads, number of queries, class
   count, and denoising label-book rules in
   [model architecture](references/model-architecture.md).
5. **Extension gate.** If the model will run its deformable encoder/decoder,
   compile and run the repository's CUDA operator test as described in
   [environment](references/environment.md). A package import alone is not a
   numerical proof.

Stop on a failed strict gate. Report the exact failed check and apply the
corresponding recovery in [troubleshooting](references/troubleshooting.md)
rather than silently falling back to an incompatible backend.

## Operating procedure

- Treat `coco_path` as a read-only input to this route. The standard instance
  layout is `train2017/`, `val2017/`, and `annotations/`; the expected JSON
  names are `instances_train2017.json` and `instances_val2017.json`. The test
  split uses `test2017/` and `image_info_test-dev2017.json` when requested.
- Validate annotation references and image filenames before importing the
  dataset loader. Do not use the repository's optional `DATA_COPY_SHILONG`
  path here: its helper removes/recreates paths and is outside this skill's
  safety boundary.
- For a custom dataset, decide the maximum category ID and config class
  convention together. This repository's `num_classes` is a classifier width
  / maximum-object-ID-plus-one convention, not simply the count of category
  names. Recheck `dn_labelbook_size` after changing it.
- Confirm transforms are appropriate for the run. Training uses random flip,
  multiscale resize and a random crop branch; validation/evaluation uses a
  deterministic largest configured resize followed by normalization. The
  resulting boxes are normalized `(center_x, center_y, width, height)`.
- Compile the extension only after confirming a CUDA-enabled PyTorch, a
  matching toolkit, a compatible host compiler (use GCC <= 12 when required
  by the toolkit), valid CUDA and CCCL include directories, and a free GPU.
  Keep build outputs in the normal build area; this route provides no cleanup,
  copy, download, or deletion helper.
- Route **training launches, optimizer/scheduler settings, and checkpoints**
  to the parent skill's training route. Route **prediction, post-processing,
  and COCO/panoptic evaluation** to its inference/evaluation route. This
  sub-skill supplies their setup facts only.

## Expected handoff

Record the following for the next route: validated root and split(s), JSON
files checked, image/annotation counts and warnings, whether masks/panoptic
paths were checked, config name and salient shape settings, package/CUDA
observations, extension import and numerical-test status, and unresolved
backend limitations. Never record private machine prefixes, private dataset
locations, or credentials.

## References

- [COCO data formats and targets](references/data-formats.md)
- [DINO model architecture and compatibility](references/model-architecture.md)
- [Environment installation and extension build](references/environment.md)
- [Troubleshooting and recovery](references/troubleshooting.md)

## Scope and limitations

This is a preparation and validation route. It deliberately excludes dataset
acquisition, checkpoint acquisition, training/evaluation launch commands,
checkpoint surgery, destructive copy helpers, and claims that a CPU execution
is an equivalent substitute for DINO's CUDA multi-scale deformable attention.
The supplied scripts are read-only except for their `--fixture` mode, which
creates and removes only a temporary self-test fixture.

## Evidence provenance

This skill was distilled from the repository README installation/data sections;
`requirements.txt`; `datasets/coco.py`, `coco_panoptic.py`, `transforms.py`,
`dataset.py`, and `data_util.py`; the deformable-attention setup, test,
function, and module files under `models/dino/ops/`; `models/dino/backbone.py`,
`deformable_transformer.py`, and `dino.py`; `util/slconfig.py`; all
`config/DINO/*.py`; `tools/README.md`; and the verified environment report
for this repository. The report established a successful CUDA extension build
and import, COCO dependency imports, and `pip check`; it did not establish a
full training or evaluation result.

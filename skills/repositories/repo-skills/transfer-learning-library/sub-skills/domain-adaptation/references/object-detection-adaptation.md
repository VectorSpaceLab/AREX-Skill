# Object Detection Adaptation

This reference covers the D-adapt / cross-domain object detection branch of the domain-adaptation skill.
It is intentionally optional-stack guidance: do not treat it as CPU-smoke coverage.

## When to use this branch

Use this branch when the user wants one of the following:

- source-only or adapted detection on VOC, Clipart, WaterColor, Comic, Cityscapes, Foggy Cityscapes, or Sim10k-style tasks,
- Decoupled Adaptation for Cross-Domain Object Detection (D-adapt),
- CycleGAN-translated detection datasets,
- proposal/feedback handling for unlabeled target images.

## Required stack

The workflow depends on an object-detection runtime that matches Detectron2-style meta-architectures.
Common optional dependencies in the example suite include:

- Detectron2-compatible PyTorch / CUDA wheels,
- `timm`,
- `mmcv`,
- `prettytable`,
- `pascal_voc_writer`.

If that stack is missing, keep the guidance at the reference level and do not claim execution support.

## Data preparation patterns

### Standard detection datasets

The benchmark recipes expect VOC-like layouts for several tasks and use dataset-specific conversion or registration helpers.
Typical families are:

- VOC2007 / VOC2012,
- Clipart,
- WaterColor,
- Comic,
- Cityscapes and Foggy Cityscapes,
- Sim10k.

### Translated datasets

Some recipes also use translated source images.
The workflow usually looks like:

1. translate the source domain into the target style,
2. keep the original detector labels,
3. train or adapt the detector on the translated source plus target supervision/feedback.

## Workflow shape

### 1) Source-only detector

Train a detector on the source domain first.
This stage produces the pretrained detector checkpoint that D-adapt builds on.

### 2) D-adapt stage

Run the decoupled adaptation stage after the source model exists.
The adaptation is split into independent pieces:

- a detector,
- a category adaptor,
- a bounding-box adaptor.

That split is deliberate and is one of the main reasons the workflow is easier to modify than a monolithic detector loop.

### 3) Optional visualization

Use the visualization path to inspect predictions, background proposals, and feedback boxes.
This is a debugging aid, not a substitute for training verification.

## Core runtime APIs

### Proposal and feedback data

- `tllib.alignment.d_adapt.proposal.Proposal`
- `tllib.alignment.d_adapt.proposal.PersistentProposalList`
- `tllib.alignment.d_adapt.proposal.ProposalDataset`
- `tllib.alignment.d_adapt.proposal.ExpandCrop`
- `tllib.alignment.d_adapt.proposal.ProposalMapper`
- `tllib.alignment.d_adapt.proposal.ProposalGenerator`
- `tllib.alignment.d_adapt.feedback.load_feedbacks_into_dataset`
- `tllib.alignment.d_adapt.feedback.get_detection_dataset_dicts`
- `tllib.alignment.d_adapt.feedback.transform_feedbacks`
- `tllib.alignment.d_adapt.feedback.DatasetMapper`

### Detectron2-style model classes

- `tllib.alignment.d_adapt.modeling.meta_arch.DecoupledGeneralizedRCNN`
- `tllib.alignment.d_adapt.modeling.meta_arch.DecoupledRetinaNet`
- `tllib.alignment.d_adapt.modeling.roi_heads.DecoupledRes5ROIHeads`
- `tllib.alignment.d_adapt.modeling.roi_heads.DecoupledStandardROIHeads`
- `tllib.alignment.d_adapt.modeling.roi_heads.fast_rcnn.DecoupledFastRCNNOutputLayers`
- `tllib.alignment.d_adapt.modeling.matcher.MaxOverlapMatcher`

### Supporting transfer-learning detection bases

The D-adapt classes extend TLLib's transfer-learning detector bases in `tllib.vision.models.object_detection.meta_arch`.
They accept unlabeled inputs during training and expose both detection outputs and losses in train mode.

## CLI pattern to describe to users

Keep the pattern abstract rather than pointing to a repository script path.
A good description is:

- a source-only stage with source, target, and test dataset lists,
- a config file for the detector backbone/head settings,
- a finetune toggle,
- an eval-only toggle,
- distributed-training switches when GPUs are available.

For D-adapt itself, explain that the category and bbox adaptor argument families are separated, and that the latter two usually use suffixed flag groups to avoid collisions.

### Useful flags to mention

- `--bbox-refine`
- `--reduce-proposals`
- `--trade-off`
- `--config-file`
- `--eval-only`
- `--finetune`
- dataset `-s/--sources`, `-t/--targets`, and `--test`

## Practical constraints

- Require Detectron2 and a compatible CUDA stack for real runs.
- Treat `timm` / `mmcv` / `pascal_voc_writer` as optional-stack notes rather than minimum runtime guarantees.
- The CPU smoke helper does not cover this branch.
- If the user asks for translation-based detection adaptation, mention the translated-source path but keep translation internals in `../translation/SKILL.md`.

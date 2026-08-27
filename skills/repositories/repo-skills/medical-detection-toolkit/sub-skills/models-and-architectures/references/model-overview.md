# Model overview

Read this reference after choosing a task and before changing architecture
settings. The model family names and result/target distinctions below are
source-backed from the repository's model modules and experiment configs; they
are not a claim that a modern environment can execute every family.

## Families

| Family | Primary behavior | Important settings | Runtime boundary |
|---|---|---|---|
| `detection_unet` | Segmentation-first detection; connected components become ROI candidates and segmentation logits are aggregated into detections | `aggregation_operation`, `n_roi_candidates`, `seg_loss_mode`, `num_seg_classes`, `detection_min_confidence` | Most suitable for portable source/API inspection; still depends on the legacy torch model API for a real forward |
| `mrcnn` | Two-stage RPN → proposal → RoIAlign → classifier/box/mask heads | proposal counts, pool/mask shapes, anchor matching, `frcnn_mode`, `return_masks_*` | Imports NMS and 2D/3D RoIAlign wrappers; exact detector execution is legacy-CUDA-unverified |
| `ufrcnn` | Two-stage detector with an auxiliary semantic-segmentation path | MRCNN settings plus `operate_stride1` and class-specific segmentation | Same custom-op boundary as MRCNN |
| `retina_net` | One-stage anchor classification and box regression | anchor scales/ratios, focal-style class loss, pre-NMS limits, confidence/NMS thresholds | Imports NMS wrappers; exact runtime remains optional/unverified |
| `retina_unet` | Retina-style detection plus a high-resolution segmentation decoder | `operate_stride1`, segmentation class settings, Retina anchor expansion | Imports NMS wrappers; exact runtime remains optional/unverified |

`DefaultConfigs` dispatches model-specific defaults from the experiment's model
label. Do not invent a new label without adding the corresponding config method
and model module, and do not assume a label mentioned in one revision exists in
another.

## Shared pipeline

The common conceptual sequence is: input batch → backbone/FPN feature maps →
anchors or proposals → class/box heads → filtering/refinement → result
records. Two-stage families additionally pool ROIs and may return masks;
Detection U-Net maps segmentation components into candidates; Retina families
predict dense anchor outputs. The data route owns how `bb_target`, `roi_labels`,
channels, and patch coordinates are formed.

## 2D versus 3D

`dim` changes spatial axes, feature strides, anchor scales, pooling/mask shapes,
box coordinate length, and memory use. A 2D box is conventionally four spatial
coordinates; a 3D box adds z extents. In 3D, z strides and z-specific anchor
scales are separate from XY values. Any custom change must be checked against
`patch_size`, `backbone_shapes`, `window`, `scale`, and the output record
consumer in [inference-and-evaluation](../../inference-and-evaluation/SKILL.md).

## What not to claim

A successful import of `backbone` or a pure box helper does not prove a model
forward. MRCNN/U-FRCNN/Retina modules import old custom operators at module
load time. Route those cases through [cuda-extensions](../../cuda-extensions/SKILL.md)
and preserve an explicit `LEGACY_CUDA_UNVERIFIED` result when the ABI is not
available.

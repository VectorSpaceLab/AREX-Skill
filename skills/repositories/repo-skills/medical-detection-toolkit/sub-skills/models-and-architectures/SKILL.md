---
name: models-and-architectures
description: "Select and reason about MedicalDetectionToolkit detector families,
  FPN/backbone settings, anchors, heads, losses, tensor shapes, and model result
  contracts while separating legacy custom-operator limits from portable source
  facts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Models and architectures

Use this route when choosing `mrcnn`, `ufrcnn`, `retina_net`, `retina_unet`, or
`detection_unet`, comparing 2D and 3D settings, interpreting model outputs, or
diagnosing shape/anchor/loss problems. Begin with the experiment configuration
route when `cf` does not yet exist, and use the CUDA route before exact
MRCNN/U-FRCNN/Retina execution.

## Workflow

1. Freeze `cf.model`, `cf.dim`, input channels, patch size, class count, and
   backbone/FPN stride assumptions. Read [model configurations](references/model-configurations.md).
2. Choose a family using [model overview](references/model-overview.md), then
   check the corresponding result dictionary and loss/target contract.
3. Validate anchors, box coordinates, padding, and Dice/segmentation helpers
   with [model utilities](references/model-utilities.md) before changing a
   network implementation.
4. If import reaches NMS or RoIAlign, stop and run the read-only diagnostic in
   [cuda-extensions](../cuda-extensions/SKILL.md). A current PyTorch CUDA
   import is not proof of this repository's historical detector path.
5. Record exact tensor shapes and whether a claim is source-backed, portable
   helper behavior, or unverified legacy runtime behavior.

## Model-family routing

- Use **Detection U-Net** when the task is segmentation-first detection using
  connected components and configurable aggregation; it is the least coupled
  model path for source/API inspection.
- Use **Mask R-CNN/U-FRCNN** for two-stage proposal/classification/mask flows;
  they require RPN, RoIAlign, and legacy custom NMS/RoIAlign in the supplied
  implementation.
- Use **RetinaNet/Retina U-Net** for one-stage anchor classification and box
  regression; Retina U-Net additionally exposes the segmentation decoder and
  stride-1 path.
- `dim=2` and `dim=3` are not interchangeable: patch axes, pyramid strides,
  anchor scales, pooling/mask shapes, output box coordinate length, and memory
  use all change. Do not infer 3D runtime support from imports alone.

## Acceptance boundary

The source modules, configuration defaults, and pure utility functions are
usable evidence for a versioned operating graph. Exact detector construction,
training, and inference are not verified on a modern stack when the custom
extension import requires removed `torch.utils.ffi`; see [troubleshooting](references/troubleshooting.md).
Do not implement a replacement model in this skill and do not substitute a CPU
forward for the old CUDA-backed path.

Read the linked references for detailed family comparisons, configuration
fields, tensor/result contracts, utility signatures, and failure recovery.

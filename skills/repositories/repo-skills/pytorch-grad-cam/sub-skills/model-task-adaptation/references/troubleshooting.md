# Model/Task Adaptation Troubleshooting

## `reshape_transform` shape errors

- Preserve batch dimension.
- Return channel-first spatial tensors, usually `B x C x H x W`.
- For ViT, remove the class token before reshaping patches.
- For Swin, do not remove a class token unless the model actually has one.
- Derive `height` and `width` from token count when unsure; `height * width`
  must equal the number of spatial tokens.

## Final transformer layer has zero gradients

If a model's classifier reads only the class token, patch tokens in the final
block may not affect the class score. Move the target layer earlier, typically
to a normalization layer before the final attention block or before the head.

## Optional dependency failures

- `ModuleNotFoundError: timm`: install `timm` only for timm/Swin model
  construction tasks.
- `ModuleNotFoundError: transformers`: install `transformers` only for CLIP or
  HuggingFace model tasks.
- Model download, authentication, or cache errors are external to `grad-cam`;
  confirm the user wants to download or has supplied a local checkpoint.

## Detection target dtype/device failures

`FasterRCNNBoxScoreTarget` expects labels and boxes that can be converted to the
model output device and boxes dtype. If `torchvision.ops.box_iou` complains,
check that requested boxes and model output boxes have compatible dtype and
shape `(N, 4)`.

## Segmentation mask failures

- The mask should be a NumPy array with the same spatial size as the output
  class map.
- The target class index should match the segmentation model's class order.
- If the model output is batched, write or wrap a target per batch member.

## Custom target does not backpropagate

- Return a scalar tensor, not a Python float detached from the graph.
- Avoid `.item()`, `.detach()`, or NumPy conversion inside the target.
- Use tensor operations on the same device as the model output.

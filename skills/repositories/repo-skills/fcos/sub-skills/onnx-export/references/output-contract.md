# FCOS ONNX Output Contract

## Input

The export script uses a dummy input tensor:

```python
torch.zeros((1, 3, 800, 1216)).to(cfg.MODEL.DEVICE)
```

The exported model contains the backbone and FCOS head. It does not include all Python post-processing as a single portable graph.

## Output names

For each FCOS FPN stride level, the export script creates three outputs. With the default five FPN levels, output names are:

```text
P3/logits
P3/bbox_reg
P3/centerness
P4/logits
P4/bbox_reg
P4/centerness
P5/logits
P5/bbox_reg
P5/centerness
P6/logits
P6/bbox_reg
P6/centerness
P7/logits
P7/bbox_reg
P7/centerness
```

The test script expects outputs ordered as all logits, then all bbox regression tensors, then all centerness tensors. It computes locations from `MODEL.FCOS.FPN_STRIDES` and applies a PyTorch `FCOSPostProcessor` equivalent.

## Consequence

If a user wants an end-to-end portable detector with NMS/post-processing inside ONNX, this repo's script is not enough by itself. It exports backbone/head tensors and relies on separate post-processing.

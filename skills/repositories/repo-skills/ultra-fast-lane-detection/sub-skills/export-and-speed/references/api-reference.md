# API Reference

## Purpose

Read this when you need the verified signatures for the model and export helpers.

## Verified signature

### `model.model.parsingNet`

```python
parsingNet(size=(288, 800), pretrained=True, backbone='50', cls_dim=(37, 10, 4), use_aux=False)
```

## Important model facts

- `parsingNet` can be instantiated without pretrained weights.
- The source uses a fixed image input shape of `1 x 3 x 288 x 800` for the TorchScript trace example.
- The class dimension must match the dataset family and backbone configuration.

## Helper expectations

### `scripts/export_torchscript.py`

- Accepts explicit repo root, checkpoint, output path, device, backbone, `griding_num`, and `num_lanes`.
- Strips `module.` prefixes from checkpoints when needed.
- Loads the model on the selected device, traces a small input tensor, and writes the TorchScript file.

### `scripts/benchmark_synthetic.py`

- Accepts explicit repo root, device, backbone, `griding_num`, `num_lanes`, warmup count, and loop count.
- Runs a tiny forward timing loop on a synthetic tensor.

## Verification note

The model tiny-forward smoke on CUDA is the strongest quick proof that the export/timing path has a compatible backend before running a larger benchmark.

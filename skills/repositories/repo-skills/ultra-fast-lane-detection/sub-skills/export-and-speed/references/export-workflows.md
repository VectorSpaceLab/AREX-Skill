# Export Workflows

## Purpose

Read this when you need to turn a trained lane model into a TorchScript file or a timing check.

## Verified source behavior

- `export.py` traces a `parsingNet` instance and saves TorchScript.
- The source script uses a checkpoint path, a chosen dataset family, and a fixed example input tensor.
- The source script loads the checkpoint with `map_location='cuda'` in its CUDA example.

## Safer export pattern

1. Pick the checkpoint file explicitly.
2. Pick the device explicitly.
3. Load the checkpoint and strip `module.` prefixes if needed.
4. Build the model with the correct `cls_dim`.
5. Trace or script the model with a tiny tensor of the correct input shape.
6. Save the TorchScript file to an explicit output path.

## Why the helper exists

The repository's original export script is a demo-style file with hardcoded paths. A bundled helper should be runnable from any directory and should not rely on the original checkout layout.

## Practical command pattern

```bash
python scripts/export_torchscript.py \
  --repo-root . \
  --checkpoint <CHECKPOINT> \
  --output <MODEL.pt> \
  --device cuda \
  --backbone 18 \
  --griding-num 200 \
  --num-lanes 4
```

## Benchmarking pattern

- Use the synthetic benchmark helper first when you only need a throughput estimate.
- Use the camera/video benchmark only when the user has a real camera or video input source.
- The synthetic benchmark should be configured with an explicit warmup count and timing loop count.

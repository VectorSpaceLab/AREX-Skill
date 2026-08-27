# Checkpoint-tool workflows

## Extract a legacy delta

1. Point the extractor at a checkpoint folder.
2. Keep only the K/V tensors and any requested optimized embeddings.
3. Review the extracted delta with the layout checker.
4. Move on to compression or inference as needed.

The bundled extractor is safer than the source helper because it does not delete the source checkpoint unless you opt in.

## Compress a delta

1. Make sure you know whether the downstream sampler expects compressed or uncompressed weights.
2. Use the compressor on a local delta and matching base model.
3. Confirm the output layout before handing it to inference.

## Compose multiple concepts

1. Start from multiple diffusers deltas plus category strings.
2. Use the regularization prompt file to anchor the concept alignment.
3. Save the composed `delta.bin` and route it back to inference.

## Handoff to inference

After extraction, compression, or composition, validate the output layout and then use the inference route. The inference route decides whether a compressed delta needs an extra sampler flag.

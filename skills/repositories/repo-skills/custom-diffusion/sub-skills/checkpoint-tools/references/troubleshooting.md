# Checkpoint-tool troubleshooting

- **Wrong checkpoint family**: the extractor expects checkpoint folders with training checkpoints, not already-composed deltas.
- **No attention K/V keys**: the source checkpoint does not contain the expected `attn2.to_k` / `attn2.to_v` tensors.
- **Embedding count mismatch**: the requested `newtoken` value is larger than the available optimized token slice.
- **Compressed delta looks wrong**: the sampler or checker should see `u`/`v` pairs for compressed K/V entries.
- **Uncompressed delta looks wrong**: the K/V entries should be tensors, not nested dicts.
- **SVD or memory failure**: reduce the workload, switch to a local fixture, or ensure the selected device has enough memory.
- **Composition category mismatch**: category ordering and path ordering must stay aligned.
- **Output path collision**: do not let compression or composition overwrite an unrelated delta file.

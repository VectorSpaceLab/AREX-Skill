# Workflows

## Sequential round-trip

1. Build a short `torch.nn.Sequential` chain from supported layers such as `Linear` and `Leaky`.
2. Use vector-shaped neuron parameters that match each layer width.
3. Trace the model with a representative `sample_data` tensor and `ignore_dims=[0]` for batched inputs.
4. Export to NIR and check the node keys, edge count, and inferred input/output shapes.
5. Import the graph and verify the output tensor shape. Unwrap `(output, state)` if the importer returns a tuple.

Expected pattern:
- input type: feature shape only, with the batch axis removed
- graph keys: `input`, `output`, and one key per traced module
- common edge pattern: `input -> 0 -> 1 -> 2 -> 3 -> output`

## Recurrent round-trip

1. Build a small model with `Linear -> RLeaky` or `Linear -> RSynaptic -> Linear`.
2. Prefer `all_to_all=False` with a vector `V` when you want the diagonal recurrent path.
3. Use vectorized `beta` / `alpha` / `threshold` tensors whose length matches the hidden width.
4. Export and confirm the recurrent block appears as an embedded NIR subgraph.
5. Import and verify the output shape from the reconstructed recurrent module.

Expected pattern:
- node keys such as `1.lif` and `1.w_rec`
- edges forming the simple cycle `lif -> w_rec -> lif`
- output shape matching the final spiking layer width

## Fixture import smoke

1. Read `references/fixtures/lif.nir`.
2. Import it with `import_from_nir`.
3. Run a `(1, 1)` input tensor through the reconstructed network.
4. Confirm the output shape is `(1, 1)` and that the call returns a state object alongside the output.

## Conv/pool compatibility check

Use this only when you need to exercise the current edge of support.

- Plain `Conv2d` graphs can round-trip when the traced shapes are compatible.
- `AvgPool2d` round-trips are safest when `kernel_size` and `stride` are tuples, not scalar ints.
- If a legacy conv/pool fixture raises a type-inference error, treat it as a compatibility reference rather than a guaranteed smoke test.

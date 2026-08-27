# Datasets Troubleshooting

## Network or cache failures

**Symptoms**
- `fetch_ucr_dataset` / `fetch_uea_dataset` hangs, times out, or raises a
  network-related error.
- A dataset name that looked plausible fails with a lookup or download error.

**Likely causes**
- No internet access or a restricted proxy.
- The dataset name is not present in the UCR/UEA catalog.
- The local cache does not already contain the requested archive.

**What to do next**
1. Run `ucr_dataset_list()` or `uea_dataset_list()` to verify the name.
2. Prefer `load_coffee`, `load_gunpoint`, `load_pig_central_venous_pressure`,
   `load_basic_motions`, or `make_cylinder_bell_funnel` when you need a
   network-free smoke test.
3. If remote fetch is required, document the cache location and the network
   assumption explicitly.

## Shape confusion

**Symptoms**
- You expected a single matrix but got train/test splits.
- A downstream preprocessing or multivariate workflow rejects the shape.

**Likely causes**
- `return_X_y=True` on a packaged loader returns train/test outputs.
- `load_basic_motions` is multivariate and returns a 3D tensor.

**What to do next**
- Inspect the shapes in `references/data-formats.md`.
- Route 3D data to `../multivariate-workflows/SKILL.md`.
- Keep the split arrays separate until the downstream workflow tells you how to
  combine them.

## Invalid dataset name

**Symptoms**
- A fetch helper rejects the dataset string immediately.

**Likely causes**
- The catalog name is misspelled or uses the wrong family.

**What to do next**
- Check `ucr_dataset_list()` / `uea_dataset_list()`.
- When you only need a quick example, use a bundled loader instead of a fetch.

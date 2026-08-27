# Multimodal Physics Troubleshooting

## Missing Dependencies

### `ModuleNotFoundError` for `einops`, `jaxtyping`, or `torchdiffeq`

- **Likely cause:** the environment does not have the extra packages required by the multimodal and ODE paths.
- **Fix:** install the missing dependency in the private inspection environment and rerun the smoke script.

## Catchment Dataset Problems

### `No .npz records found in <dir>`

- **Likely cause:** the dataset directory does not contain any site records.
- **Fix:** confirm that each site is stored as a `.npz` file with the expected keys.

### Missing `image`, `static`, or `history` keys

- **Likely cause:** the `.npz` records were built with a different schema.
- **Fix:** regenerate the records using the expected keys before pretraining.

### History windows are too short or too sparse

- **Likely cause:** the sampled window does not contain enough observed flow values.
- **Fix:** increase the history length or lower the minimum observed fraction.

## Shape And Geometry Problems

### `Image dimensions must be divisible by the patch size.`

- **Likely cause:** the patch size does not tile the image size cleanly.
- **Fix:** adjust the image crop size or the patch size before constructing the encoder.

### `fusion must be 'concat' or 'cross_attention'`

- **Likely cause:** the catchment encoder was configured with an unsupported fusion mode.
- **Fix:** choose one of the two supported values.

### `Expected params of shape (batch_size, 4)`

- **Likely cause:** the GR4 parameter head or a custom upstream module produced the wrong parameter tensor shape.
- **Fix:** ensure the catchment embedding dimension and parameter head output stay aligned with the GR4 parameter vector.

## ODE And Forcing Problems

### `No forcing attached. Call set_forcing before integrating.`

- **Likely cause:** `GR4Dynamics` was integrated before a forcing tensor and time grid were attached.
- **Fix:** call `set_forcing(forcing, times)` before integrating.

### Solver failures or unstable trajectories

- **Likely cause:** the ODE time grid is not strictly increasing or the forcing tensor has the wrong shape.
- **Fix:** validate the grid and the `(batch, time, forcing_dim)` forcing shape.

## CrossViViT Problems

### Masking or positional encoding assertions fail

- **Likely cause:** `ctx_masking_ratio`, `ts_masking_ratio`, or `pe_type` is outside the supported range.
- **Fix:** use one of the documented values and keep ratios in `[0, 1)`.

## Contrastive Pretraining Problems

### The pretraining loss does not decrease

- **Likely cause:** the batch size is too small or the embeddings are not aligned across modalities.
- **Fix:** confirm that the synthetic batch has multiple sites and that all modality tensors share the same site index.

## When To Stop And Ask

Ask the user for the exact `.npz` schema, the intended image size, or the expected forcing definition when the issue depends on data that is not visible in the local fixture.

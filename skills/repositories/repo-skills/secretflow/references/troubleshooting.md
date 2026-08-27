# SecretFlow troubleshooting

## Installation and import

### `ModuleNotFoundError` for `secretflow`
- Confirm you are using the Python 3.10 environment that has the package installed.
- Re-run `python -m pip check` in that environment.
- If the package was installed from a checkout, make sure the editable install completed successfully and that the environment has not been replaced.

### Missing runtime dependencies
Common runtime dependencies in this repo include `secretflow-spec`, `spu`, `kuscia`, `sf-sml`, `sf-heu`, `secretflow_serving_lib`, and `secretflow-dataproxy`.
If a direct import fails, check the failing module name before widening the install.

### Editable install confusion
If imports resolve to the source tree unexpectedly, confirm the environment was installed from the intended checkout and that no user-site package shadows it.

## CLI problems

### `secretflow` command not found
- The package was not installed into the active environment, or the environment's bin directory is not on PATH.
- Re-run the install check script and use the environment Python or `conda run --prefix ...` instead of a global shell Python.

### `secretflow component` fails to start
- The component CLI imports `secretflow.component.core` and its protobuf dependencies.
- Re-check `pip check` and verify `secretflow-spec`, `pyarrow`, `protobuf`, and `grpcio` are present.

## Backend and runtime issues

### GPU host present but CPU jaxlib selected
- This is acceptable for the core CPU scope.
- GPU tutorials and accelerated paths remain unverified until a CUDA-enabled JAX/Torch setup is prepared.

### Local cluster init problems
- `sf.init(..., address='local')` is the safest quick-start route.
- If you pass an explicit `cluster_config`, make sure the party names and ports match the devices you create.

### `You cannot put data to SPU directly`
- Use `PYU` as the staging device, then move the object to SPU.
- This is intentional: the runtime expects data to flow through a plain device first.

### `You cannot put data to HEU directly`
- Stage data on `PYU` first and then move it to `HEU`.

## Data and dataframe issues

### Device mismatch in federated tables
- `HDataFrame`, `VDataFrame`, and `MixDataFrame` expect all partitions to remain aligned with the owning devices.
- If a column or partition disappears, check the selection and assignment order.

### Unexpected shape or missing columns
- For vertical tables, verify the per-party column lists before fitting or joining.
- For horizontal tables, ensure the aggregator and comparator are present when required.

## Component workflow issues

### Unknown component id
- The component registry is data-driven.
- Use the component list route before constructing a component eval payload.

### `NodeEvalParam` / `DistData` / `StorageConfig` errors
- These payloads must agree on input order, output order, and component-specific metadata.
- Component export and serving workflows are especially sensitive to ordering and data ids.

## Analytics and ML issues

### Missing optional packages
- Some tutorials or tests rely on packages such as `statsmodels` or `xgboost`.
- Keep the core runtime install minimal, but add optional packages only when the selected workflow needs them.

### SPU-backed estimator errors
- Check the SPU cluster definition and party names first.
- Many models assume a multi-party environment and will fail if the SPU object was created with the wrong nodes or protocol.

## Privacy and orchestration issues

### PSI device co-location errors
- PSI workflows require the relevant inputs to be co-located as the chosen protocol expects.
- If a PSI test complains about devices not being co-located, re-check the party/device mapping.

### Kuscia task parsing failures
- The Kuscia helpers expect structured request data, allocated ports, and cluster definitions.
- Parse the JSON payload before trying to derive a SecretFlow cluster config.

### TEEU simulation memory or auth failures
- The simulation docs require substantial memory and an auth manager configuration.
- If the TEEU workflow is not the one you are actively using, leave it out of the minimum environment and treat it as advanced deployment guidance.

## When to escalate

Escalate to a narrower scope or a more specific workflow when:
- the missing dependency is only needed for an excluded workflow,
- the required backend is unavailable,
- or the workflow needs a distributed/TEE/Kuscia setup that is outside the current local scope.

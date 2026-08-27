# Troubleshooting

Use this page when imagery/raster workflows fail, are unsupported, or need a safe fallback.

## 1) Imports or package surfaces fail

**Symptom**: `arcgis` or one of the raster modules does not import.

**Likely cause**: The environment does not have the expected ArcGIS Python package set, or the optional surface is missing.

**Safe next steps**:
- Run the bundled smoke script.
- Confirm the environment matches the repository's supported ArcGIS package family.
- Keep to import/signature checks until the package surface is stable.

## 2) Raster analytics or orthomapping is not supported

**Symptom**: `arcgis.raster.analytics.is_supported(gis)` or `arcgis.raster.orthomapping.is_supported(gis)` returns false.

**Likely cause**: The target GIS does not expose the required server capability.

**Safe next steps**:
- Stop before calling server-side imagery tools.
- Tell the user that the GIS lacks the needed raster service.
- Offer only client-side reasoning, workflow planning, or a different GIS with the service enabled.

## 3) The image service or imagery layer is not usable

**Symptom**: `ImageryLayer(url, gis=...)` cannot be created, or the layer has no usable raster functions.

**Likely cause**:
- The URL is not an image service.
- The service is secured and the GIS is not authenticated.
- The layer does not publish the function names the user expected.

**Safe next steps**:
- Verify the URL points to an image service.
- Use an authenticated GIS when the service is secured.
- Inspect `layer.properties.rasterFunctionInfos` and choose only supported names.

## 4) Raster function chains do not behave as expected

**Symptom**: A chain renders incorrectly or fails during `apply`, `stretch`, `extract_band`, `band_arithmetic`, or `save`.

**Likely cause**:
- Wrong band order.
- Unsupported function name.
- Invalid raster-function parameter values.
- A visualization chain was mistaken for a persisted analysis product.

**Safe next steps**:
- Confirm the band order and the number of bands.
- Use `draw_graph()` to inspect the chain.
- Start with a small AOI or a single simple function.
- Decide whether the user wants `save(for_viz=True)` or `save(for_viz=False)`.

## 5) Output naming or job handling causes trouble

**Symptom**: The job overwrites an earlier output, or the result is not immediately available.

**Likely cause**:
- Reused `output_name`.
- The tool is asynchronous and the result is still running.

**Safe next steps**:
- Use a unique `output_name`, ideally with a timestamp suffix.
- Treat `future=True` outputs as jobs or result objects.
- For `interpolate_points`, use the returned `output_raster` property instead of assuming the call returned a ready layer.

## 6) Multidimensional or classification inputs are rejected

**Symptom**: The server tool rejects the raster or produces a partial output.

**Likely cause**:
- The raster needs multidimensional handling.
- The segmentation input is not the expected 8-bit raster.
- The tool needs a different raster type or processing template.

**Safe next steps**:
- For multidimensional inputs, prefer the multidimensional settings in `copy_raster` or the multidimensional analytics tools.
- Check whether the workflow needs a raster type, product type, or processing template.
- Confirm the source raster matches the tool's documented format expectations.

## 7) Orthomapping stops at the product stage

**Symptom**: Sensor model, control points, seamlines, orthomosaic, or DSM generation cannot proceed.

**Likely cause**:
- The image collection was not prepared with the required metadata.
- The GIS lacks orthomapping or raster analytics support.
- The workflow needs GCPs, camera info, or elevation reference data that are missing.

**Safe next steps**:
- Confirm the image collection was built from the correct inputs.
- Check that the image metadata includes the needed GPS and camera properties.
- Stop before any server-side product generation when the target GIS does not support the workflow.

## 8) No credentials are available

**Symptom**: The user asks for a workflow that would require a live image service or hosted output, but no credentials are available.

**Safe next steps**:
- Do not call service-backed tools.
- Provide only the decision path, the required prerequisites, and the verification checks.
- Route deep-learning model work to `deep-learning`, feature analysis to `features-dataframes-analysis`, and map widget tasks to `mapping-location-services`.

For a safe import-only check, use [the bundled smoke script](../scripts/raster_import_smoke.py).

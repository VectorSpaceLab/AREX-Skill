# Troubleshooting

This note focuses on the most common family-level failure patterns.

## 1) Shape mismatch or name mismatch

### Symptoms
- `infer_shape` fails
- bind fails in `detection_train.py` or `detection_test.py`
- the loader provides a name that the symbol does not declare
- a terminal output is present but the metric cannot find it

### Likely causes
- config `data_name` / `label_name` does not match `X.var(...)`
- class count changed but bbox or mask output width did not
- ROI or pyramid stride settings no longer match the feature map layout
- branch count changed without updating the downstream reshape logic

### Fixes
- inspect `sym.list_arguments()` and `sym.list_outputs()`
- compare loader names with symbol input names
- re-run `sym.infer_shape(**worker_data_shape)` before checkpoint loading
- when class count changes, update bbox and mask channel counts together

## 2) Missing `mxnext` / TVM / custom-op helpers

### Symptoms
- import errors for `mxnext.tvm.*`
- `mx.sym.Custom` op type not found
- symbol build works in one environment but not another

### Likely causes
- the runtime environment lacks the compiled `mxnext` helper package
- the file that registers the operator was not imported before symbol build
- the environment does not expose the backend op that the code expects

### Fixes
- import the module containing `@mx.operator.register(...)` before graph
  construction
- confirm the helper path is available in the runtime environment
- fall back to a config that does not require that backend path if one exists
- do not assume backend support just because the source parses

## 3) Custom operator registration problems

### Symptoms
- `CustomOp` registration fails
- the graph compiles in one family but not another
- an operator works in training but not in test

### Likely causes
- `@mx.operator.register('...')` never ran
- `op_type` in `mx.sym.Custom(...)` does not match the registered name
- `infer_shape()` returns a shape that differs from the graph call site

### Fixes
- verify module import order
- verify exact operator names and argument lists
- check `list_arguments()` / `list_outputs()` against the symbol call
- keep forward-only and training-time operators separate when possible

## 4) Class-aware bbox dimensions

### Symptoms
- bbox decode errors
- proposal target errors
- checkpoints load but inference output is malformed

### Likely causes
- `class_agnostic` was changed without updating regression width
- `num_reg_class` does not match the configured class count
- test post-processing still assumes background-stripped layout

### Fixes
- remember: per-class regression usually uses `4 * num_class`
- class-agnostic regression often uses `4 * 2`
- update both target generation and decode helpers
- check whether the family strips background scores before NMS

## 5) Mask polygon resolution or mask ROI mismatch

### Symptoms
- `gt_poly` shape mismatch
- mask target reshape failure
- mask prediction works but output is obviously misaligned

### Likely causes
- `EncodeGtPoly` / dataset preprocessing does not match mask branch shape
- `MaskParam.resolution` and `MaskRoiParam.out_size` were changed separately
- the number of foreground proposals used for masks is different from the slice
  in the mask head

### Fixes
- keep polygon encoding, mask resolution, and mask ROI size in sync
- confirm that the mask branch only consumes foreground proposals
- re-check the mask output order in the family test script

## 6) DCN, FP16, or backend issues

### Symptoms
- deformable convolution import or runtime failure
- FP16 overflow or unstable gradients
- NaNs appear after BN or custom conv blocks

### Likely causes
- backend lacks `mx.sym.contrib.DeformableConvolution`
- FP16 graph still feeds a sensitive head in half precision
- BN mode or epsilon differs from the expected family config

### Fixes
- verify the backend build before using DCN configs
- use the family’s own fp16 / fp32 toggles, not a blanket toggle
- keep the explicit `X.to_fp32(...)` conversions used by the family
- if the environment cannot support the custom op, switch to a non-DCN family

## 7) Stale checkpoints

### Symptoms
- parameter loading complains about missing or extra names
- the graph loads but weights do not fit new heads
- a multi-stage family loads only the first stage cleanly

### Likely causes
- architecture changed after the checkpoint was created
- stage-specific names changed in Cascade or DoublePred-style models
- anchors were cached with a different shape

### Fixes
- use the closest matching pretrained checkpoint
- set `from_scratch = True` when the topology changed materially
- update `fixed_param` / `excluded_param` if the backbone or head changed
- re-run `process_weight()` whenever cached anchors or similar parameters
  depend on config values

## 8) Family-specific reminders

- **FCOS**: `throwout_param` must exist before the head is constructed.
- **TSD**: the external `shape_tool` dependency must be available.
- **CrowdHuman**: ignore labels are part of the target contract; do not treat
  them as ordinary background.
- **Trident**: branch processing depends on `valid_ranges` and branch count.
- **Mask / Mask Scoring**: output order is test-script specific.
- **FreeAnchor**: pre-anchor top-N logic and decoded box helpers must align.

## 9) Debug sequence that usually works

1. Print config summary.
2. Inspect symbolic input and output names.
3. Run `infer_shape` with loader-provided shapes.
4. Check custom-op imports.
5. Revisit class count, anchor topology, and ROI topology.
6. Only then touch checkpoints or backend settings.

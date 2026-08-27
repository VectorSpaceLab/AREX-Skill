# Cross-cutting troubleshooting

Read this when a leaf route reports an install, import, path, or compatibility
failure that spans more than one workflow.

| Symptom | Likely cause | Next action |
|---|---|---|
| `pip` tries to resolve `torch==0.4.1` or fails on old NumPy/SciPy pins | The source requirements are a historical Python 3.6 environment recipe | Decide whether exact reproduction is required. If yes, locate matching historical artifacts/toolchain; if no, use a modern isolated inspection environment only for portable APIs and record unverified detector behavior. |
| `torch.utils.ffi` is missing | Modern PyTorch removed the legacy FFI API required by checked-in NMS/RoIAlign wrappers | Route to `cuda-extensions`; do not monkey-patch imports or call the CPU branch as proof of exact detector support. |
| A `.so` exists but import or execution fails | Binary was built for a different torch ABI, CUDA/toolkit, or GPU architecture | Ignore presence as proof. Run the read-only compatibility checker and rebuild only as a separately reviewed modernization task. |
| Loader import fails in `SingleThreadedAugmenter` or transform symbols | `batchgenerators` version drift | Compare the loader contract with the version selected for the checkout. Do not change only one transform import without checking train/test pipelines. |
| `configs`, `model`, or `data_loader` cannot be imported | The legacy workflow dynamically loads modules relative to the experiment source | Check that the experiment source is a real module directory and that its config/data-loader/model paths are coherent; do not add arbitrary global `sys.path` entries. |
| No data is found under `root_dir` or `input_df_name` | Example configs contain machine-specific dataset roots | Replace with an approved preprocessed-data root and validate the manifest/array contract using the data leaf. Never guess a clinical dataset path. |
| Shapes or boxes are wrong after augmentation | Image and segmentation were transformed with different geometry or axes | Recheck `(x,y)` vs `(x,y,z)`, channel-first layout, segmentation interpolation order, patch coordinates, and ROI label alignment before changing model settings. |
| Training/testing would overwrite source or experiment files | `prep_exp` snapshots and reloads mutable legacy modules | Use a disposable copied experiment directory, preserve the original, and stop if the snapshot is incomplete or paths are ambiguous. |
| WBC returns empty/overmerged detections | Invalid box schema, confidence/IoU threshold, overlap metadata, or wrong 2D/3D mode | Validate raw records first, preserve them, then change one threshold while checking class and coordinate dimensionality. |
| AUC/PRC or patient metrics fail | The input dataframe lacks both classes or required columns | Inspect evaluation records and class targets; do not fabricate negatives or interpret a single-class score. |
| Plotting fails on a headless host | Matplotlib backend/display configuration | Select a non-interactive backend and write files to a disposable output directory; plotting success does not validate detector accuracy. |
| GPU allocation fails with out-of-memory | Selected device is already occupied or model/patch shape is too large | Choose an approved free device, reduce a bounded smoke tensor/patch, and do not infer custom-op incompatibility from unrelated allocation pressure. |

Stop and report an unresolved limitation when it requires a private dataset,
credentials, network acquisition, destructive cleanup, a missing historical
binary/toolchain, or unsupported CUDA ABI. The graph is not a substitute for
modernizing this unmaintained framework.

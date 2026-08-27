# pointnet2 root troubleshooting

This file covers failures that cut across the PointNet2 workflow sub-skills. After the shared diagnosis, route to the owning sub-skill for workflow-specific commands and validators.

## Quick triage

```bash
python scripts/check_pointnet2_env.py --repo-root /path/to/pointnet2
python scripts/check_pointnet2_env.py --repo-root /path/to/pointnet2 --require tf1
python sub-skills/model-apis-and-custom-ops/scripts/inspect_custom_ops.py --repo-root /path/to/pointnet2 --require tensorflow
```

Use `--require custom-ops --try-load-custom-ops` only when the TensorFlow custom-op `.so` files are expected to exist and ABI load errors are acceptable diagnostics.

## Cross-cutting failures

| Symptom | Likely cause | Recovery | Route next |
|---|---|---|---|
| `SyntaxError` from Python-2-style `print`, `TabError`, `xrange` errors, or inconsistent behavior between scripts | The upstream repo is Python-2-era; several original trainers/loaders are not clean Python 3 entry points. | Use a Python 2.7 + TensorFlow 1.x environment for native source execution, or use the generated Python 3-compatible validators/command builders for planning and data checks. Do not patch source files silently unless the user asks for a port. | Workflow owner for the script; shared APIs in [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) if TensorFlow model code is involved. |
| `AttributeError: module 'tensorflow' has no attribute 'contrib'`, TF2 eager/compat errors, or `tf.Session`/`tf.get_variable` failures | The model code expects TensorFlow 1.x APIs and `tf.contrib`. | Use TensorFlow 1.x. A TF2 install may import successfully but is not equivalent. Check with `scripts/check_pointnet2_env.py --repo-root /path/to/pointnet2 --require tf1`. | [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) for TF1 baseline and API guidance. |
| `ImportError` or `NotFoundError` for `tf_sampling_so.so`, `tf_grouping_so.so`, or `tf_interpolate_so.so` | PointNet++ Python wrappers call `tf.load_op_library` for custom TensorFlow ops; missing files or ABI mismatch blocks PointNet++ graph construction. | Run the custom-op inspector. Confirm the `.so` file exists, TensorFlow version/ABI matches the compiler flags, and CUDA/nvcc are compatible. Treat CPU baseline checks as separate from PointNet++ readiness. | [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) custom-op reference. |
| `nvcc: command not found`, CUDA path errors, or C++ ABI compile failures | Original compile scripts are CUDA-8/TF1-era recipes with hard-coded include/library assumptions. Modern GPU visibility alone does not prove build readiness. | Install or select a matching legacy CUDA/nvcc stack; update `nvcc`, TensorFlow include/lib paths, and `_GLIBCXX_USE_CXX11_ABI` flags according to the active TensorFlow build. Keep full PointNet++ native execution unverified until an op load check passes. | [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/). |
| Data starts downloading during a simple import | `modelnet_h5_dataset.py` has a top-level download side effect when `data/modelnet40_ply_hdf5_2048/` is missing. | Avoid naive loader imports for inspection. Validate the dataset folder first with the ModelNet validator, or create/populate the expected folder intentionally before importing the original loader. | [classification-workflows](../sub-skills/classification-workflows/) data reference and validator. |
| Missing ModelNet40, ShapeNetPart, or ScanNet files | The datasets are external and each workflow has a different layout. | Use the bundled validator for the selected dataset. Do not reuse ShapeNetPart checks for ScanNet or vice versa. | [classification-workflows](../sub-skills/classification-workflows/), [part-segmentation-workflows](../sub-skills/part-segmentation-workflows/), or [scannet-semantic-scene-workflows](../sub-skills/scannet-semantic-scene-workflows/). |
| ShapeNetPart plus ScanNet data prep in one request becomes confusing | Both workflows are point-cloud segmentation tasks, but their schemas and labels are unrelated. | Run the ShapeNetPart validator for `synsetoffset2category.txt`, split JSON, and category folders; run the ScanNet validator for pickle/raw scene prerequisites and label TSV columns. Share only the backend notes. | [part-segmentation-workflows](../sub-skills/part-segmentation-workflows/) and [scannet-semantic-scene-workflows](../sub-skills/scannet-semantic-scene-workflows/). |
| Missing `eulerangles`, `plyfile`, `scikit-learn`, `cv2`, or renderer dependency | Geometry utilities and visualization helpers have optional scientific/GUI dependencies beyond TensorFlow. | Install the missing package when the workflow needs it, or use the geometry smoke to separate missing dependency from malformed point-cloud data. Avoid importing `show3d_balls.py` blindly in headless environments because it loads the renderer and opens GUI state. | [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) utilities reference. |
| `render_balls_so` missing or visualization window fails | `show3d_balls.py` requires a compiled renderer library and an environment capable of GUI/OpenCV display. | Use the bundled renderer compile helper with `--dry-run` first. In headless sessions, skip GUI visualization or render through a controlled noninteractive path. | [model-apis-and-custom-ops](../sub-skills/model-apis-and-custom-ops/) renderer section. |
| Checkpoint restore or evaluation command fails before data/model setup | Legacy train/eval scripts assume exact checkpoint prefixes, log/dump directories, data roots, and model import paths. | Use the command builder for the workflow, then verify data layout and backend readiness before running the original trainer/evaluator. | Owning workflow sub-skill. |

## Backend claim rule

A later agent may claim these levels only when the corresponding checks pass:

- **Data/layout planning**: relevant validator passes on the user's dataset or a deliberate fixture.
- **CPU/API smoke**: TensorFlow 1.x imports and the targeted CPU-safe smoke passes.
- **PointNet++ native execution**: TensorFlow 1.x imports, custom-op `.so` files exist, `tf.load_op_library` succeeds for the required ops, and the workflow's dataset/checkpoint/GPU prerequisites are satisfied.

If any layer is missing, report the exact blocked layer and continue with the highest verified level rather than upgrading the claim.

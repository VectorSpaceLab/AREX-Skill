# Install and Compatibility Notes

## Purpose

Read this before preparing a 3DDFA runtime, choosing CPU/GPU mode, or deciding whether a failure is an install issue versus a workflow issue.

## Repository Shape

3DDFA is a legacy script-oriented Python repository, not a modern installable package with root `pyproject.toml` or root `setup.py`. Most native workflows expect to run from a 3DDFA checkout with source modules importable from the checkout root.

Important runtime resources relative to a checkout:

| Resource | Required for |
|---|---|
| `models/phase1_wpdc_vdc.pth.tar` | Default MobileNet-V1 inference checkpoint. |
| `train.configs/*.npy` and `train.configs/*.pkl` | Landmark/dense reconstruction, whitening, PAF, PNCC. |
| `visualize/tri.mat` | Mesh triangles for PLY/OBJ/depth/PNCC. |
| `models/shape_predictor_68_face_landmarks.dat` | Default dlib landmark initialization; not bundled in the small checkout. |
| `utils/cython/mesh_core_cython*.so` or platform equivalent | Cython-accelerated depth/PNCC/render path. |
| `test.data/` and training image archives | Benchmarks and training; external downloads. |
| `c++/weights/mb_1.onnx` and `tiny-yolo-azface-fddb_82000.weights` | Optional C++ OpenCV DNN demo; external downloads. |

## Python Dependencies

The documented legacy requirements include PyTorch, torchvision, NumPy, SciPy, Matplotlib, OpenCV, Cython, and dlib. Modern versions can run the safe architecture/geometry smokes, but native scripts may expose legacy assumptions.

Recommended staged setup:

1. Install PyTorch/torchvision for the intended CPU or CUDA backend.
2. Install NumPy, SciPy, Matplotlib, OpenCV Python, and Cython.
3. Only install dlib when the workflow requires the unmodified image/video CLI or the dlib detector/landmark path.
4. Build the Cython mesh core only when depth, PNCC, render imports, or unmodified native CLI startup require it.
5. Add external model/data files deliberately; do not hide downloads inside diagnostics.

## Backend Matrix

| Capability | Backend/dependency | CPU substitute | Notes |
|---|---|---|---|
| MobileNet forward shape smoke | PyTorch CPU or CUDA | full | CPU validates architecture/import but not native GPU throughput. |
| Bbox-driven image inference | CPU or CUDA PyTorch plus Python `dlib` import and render import availability | full for CPU behavior | The flags can avoid dlib detector/predictor model, but not the top-level `dlib` import in the unmodified CLI. |
| Default dlib detector/landmark inference | Python `dlib` plus external shape predictor | partial | Needed for unknown images without bbox sidecars. |
| Depth and PNCC | Cython mesh core extension | partial | Build extension for the active Python ABI. |
| Training and benchmark parameter extraction | CUDA-centric native scripts | none for full training speed/path | `train.py` calls CUDA APIs directly. CPU can import losses but does not validate native training. |
| AFLW/AFLW2000 benchmark metrics from existing params | NumPy + config arrays | full for metric computation | Full extraction still needs images and usually CUDA. |
| C++ OpenCV DNN demo | CMake, compiler, OpenCV >=4.2, ONNX/Yolo weights | partial | Build/run is a system dependency workflow. |

## Modern Python Caveats

- `dlib==19.5.0` from the old requirements is often hard to build on modern Python. A compatible newer dlib may be more practical, but verify native behavior after changing versions.
- PAF code uses deprecated NumPy aliases such as `np.int`; NumPy 1.24+ can fail if `--dump_paf=true`.
- The Cython extension filename is Python-version and platform-specific; rebuild it after changing Python versions.
- OpenCV GUI calls and Matplotlib display can fail in headless environments. Disable display flags or wrap GUI code before automation.
- The checkpoint loader strips a leading `module.` prefix from DataParallel-trained weights; keep architecture and `num_classes=62` aligned with the checkpoint.

## Safe Diagnostic Order

From this skill root:

```bash
python scripts/check_3ddfa_environment.py --repo-root /path/to/3DDFA
```

Then route to sub-skill scripts for focused checks:

```bash
python sub-skills/python-inference/scripts/smoke_mobilenet_forward.py --repo-root /path/to/3DDFA
python sub-skills/geometry-rendering/scripts/smoke_geometry.py --repo-root /path/to/3DDFA
python sub-skills/training-evaluation/scripts/validate_training_args.py --repo-root /path/to/3DDFA --train-script train.py
```

These checks avoid native inference, training, downloads, benchmarks, and C++ builds unless you explicitly run those workflows afterwards.

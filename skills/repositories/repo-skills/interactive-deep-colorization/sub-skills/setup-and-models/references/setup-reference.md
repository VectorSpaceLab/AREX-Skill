# Setup Reference

## Purpose

Read this when deciding how to prepare an environment for Interactive Deep Colorization. The repository is a script-style research checkout, not an installable Python distribution, so setup is about satisfying imports, model files, UI/display requirements, and backend-specific runtime dependencies.

## Backend decision table

| Backend path | Best for | Core requirements | Notes |
| --- | --- | --- | --- |
| Caffe root GUI/notebook | Official SIGGRAPH local-hints model and Caffe-only notebook workflows | PyCaffe built with Python layer support, Caffe runtime, model `.caffemodel` files, image/scientific Python stack, PyQt4 for GUI | Required for global histogram transfer. Hardest path on modern Python because PyCaffe/PyQt4 are legacy. |
| PyTorch root GUI | Local-hints GUI with converted PyTorch weights | PyTorch, image/scientific Python stack, PyQt4 GUI stack, `models/pytorch/caffemodel.pth` | Avoids PyCaffe for local hints, but the root GUI still imports PyQt4/qdarkstyle at module import time. |
| Docker/PyQt5 path | Running the app through the repository's Docker variant, especially on macOS/XQuartz-style display forwarding | Docker build, display server forwarding, PyTorch model weight inside Docker context | Docker entry script defaults to `--backend pytorch` and uses PyQt5 instead of PyQt4. |
| Source/API inspection | Understanding helper APIs, CLI defaults, tensor shapes, or model architecture without GUI/weights | NumPy, SciPy, scikit-image, scikit-learn, OpenCV, PyTorch | Sufficient for many agent reasoning and troubleshooting tasks; not proof of full GUI/model inference. |

## Dependency surfaces from repository evidence

The README and install scripts name these runtime surfaces:

- Linux or macOS host for the original non-Docker path.
- Caffe or PyTorch backend.
- CPU or NVIDIA GPU/CUDA/CuDNN for the deep model backend; GPU is useful but not always mandatory for source inspection.
- OpenCV, scikit-learn, scikit-image, SciPy/NumPy, and Matplotlib-style notebook support.
- PyQt4 plus QDarkStyle for the root GUI script.
- PyQt5 for the Docker entry script.
- Downloaded model artifacts under `models/` before real inference.

Legacy install scripts use commands such as `sudo pip install`, `apt-get`, and old Conda channels. Treat those scripts as historical evidence and not as safe copy-paste automation for a user's machine.

## Backend-specific notes

### Caffe

Caffe support in this repository expects PyCaffe. The README specifically says Caffe should be compiled with Python layer support and the PyCaffe path added to `PYTHONPATH`. The Caffe classes also load custom colorization prototxts and set model parameters such as in-gamut cluster centers or bilinear upsampling kernels.

Use Caffe when the task requires:

- official model parity with the SIGGRAPH 2017 release;
- the barebones Caffe notebook;
- global histogram transfer;
- the global stats network and `caffe.io` image helpers.

### PyTorch

The PyTorch path uses `models/pytorch/model.py` and `data.colorize_image.ColorizeImageTorch` / `ColorizeImageTorchDist`. It still needs a weight file, typically `models/pytorch/caffemodel.pth`, before real inference. Source-level architecture inspection can instantiate `SIGGRAPHGenerator`, but real colorization should use trained weights.

### Qt and display

The root GUI imports PyQt4 and qdarkstyle at module top level, so even `--help` style execution may fail before parsing if those packages are missing. Use the local-hints sub-skill's CLI inspector when you only need parser facts.

GUI execution also needs a display server. In headless or remote sessions, prefer static checks, notebook/API guidance, or Docker display-forwarding only when the host is configured for it.

## Safe setup workflow

1. Pick Caffe, PyTorch, or Docker based on the requested workflow.
2. Use [model-artifacts.md](model-artifacts.md) and [../scripts/check_model_artifacts.py](../scripts/check_model_artifacts.py) to check expected weight files.
3. Verify the scientific image stack with a small import check before launching a GUI.
4. Verify backend-specific imports separately:
   - Caffe: `import caffe` plus access to required prototxt/model files.
   - PyTorch: `import torch`; optionally verify CUDA if GPU use is required.
   - Qt: `from PyQt4.QtGui import QApplication` for the root script, or PyQt5 for Docker-derived code.
5. Launch only the workflow that matches the prepared backend.

## What this generated skill verified

Construction verified source imports, helper signatures, Lab/gamut behavior, PyTorch architecture tiny forwards, and optional torch CUDA visibility. It did not verify PyCaffe, PyQt GUI launch, Docker build, network downloads, or downloaded model-weight inference.

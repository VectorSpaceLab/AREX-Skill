# Setup Troubleshooting

## Purpose

Use this reference when setup, backend imports, model artifacts, display configuration, or legacy dependency choices block Interactive Deep Colorization.

## Fast triage

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `No module named caffe` | PyCaffe is not installed or not on `PYTHONPATH` | Use Caffe only when required. For local hints, consider PyTorch if available. For global histogram transfer, install PyCaffe with Python layer support. |
| Caffe complains about Python layers | Caffe was built without Python layer support | Rebuild/configure Caffe with Python layer support before using Caffe workflows. |
| `No module named PyQt4` before `--help` output | Root GUI imports PyQt4 at module import time | Use the local-hints CLI inspector for parser facts; install PyQt4 only when actually launching the root GUI. |
| GUI starts but no window appears | Headless/remote host or display permissions | Use notebook/API route, configure a display server, or use Docker display forwarding intentionally. |
| `FileNotFoundError` / Caffe file-open error for a model path | Required weight file missing | Read [model-artifacts.md](model-artifacts.md) and run [../scripts/check_model_artifacts.py](../scripts/check_model_artifacts.py). |
| `--backend pytorch` still fails in GUI | PyQt import happens before backend selection, or PyTorch weight file is missing | Verify Qt import separately from PyTorch/model artifact validation. |
| User expects training code | Training is not in this checkout | State that the README routes local-hints training to an external PyTorch reimplementation. |
| Docker container cannot display GUI | Display forwarding is not configured for the host | Read [docker-reference.md](docker-reference.md); verify display permissions and environment variables. |

## Missing model files

Run the bundled checker before debugging backend internals:

```bash
python sub-skills/setup-and-models/scripts/check_model_artifacts.py --repo-root /path/to/checkout
```

Use `--workflow pytorch-local`, `--workflow caffe-local`, or `--workflow global-histogram` to focus on a specific route. A missing weight file is not fixed by installing Python packages.

## Caffe versus PyTorch confusion

The root README names Caffe as the official model path and PyTorch as a converted backend. Global histogram transfer is Caffe-only in this checkout. If a user asks for global histogram transfer in PyTorch, explain that the repository does not provide that implementation and route them to the Caffe/global sub-skill.

## Legacy dependency risk

The repository's install snippets are historical. They use old package names and channels such as PyQt4, old OpenCV, and `sudo pip`. On modern systems, install packages deliberately instead of replaying every historical command.

## What counts as verified

- Source import/signature checks prove helper facts and API shapes.
- PyTorch architecture smokes without weights prove code can instantiate and run with random parameters, not that the trained model is correct.
- Caffe import success proves PyCaffe availability, not that all prototxt/weight files are staged.
- GUI import success proves Qt bindings exist, not that a display is reachable.
- Docker build success proves the image built, not that GUI display forwarding is correct.

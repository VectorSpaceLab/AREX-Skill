# Setup and Build Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `externally-managed-environment` from pip | System Python is protected | Create/activate a conda or venv and rerun install there. |
| Python version unsupported | Python outside 3.10-3.14 | Create a compatible env before installing. |
| CMake too old or missing | Host lacks CMake >=3.24 | Install CMake inside the active env or through the approved system package manager. |
| `CMakeLists.txt not found` in a third-party path | Required submodule not initialized | Synchronize and initialize submodules needed by the selected backend; avoid fetching every backend unless required. |
| Missing `Python.h` on Linux | Python dev headers missing for the selected interpreter | Install the matching `python3.X-dev` package or use a conda Python with headers. |
| Build succeeds but runtime cannot find operators | Static registration library pruned by linker | Link registration libraries with force-load/whole-archive flags. |
| PyTorch or torchao version conflicts | Mixed package indexes or inherited environment | Use a fresh env or the pinned PyTorch install mode; verify `import torch`, `import torchao`, and `pip check`. |
| `conda env list` permission errors | Conda plugin/path issue | Try `CONDA_NO_PLUGINS=true conda env list` or inspect the env directory directly. |
| Full source build too slow | Building C++ pybindings/backends not needed | Use a minimal package/export inspection path if runtime pybindings or backend libraries are not required. |


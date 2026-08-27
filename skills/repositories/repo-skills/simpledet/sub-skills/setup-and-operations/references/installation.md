# Installation and extension contract

## When to read

Read this before creating or repairing an environment. Commands below are
recipes, not proof that a modern host can run this 2021-era checkout.

## Documented dependency matrix

| Surface | Repository evidence | Operational implication |
|---|---|---|
| Python | README and INSTALL document Python 3.5+/3.7 | Prefer an isolated Python 3.7 environment for the documented stack. |
| MXNet | custom CUDA 9/10/10.1 wheels, source build instructions | Match wheel CUDA runtime to driver/toolkit; current MXNet is not automatically compatible. |
| `mxnext` | separate Git package described as symbolic API wrapper | Install a revision compatible with this SimpleDet commit; it is not vendored here. |
| COCO | patched `cocoapi` Python package | Required by COCO conversion and evaluation. |
| image/data | OpenCV, NumPy, `pytz`, optional Pillow/matplotlib | OpenCV reads BGR images; transforms convert to RGB and normalize. |
| extensions | Cython CPU bbox/NMS plus CUDA gpu_nms | `make` invokes the CUDA-aware setup script and needs `nvcc`. |

The repository has no `setup.py`, `pyproject.toml`, requirements lockfile, or
console entry point. Do not use `pip install -e` as if SimpleDet were a normal
package; execute its scripts from a compatible checkout root.

## Safe preparation order

1. Create a new private environment; never mutate the Python running the agent.
2. Install the repository-documented Python version and NumPy/Cython versions.
3. Install a matching MXNet CUDA wheel or complete the documented source build.
4. Install compatible `mxnext` and patched `pycocotools`.
5. Install OpenCV and `pytz`; add `mxboard`/TensorBoard only for logging.
6. Run the bundled read-only diagnostic.
7. Build extensions only after the compiler/toolkit decision is explicit.
8. Import a small config or run a safe parser/help check before training.

Do not download datasets, pretrained weights, or a model during environment
preparation. Those are separate, user-authorized side effects.

## CUDA and extension decisions

The public docs target CUDA 9.0, 10.0, or 10.1 and old GPU generations; the
source build lists explicit architectures. An A100 or newer host is not
automatically covered by those artifacts. Check the NVIDIA driver, toolkit,
`nvcc`, MXNet's `context.num_gpus()`, and a one-element device allocation.

The standard Cython setup imports `locate_cuda()` before building any extension.
If `nvcc` is absent, it fails before CPU extensions are built. A safe CPU-only
inspection can compile `bbox.pyx`, `bbox_self.pyx`, and `cpu_nms.pyx` with a
small local build adaptation, but that does not validate CUDA execution or
`gpu_nms`.

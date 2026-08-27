# Installation and Compatibility

Det3D's source documentation targets Linux, Python 3.6+, PyTorch 1.1-1.6,
CUDA 10.0/10.1, CMake 3.13.2+, a specific historical `spconv`, and a compatible
nuScenes devkit. It reports testing on Ubuntu 16.04/18.04 with Python 3.6.5,
PyTorch 1.1, CUDA 10.0, and cuDNN 7.5. These are historical constraints, not a
promise that modern Python/torch builds are source-compatible.

Install order:

1. Choose an isolated Python/torch/CUDA environment with a known compatibility
   matrix and verify a CUDA tensor operation.
2. Ensure a matching CUDA toolkit (`nvcc`) and C++ compiler are present when
   building extensions; the framework runtime libraries alone are insufficient.
3. Build/install the compatible `spconv` variant.
4. Install only dataset SDKs and visualization packages needed by the selected
   workflow.
5. Build Det3D's extensions against the same torch/toolkit, then verify imports.

Legacy documentation mentions pinning setuptools, Pillow, torch, and torchvision
for old dependency failures. Treat those pins as environment-specific recovery,
not universal install advice, and never downgrade a shared environment silently.

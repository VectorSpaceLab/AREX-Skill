# Det3D Compatibility and Install Contract

The repository is an old PyTorch codebase with custom CUDA extensions and sparse
convolution dependencies. Its installation document names Linux, Python 3.6+,
PyTorch 1.1–1.6, CUDA 10.0/10.1, CMake >=3.13.2, a specific historical
`spconv`, and `nuscenes-devkit`; tested examples are Ubuntu 16.04/18.04,
Python 3.6.5, PyTorch 1.1, CUDA 10.0, and cuDNN 7.5.

Use a private environment and validate the complete tuple:

1. Python and torch wheel compatibility.
2. Driver and CUDA runtime visibility.
3. CUDA toolkit/compiler (`nvcc`) and host compiler for source builds.
4. `spconv` variant and ABI compatibility.
5. Det3D extension build outputs and imports.
6. Dataset SDK versions and data schema.

A framework CUDA smoke can pass while `det3d.core` or model imports fail because
package initializers eagerly import `spconv`-dependent modules. Record those as
backend/dependency blocks, not as config errors. Modern inspection environments
are useful for source/API facts but do not establish historical benchmark parity.

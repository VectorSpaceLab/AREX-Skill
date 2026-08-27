# Internals and Compatibility Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| C++ compile error involving `input.type()` or `AT_DISPATCH` | Legacy extension code against a newer PyTorch C++ API. | Use an older compatible PyTorch stack or update extension code to modern `scalar_type()` / `data_ptr()` patterns. |
| `cpu/vision.h` not found during PEP 660 editable build | Temporary editable build path changes relative include resolution. | Use legacy `setup.py build develop` for investigation or patch include directories/build config. |
| `libc10.so` missing | Extension shared library dependencies are not loaded. | Import `torch` first; verify the same environment that built the extension is used. |
| `torch._six.PY3` missing | PyTorch removed old compatibility surface. | Patch imports deliberately or use an older torch version; do not hide this in public workflow claims. |
| `_download_url_to_file` import fails | Download helper moved/changed across PyTorch versions. | Patch model-zoo utility or use a compatible torch release. |
| NumPy 2 warning with old torch/torchvision | ABI mismatch. | Pin `numpy<2` for old torch wheels. |
| Deformable conv unavailable | Config requires CUDA/deformable extension but build did not include it. | Rebuild with compatible CUDA/NVCC or select a non-DCN config. |

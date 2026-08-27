# Setup troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No such file or directory` for `mxnet` or `mxnext` | Wrong environment or missing separate dependency | Run the diagnostic with the intended Python; install the exact legacy-compatible variants. |
| `mx.gpu` exists but device allocation fails | CPU MXNet build, incompatible CUDA wheel, driver/toolkit mismatch, or unsupported GPU architecture | Check `num_gpus()`, driver/toolkit, wheel tag, and one-element allocation. Do not use CPU as a GPU substitute. |
| `nvcc binary could not be located` from Cython setup | Makefile's CUDA extension path is active | Install/activate a compatible toolkit or perform a documented CPU-only adaptation; mark `gpu_nms` unverified. |
| Cython import `operator_py.cython.bbox` fails | Extensions were not built or are on another Python path | Build CPU extensions in the checkout and verify the generated module with the same interpreter. |
| `ImportError` for `mxnext.tvm.*` or custom operator | mxnext revision/backend mismatch | Compare the config's model family and required mxnext operators; use a compatible revision rather than removing the operator. |
| OpenCV cannot read an image | Bad `image_url`, missing system library, or headless GUI path | Validate the file and use non-GUI transforms; do not debug with `imshow` on a headless host. |
| TensorBoard log is empty | Metrics were not constructed with a SummaryWriter or wrong logdir | Check config metric construction and log directory; TensorBoard is optional. |
| Cluster hangs or kills unrelated processes | Private launcher assumptions or unsafe cleanup | Stop; use a reviewed launcher, one-node smoke, hostfile, shared paths, and explicit process ownership. |

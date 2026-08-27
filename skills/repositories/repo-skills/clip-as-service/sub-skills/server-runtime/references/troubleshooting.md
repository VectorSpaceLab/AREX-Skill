# Server Runtime Troubleshooting

## Backend import failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `No module named 'onnxruntime'` | ONNX extra missing. | Install `clip-server[onnx]`; rerun `scripts/check_install.py --server-only --check-onnx`. |
| `TensorRT is not yet installed` | TensorRT Python/runtime missing. | Install NVIDIA TensorRT according to the host CUDA stack, then install `clip-server[tensorrt]`. Verify with `--check-tensorrt`. |
| `can not perform inference on cpu with Nvidia TensorRT` | TensorRT executor was configured with CPU. | Use `device: cuda`; if CUDA/TensorRT is unavailable, switch runtime to PyTorch/ONNX and do not claim TensorRT coverage. |
| `CUDA/GPU is not available on Pytorch` | TensorRT path requires CUDA-visible PyTorch. | Check `nvidia-smi`, torch CUDA availability, driver/wheel compatibility, and container GPU flags. |
| `No module named 'transformers'` | M-CLIP selected without optional transformers dependency. | Install `clip-server[transformers]` or choose an OpenCLIP model. |
| `No module named 'cn_clip'` | CN-CLIP selected without optional dependency. | Install `clip-server[cn_clip]` or choose a supported OpenCLIP/M-CLIP model. |

## YAML and CLI issues

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Extra CLI flags are ignored or fail | `python -m clip_server` accepts only a Flow YAML path or `-i`. | Move settings into YAML under Flow or executor fields. |
| Packaged `onnx-flow.yml` is not found | Package resources are unavailable or the wrong Python environment is used. | Verify `clip_server` import in the same environment; copy the bundled skill template and pass its path explicitly. |
| Executor import fails when Flow starts | `metas.py_modules` points to the wrong runtime module. | Use `clip_server.executors.clip_torch`, `clip_server.executors.clip_onnx`, or `clip_server.executors.clip_tensorrt`. Run `check_server_config.py`. |
| Client cannot connect after server starts | Flow protocol/port differs from client URI. | Use the endpoint printed by the server; match `grpc`, `http`, or `websocket` and TLS suffix exactly. |

## Model and cache failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| First startup takes a long time | Model artifacts are downloading. | Use a smaller default model for smoke tests, preserve cache between runs, and avoid interrupting unless logs show a failure. |
| MD5 mismatch or repeated download retry | Corrupt partial cache or unstable network. | Remove only the affected cached artifact and retry. Do not delete the whole cache blindly. |
| `CLIP model ... not found` | Model name is not present in the runtime's support map. | Check [model-overview.md](model-overview.md), choose a supported name, and remember old aliases differ by runtime. |
| ONNX custom model path error | Directory is missing `textual.onnx` or `visual.onnx`. | Create/export both files and ensure `name` matches the exported model family. |
| Embeddings from a changed model do not match an existing index | Output dimension or embedding distribution changed. | Rebuild downstream indexes; validate `n_dim` with the search-retrieval helper. |

## Performance and OOM

| Symptom | Cause | Recovery |
| --- | --- | --- |
| CUDA/CPU OOM during encode/rank | Batch or model too large, too many replicas, or prefetch too high. | Reduce `minibatch_size`, Flow `prefetch`, client `batch_size`, or `replicas`; choose a smaller model. |
| CPU throughput is poor | Too few threads per replica or too many replicas for available CPU threads. | Reduce replicas or set `OMP_NUM_THREADS` before starting the server; benchmark with bounded helper. |
| TensorRT build OOM | Large optimization profile/workspace or unsupported model. | Use a smaller TensorRT-supported model, prebuild on an appropriate GPU, or switch runtime. Do not verify TensorRT with CPU fallback. |
| Cloud/proxy timeouts for big batches | External proxy timeout or HTTP/gRPC service limit. | Lower client `batch_size` and Flow `prefetch`; avoid sending huge CPU-bound batches through short-timeout proxies. |

## TLS and monitoring

- For gRPC TLS, certificate common name or subject alternative name must match the IP/domain used by the client.
- `protocol: http` plus `cors: true` is needed for browser-style cross-origin calls.
- Prometheus metrics need `monitoring: true` and distinct `port_monitoring` values for gateway/executor.

## Safe validation commands

```bash
python sub-skills/server-runtime/scripts/check_server_config.py sub-skills/server-runtime/scripts/torch-flow.yml --expected-runtime torch
python scripts/check_install.py --server-only
python scripts/check_install.py --server-only --check-cuda
```

Only start the server after the user approves long-running processes and possible model downloads.

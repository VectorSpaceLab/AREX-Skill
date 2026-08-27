# Runtime Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Docker launch fails with GPU flag | NVIDIA Container Toolkit or device selection unavailable | Re-run CPU plan without `--gpus` if the model supports CPU; otherwise fix host runtime. |
| Readiness returns non-200 | Model load still running, strict readiness, wrong URL/port, or failed model | Check logs and repository index; decide whether model/config or network layer owns the failure. |
| Model absent from startup table | Wrong model repository mount or path | Confirm the container sees model directories directly under `/models`. |
| Metrics endpoint missing | Metrics disabled, wrong metrics address/port, or HTTP service settings | Check `--allow-metrics`, `--metrics-port`, and network exposure. |
| GPU metrics missing | CPU-only run or GPU metrics disabled | Verify GPU runtime and `--allow-gpu-metrics`; do not treat absence as protocol failure. |
| Server crash during model load/infer | Backend/model/framework/version issue | Run model outside Triton, compare backend versions, then use debug build/GDB only if approved. |
| Poll mode sees partial files | Repository update not staged atomically | Prefer explicit mode or stage complete model directories/configs and then atomically swap. |

# vLLM Deployment and Performance Troubleshooting

Use this runbook to move from symptom to evidence. Avoid changing many flags at once; collect version, command, environment, startup logs, metrics, and one minimal repro command first.

## Quick Evidence Bundle

Ask for or collect:

```bash
python scripts/collect_env_summary.py --json --check-vllm-help
vllm serve --help | sed -n '1,120p'
```

Also capture:

- Full `vllm serve` command with model IDs redacted only if necessary.
- GPU type/count, driver/runtime versions, interconnect, node count, and container runtime.
- Startup log lines for dtype, quantization, parallel sizes, executor backend, and KV cache capacity.
- `/metrics` output or a Prometheus screenshot/query for the problem window.
- One small smoke request result and one representative benchmark result.

## OOM or Low KV Capacity

Symptoms:

- CUDA/ROCm/XPU out-of-memory during startup or first request.
- Startup logs show low `GPU KV cache size` or `Maximum concurrency`.
- Requests fail only at long context or high concurrency.

Actions:

1. Lower `--max-model-len` to the application requirement.
2. Lower `--max-num-seqs` and benchmark with realistic concurrency.
3. Lower `--gpu-memory-utilization` if other processes share the GPU; increase it only if startup has headroom.
4. Increase `--tensor-parallel-size` on one node.
5. Add `--pipeline-parallel-size` when spanning nodes or uneven splits.
6. Use quantized checkpoints or supported online quantization.
7. Add `--cpu-offload-gb` for weights if host memory and PCIe bandwidth can absorb latency.
8. Set `--kv-cache-memory-bytes` only when explicit KV reservation is needed and verified.
9. For CPU backend, set `VLLM_CPU_KVCACHE_SPACE`.

Use the bundled planner for a command skeleton:

```bash
python scripts/memory_command_planner.py \
  --model MODEL_ID_OR_PATH \
  --num-gpus 2 \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.88 \
  --cpu-offload-gb 8
```

## Unsupported Dtype or Quantization

Symptoms:

- Startup rejects `--quantization` or `--quantization-config`.
- Logs say a quantization method is unsupported on the current platform.
- Quality changes unexpectedly after quantization.

Actions:

1. Re-run `vllm serve --help` and confirm the flag spelling exists in the installed version.
2. Use `--dtype auto` unless the model/backend requires explicit dtype.
3. Prefer a checkpoint with known compatible quantization metadata.
4. For online quantization, use accepted shorthands such as `fp8_per_tensor`, `fp8_per_block`, `fp8_per_channel`, `mxfp8`, `int8_per_channel_weight_only`, or `online` with a config.
5. Remove `--quantization-config` when using a checkpoint quantization method that does not accept online config.
6. Verify platform support; CUDA, ROCm, CPU, XPU, and plugins differ.
7. Compare a small quality/latency benchmark before and after quantization.

## CUDA, ROCm, CPU, or Backend Mismatch

Symptoms:

- `torch.compile`, Triton, CUDA graph, NCCL, or kernel import errors.
- CPU-only install imports but GPU serving fails.
- Error appears near CUDA graph replay.

Actions:

- Confirm the installed package was built for the target backend.
- Confirm PyTorch sees the expected accelerator devices.
- Use `--enforce-eager` to isolate CUDA graph failures; keep it only if needed.
- Use `CUDA_LAUNCH_BLOCKING=1` for one debugging run when identifying a failing kernel.
- For custom Triton/PyTorch stacks, verify `torch.compile` with a minimal tensor function.
- Do not treat CPU inspection success as proof that GPU kernels will run.

## Bad Tensor/Data/Pipeline/Expert/Context Parallel Size

Symptoms:

- Validation errors about attention heads, KV heads, PP support, or expert count.
- Hangs or crashes after workers launch.
- Throughput drops after adding parallelism.

Actions:

1. Confirm total GPUs required: `TP × PP × DP` plus any external replicas.
2. For TP, ensure model attention heads divide the tensor parallel size.
3. For PP, ensure the model supports pipeline parallelism and layer splits are sensible.
4. For DP, remember `--max-num-seqs` is per rank and each rank has independent KV cache.
5. For EP, confirm the model is MoE and required all-to-all backend dependencies exist.
6. For DCP on GQA/MQA, ensure TP is greater than total KV heads and DCP is within valid range.
7. Benchmark TP/PP/DP changes separately; added communication can reduce throughput.

## Ray, Multiprocessing, and Torchrun/External Launcher Issues

Symptoms:

- Ray says no node types can satisfy resource request.
- Worker nodes do not join.
- Python multiprocessing errors mention safe importing or bootstrapping.
- External launcher ranks bind to the wrong IP or port.

Actions:

- Set `VLLM_HOST_IP` to the correct private IP per node.
- Set `NCCL_SOCKET_IFNAME` and `GLOO_SOCKET_IFNAME` to the intended network interface when auto-detection fails.
- Run `ray status` and `ray list nodes` before starting vLLM on Ray.
- Keep package versions, model paths, and environment variables consistent across nodes.
- For Python scripts using `LLM`, guard engine creation with `if __name__ == "__main__":` when multiprocessing is involved.
- For multi-node torchrun sanity tests, use static rendezvous when DNS resolution is unreliable.

## NCCL, GLOO, and Network Hangs

Symptoms:

- Distributed startup hangs.
- NCCL falls back to socket transport unexpectedly.
- Cross-node throughput is much lower than single-node throughput.

Actions:

```bash
export NCCL_DEBUG=TRACE
export VLLM_HOST_IP=PRIVATE_NODE_IP
export NCCL_SOCKET_IFNAME=eth0
export GLOO_SOCKET_IFNAME=eth0
```

- Confirm all nodes can reach the master address and DP/RPC ports.
- Keep distributed traffic on private networks.
- For InfiniBand, verify interface/container flags and look for `NET/IB/GDRDMA` in NCCL logs.
- If logs show `NET/Socket`, performance can be much lower for cross-node TP.
- Temporary NCCL workarounds such as disabling P2P may diagnose hardware/driver issues but can reduce performance; fix the underlying driver/network when possible.

## Prefix Cache and KV Offload Misconfiguration

Symptoms:

- Prefix cache hit rate is low despite repeated prompts.
- Offloading adds latency without improving hit rate.
- Filesystem offload does not share blocks across processes.

Actions:

- Verify prompts truly share identical token prefixes after chat templates and system messages.
- Route similar-prefix traffic to the same DP rank or replica when possible.
- Prefix caching mainly improves prefill; it will not help long decode-dominated generations.
- For connector offload, set `cpu_bytes_to_use` larger than aggregate GPU KV if expecting CPU tier benefits.
- Ensure offload `block_size` is compatible with GPU block size.
- For filesystem tiers, use fast storage and tune read/write thread counts.
- Set fixed `PYTHONHASHSEED` across instances when sharing a filesystem offload root.

## Metrics Endpoint Missing

Symptoms:

- `curl /metrics` returns 404, empty response, or proxy HTML.
- Prometheus target is down.
- Grafana dashboard has no data.

Actions:

1. Query the vLLM server directly: `curl http://HOST:PORT/metrics`.
2. Confirm the server is the OpenAI-compatible API server, not an offline script.
3. Check host binding and firewall rules.
4. Check reverse proxy path rewrites.
5. In Prometheus, inspect target health before debugging Grafana.
6. Verify dashboard variables match the actual model and instance labels.

## Benchmark Misinterpretation

Symptoms:

- A change appears faster or slower but workload settings differ.
- Production throughput does not match benchmark results.
- Structured outputs, LoRA, multimodal, or parser features reduce throughput unexpectedly.

Actions:

- Keep model revision, dtype, quantization, parallelism, max length, sampling, prompt/output length, and concurrency fixed across comparisons.
- Use random/synthetic data for controlled engine comparisons, but use production-shaped datasets for capacity planning.
- Compare TTFT, TPOT, ITL, request throughput, output-token throughput, and total-token throughput together.
- Feature regressions should be bisected one feature at a time, then routed to the feature-owning sub-skill for syntax/config fixes.
- For lower throughput after structured outputs plus LoRA, first compare baseline, structured-only, LoRA-only, and combined runs; inspect CPU utilization, parser overhead, adapter memory, KV cache pressure, and profiler traces.

## Native Verification Candidates

Use these only after the full generated skill is integrated and the user environment can safely run them:

- Start a tiny local model server and query `/metrics`.
- Run `vllm bench serve` with `--dataset-name random` against the tiny server.
- Run an offline profiling example with a small model and bounded tokens.
- Run a distributed smoke only on user-provided multi-GPU/multi-node hardware.

Skip native execution when models would download unexpectedly, GPUs are unavailable, optional backend packages are missing, or distributed ports/network permissions are unknown.

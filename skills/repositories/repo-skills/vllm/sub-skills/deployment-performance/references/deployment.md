# vLLM Deployment Topologies

Use this reference to choose a serving topology and launch pattern. All model execution and distributed launch examples are hardware-gated; adapt IPs, ports, model identifiers, container images, and security controls to the user's environment.

## Topology Decision Tree

1. If the model and KV cache fit on one GPU, start with one `vllm serve` process and no distributed flags.
2. If the model is too large for one GPU but fits on one node, use tensor parallelism: `--tensor-parallel-size <gpu_count>`.
3. If the model is too large for one node, combine tensor and pipeline parallelism: `--tensor-parallel-size <gpus_per_node> --pipeline-parallel-size <node_count>`.
4. If throughput is limited after one model replica fits, add data parallelism or external replicas behind a load balancer.
5. For MoE models, consider expert parallelism with data parallelism when expert layers dominate cost.
6. For long-context decode with KV duplication, add decode context parallelism only after validating TP and model KV-head constraints.
7. For prefill/decode latency separation, use disaggregated prefill; do not expect total throughput gains from disaggregation alone.

## Single-Node Serving

### Tensor parallel

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 4
```

Use when a model fits across GPUs on one node. Startup should show a TP world size of 4 and KV cache capacity per engine. Avoid initializing CUDA in parent Python code before creating `LLM`; set `CUDA_VISIBLE_DEVICES` instead of manually calling CUDA device setters.

### Pipeline parallel on one node

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 4 \
  --pipeline-parallel-size 2
```

Pipeline parallelism splits layers. It can help when GPUs do not evenly divide the model or when tensor-parallel communication is too expensive on weaker interconnects.

### Executor backend

- Single-node defaults commonly use Python multiprocessing.
- Use `--distributed-executor-backend mp` to force multiprocessing.
- Use `--distributed-executor-backend ray` when the deployment already uses Ray or spans nodes.

## Multi-Node with Ray

Ray is optional. Install and validate it in the target environment before launch. Every node must see the same model path/package versions and should run in a consistent container or environment.

Typical pattern after a Ray cluster is up:

```bash
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 2 \
  --distributed-executor-backend ray
```

For 2 nodes with 8 GPUs each, `TP=8` and `PP=2` keeps tensor parallel within each node and pipeline parallel across nodes. If using Ray inside containers, run vLLM inside the containers, not on the host shell.

Validation commands:

```bash
ray status
ray list nodes
```

Check that Ray reports the expected nodes and GPUs and that vLLM and Ray agree on node IPs. If Ray cannot satisfy GPU resource requests despite available GPUs, set `VLLM_HOST_IP` per node and verify the address Ray advertises.

## Multi-Node with Multiprocessing

Run one command per node. The head process accepts requests; worker nodes use `--headless`.

Node 0:

```bash
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 2 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr HEAD_NODE_IP
```

Node 1:

```bash
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 2 \
  --nnodes 2 \
  --node-rank 1 \
  --master-addr HEAD_NODE_IP \
  --headless
```

`HEAD_NODE_IP` must be reachable by all nodes. Use private-network addresses; distributed control/data traffic should not be exposed to untrusted networks.

## Data Parallel Serving

Data parallelism replicates model weights across ranks and serves independent batches. Each DP rank has its own KV cache. Load balancing matters because prefix-cache benefits can depend on routing similar prompts to the same rank.

### Internal load balancing

Single node, DP=4:

```bash
vllm serve MODEL_ID_OR_PATH \
  --data-parallel-size 4
```

DP with TP on one 8-GPU node:

```bash
vllm serve MODEL_ID_OR_PATH \
  --data-parallel-size 4 \
  --tensor-parallel-size 2
```

Remember `--max-num-seqs` applies per DP rank.

### Multi-node internal DP

Node 0, ranks 0-1:

```bash
vllm serve MODEL_ID_OR_PATH \
  --data-parallel-size 4 \
  --data-parallel-size-local 2 \
  --data-parallel-address HEAD_NODE_IP \
  --data-parallel-rpc-port 13345
```

Node 1, ranks 2-3:

```bash
vllm serve MODEL_ID_OR_PATH \
  --headless \
  --data-parallel-size 4 \
  --data-parallel-size-local 2 \
  --data-parallel-start-rank 2 \
  --data-parallel-address HEAD_NODE_IP \
  --data-parallel-rpc-port 13345
```

### Hybrid and external load balancing

- Hybrid DP uses `--data-parallel-hybrid-lb`; every node exposes an API endpoint, and an upstream load balancer distributes requests across nodes.
- External LB treats each independent dense-model server as a replica behind a separate HTTP load balancer. For MoE DP/EP, use explicit `--data-parallel-rank`, `--data-parallel-address`, and unique HTTP ports per rank.
- Increase `--api-server-count` if the head API process bottlenecks at large DP sizes; size it with local rank count and CPU capacity.

## Expert Parallel MoE Serving

Expert parallelism is for MoE models. Do not enable it for dense models.

Single-node EP with DP=8:

```bash
vllm serve deepseek-ai/DeepSeek-V3-0324 \
  --tensor-parallel-size 1 \
  --data-parallel-size 8 \
  --enable-expert-parallel
```

EP size is computed as `TP × DP`. With `TP=1, DP=8`, attention weights are replicated across DP ranks while experts are sharded across EP ranks. With `TP>1`, attention weights are tensor-sharded within each DP group.

Backend selection uses `--all2all-backend`:

| Backend | Best use |
| --- | --- |
| `allgather_reducescatter` | General default backend. |
| `deepep_high_throughput` | Multi-node prefill-heavy MoE workloads. |
| `deepep_low_latency` | Multi-node decode-heavy MoE workloads. |
| `flashinfer_nvlink_one_sided` | Multi-node NVLink systems with FlashInfer one-sided A2A. |
| `flashinfer_nvlink_two_sided` | Multi-node NVLink systems with FlashInfer two-sided A2A. |

If initialization hangs on InfiniBand clusters, set an Ethernet interface for GLOO discovery, for example:

```bash
export GLOO_SOCKET_IFNAME=eth0
```

EPLB can rebalance skewed expert load:

```bash
vllm serve Qwen/Qwen3-30B-A3B \
  --enable-eplb \
  --eplb-config '{"window_size":1000,"step_interval":3000,"num_redundant_experts":2,"log_balancedness":true}'
```

## Decode Context Parallel

Decode context parallel shards KV cache along token positions after TP has already sharded across KV heads. It is mainly useful for long-context decode and models where TP causes KV duplication.

Example:

```bash
vllm serve MODEL_ID_OR_PATH \
  --tensor-parallel-size 8 \
  --decode-context-parallel-size 2
```

Constraints to check:

- For GQA/MQA models without MLA, `tensor_parallel_size` must be greater than total KV heads.
- `decode_context_parallel_size` must not exceed `tensor_parallel_size // total_num_kv_heads` for those models.
- Query-per-KV-head count must be divisible by DCP size.
- Higher DCP reduces KV duplication but increases communication overhead.

## Disaggregated Prefill and KV Transfer

Disaggregated prefill runs prefill and decode in separate vLLM instances and transfers KV cache between them. Use it to tune TTFT and ITL separately or reduce tail ITL caused by prefill work interrupting decode. It does not inherently improve throughput.

Connector families include Example, LMCache, NIXL, Mooncake, MoRI-IO, MultiConnector, OffloadingConnector, and FlexKV. A minimal connector-shaped command uses `--kv-transfer-config` JSON:

```bash
vllm serve MODEL_ID_OR_PATH \
  --kv-transfer-config '{
    "kv_connector": "NixlConnector",
    "kv_role": "kv_both",
    "kv_buffer_device": "cuda",
    "kv_connector_extra_config": {"backends": ["UCX", "GDS"]}
  }'
```

Operational checks:

- Confirm the connector and backend packages are installed on every node.
- Verify network/storage paths used by the connector are reachable and private.
- Separate prefill and decode metrics when evaluating TTFT vs ITL.
- Treat connector APIs and feature compatibility as experimental unless the target release documents them as stable.

## Hardware and Backend Selection

### CUDA/NVIDIA

- Prefer fast intra-node interconnect for tensor parallelism.
- For cross-node TP, InfiniBand and GPUDirect RDMA are strongly preferred.
- Use `NCCL_DEBUG=TRACE` to confirm whether traffic uses `NET/IB/GDRDMA` or falls back to `NET/Socket`.
- Containers often need `/dev/shm` and IPC settings for high-performance communication.

### ROCm/AMD

- Check ROCm-specific quantization and attention-backend support before copying CUDA flags.
- MoRI-IO connector is ROCm-specific in the disaggregated prefill docs.

### CPU

- CPU package import and CLI help are suitable for smoke inspection.
- Do not extrapolate CPU throughput to GPU serving.
- Set `VLLM_CPU_KVCACHE_SPACE` for CPU KV cache capacity.

### Optional plugin backends

Platform plugins can change device names, supported quantization methods, attention backends, and cache behavior. Always verify `vllm serve --help`, startup logs, and a smoke request in the installed target environment.

## Security and Network Notes

- Bind public HTTP interfaces intentionally; use `--host 127.0.0.1` for local-only tests.
- Keep Ray, NCCL, GLOO, DP RPC, and connector traffic on private networks.
- Do not expose Ray cluster ports or distributed initialization endpoints to untrusted clients.
- Treat model paths, cache paths, and connector filesystem tiers as sensitive if prompts or KV cache content may contain private data.

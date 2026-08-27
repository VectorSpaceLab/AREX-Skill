# Deployment matrix

## Topology overview

| Run mode | Role | Typical flags | Notes |
| --- | --- | --- | --- |
| `normal` | Single server | `--model_dir`, `--host`, `--port`, `--tp`, `--dp` | Simplest deployment. |
| `pd_master` | PD scheduler / entrypoint | `--run_mode pd_master`, `--host`, `--port` | Start this first in PD flows. |
| `prefill` | PD prefill worker | `--run_mode prefill`, `--pd_master_ip`, `--pd_master_port`, `--tp`, `--dp` | Needs a master to join. |
| `decode` | PD decode worker | `--run_mode decode`, `--pd_master_ip`, `--pd_master_port`, `--tp`, `--dp` | Joins the same master as prefill. |
| `config_server` | PD config / registration service | `--run_mode config_server` | Used by some large-scale PD setups. |
| `visual_only` | Multimodal visual worker | `--run_mode visual_only`, `--visual_tp`, `--visual_dp` | Special multimodal deployment case. |

## Common launch variables

| Variable | Meaning |
| --- | --- |
| `MODEL_DIR` | Checkpoint path used by the server or worker. |
| `HOST` | Bind address for the current process. |
| `PD_MASTER_IP` | Address that worker roles use to reach the PD master. |
| `PD_MASTER_PORT` | Port on which the PD master listens. |
| `PREFILL_CUDA_DEVICES` | GPU assignment for the prefill worker. |
| `DECODE_CUDA_DEVICES` | GPU assignment for the decode worker. |
| `UCX_NET_DEVICES` | RDMA device selection for NIXL / UCX paths. |
| `LOG_DIR` | Directory that collects the per-process logs and summary file. |

## Typical startup order

1. Decide whether the selected model actually needs a split topology.
2. Verify the GPU / host plan and clear proxies for local traffic.
3. Start `pd_master` or `config_server` first when the topology requires it.
4. Launch `prefill` and `decode` only after the coordinating role is ready.
5. If multimodal workers are involved, verify the visual/audio worker settings
   before the final request smoke.
6. Run one tiny request against the live service before any larger benchmark.

## Deployment knobs that often matter

- `--disable_cudagraph` is common in split or dynamic topologies.
- `--use_dynamic_prompt_cache` affects cache reuse behavior.
- `--enable_mps` may improve certain GPU-sharing scenarios.
- `--enable_cpu_cache` and `--enable_disk_cache` change cache behavior and can
  alter memory or storage prerequisites.
- `--select_p_d_node_strategy` and `--dp_balancer` influence how PD nodes are
  selected or balanced.
- `--pd_trans_mode` distinguishes transport choices such as NCCL or NIXL when
  the deployment path supports them.

## What to record in a deployment log

- Run mode for each process.
- Model directory and model name.
- GPU assignment per process.
- Port values and bind addresses.
- Proxy / `no_proxy` state.
- Cache and transport settings.
- The result of one local request smoke after the topology is live.

## When to stop and revisit the plan

- The same host is trying to reuse the same port.
- A worker can see the model directory but not the coordinating service.
- The topology assumes RDMA or MPS that the host does not provide.
- A transient PD registration error persists after several minutes.

# CLI reference

The primary entry point is:

```bash
python -m lightllm.server.api_server --help
```

The live CLI is built from `lightllm.server.api_cli.add_cli_args(parser)` and
the `StartArgs` dataclass in `lightllm.server.core.objs.start_args_type`.
Use `scripts/inspect_start_args.py` to print the currently installed default
surface.

## Run modes

| `--run_mode` value | Meaning |
| --- | --- |
| `normal` | Single-process LightLLM server. |
| `prefill` | PD disaggregation prefill node. |
| `decode` | PD disaggregation decode node. |
| `pd_master` | PD scheduler / master node. |
| `config_server` | Shared config / registration server used by some PD flows. |
| `visual_only` | Multimodal visual-only worker mode. |

## Common server / network flags

| Flag | Notes |
| --- | --- |
| `--host` / `--port` | Listener address for the process. |
| `--httpserver_workers` | Worker count for the HTTP server wrapper. |
| `--hypercorn_config` | Optional Hypercorn configuration path. |
| `--zmq_mode` | ZMQ transport URI. |
| `--pd_master_ip` / `--pd_master_port` / `--pd_master_mode` | PD master discovery and master mode controls. |
| `--config_server_host` / `--config_server_port` | Config server discovery and registration. |
| `--use_config_server_to_init_nccl` | Initialize NCCL via the config server path. |
| `--nccl_host` / `--nccl_port` | Explicit NCCL rendezvous settings. |

## Model and tokenizer flags

| Flag | Notes |
| --- | --- |
| `--model_name` / `--model_owner` | Model metadata and display name. |
| `--model_dir` | Hugging Face or local model directory. |
| `--tokenizer_mode` | Tokenizer loading strategy. |
| `--load_way` | Weight loading strategy. |
| `--max_total_token_num` | Max total tokens supported by the runtime. |
| `--mem_fraction` | Fraction of GPU memory to reserve for the model. |
| `--batch_max_tokens` | Batch token budget. |
| `--eos_id` | EOS token ids. |
| `--chat_template` | Explicit chat template override. |
| `--trust_remote_code` | Allow remote model code. |

## Topology and scheduling flags

| Flag | Notes |
| --- | --- |
| `--tp` / `--dp` | Tensor/data parallel degrees. |
| `--nnodes` / `--node_rank` | Multi-node topology settings. |
| `--select_p_d_node_strategy` | PD node selection policy. |
| `--dp_balancer` | Decode/prefill balancing policy. |
| `--router_token_ratio` / `--router_max_wait_tokens` | Router scheduling knobs. |
| `--disable_aggressive_schedule` | Reduce aggressive scheduling behavior. |
| `--enable_prefill_decode_mixed` | Mixed prefill/decode execution. |
| `--use_dynamic_prompt_cache` | Enable dynamic prompt cache. |
| `--chunked_prefill_size` / `--disable_chunked_prefill` | Chunked prefill controls. |

## API feature flags

| Flag | Notes |
| --- | --- |
| `--tool_call_parser` | Tool-call parser family. |
| `--reasoning_parser` | Reasoning parser family. |
| `--enable_multimodal` | Enable multimodal routing and model setup. |
| `--disable_vision` / `--disable_audio` | Disable individual multimodal paths. |
| `--use_tgi_api` | Expose TGI-style API behavior. |
| `--use_reward_model` | Enable reward-model mode. |
| `--enable_rl` | Enable RL endpoints / workflow. |
| `--enable_profiling` | Enable profiler integration, e.g. `torch_profiler` or `nvtx`. |
| `--health_monitor` | Turn on health monitoring behavior. |
| `--enable_monitor_auth` | Enable monitor auth gating. |

## Backend / quantization flags

| Flag | Notes |
| --- | --- |
| `--llm_prefill_att_backend` / `--llm_decode_att_backend` | Attention backend selection. |
| `--vit_att_backend` | Vision backend selection. |
| `--quant_type` / `--quant_cfg` | Text-model quantization selection and config. |
| `--vit_quant_type` / `--vit_quant_cfg` | Vision quantization selection and config. |
| `--llm_kv_type` / `--llm_kv_quant_group_size` | KV cache format and quantization group size. |
| `--sampling_backend` | Sampling backend family. |
| `--penalty_counter_mode` | Penalty counter implementation. |
| `--enable_ep_moe` | Enable EP MoE path. |
| `--enable_fused_shared_experts` | Shared-experts optimization. |
| `--mtp_mode` / `--mtp_draft_model_dir` / `--mtp_step` | Multi-token prediction controls. |
| `--hardware_platform` | Hardware family selector, usually `cuda` on NVIDIA systems. |
| `--enable_torch_fallback` / `--enable_triton_fallback` | Fallback path selection. |

## Related scripts

- `scripts/inspect_start_args.py` prints the field names and selected defaults
  for the currently installed package.
- `scripts/inspect_cuda.py` confirms the target environment is CUDA-capable.

# MoE API Reference

## Purpose

Read this when you need the verified signatures for hosted experts, remote expert clients, or custom expert registration.

## Server-side API

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `hivemind.moe.Server` | `Server(dht, module_backends, num_connection_handlers=1, update_period=30, expiration=None, start=False, checkpoint_dir=None, **kwargs)` | Low-level server wrapper. |
| `Server.create` | `Server.create(num_experts=None, expert_uids=None, expert_pattern=None, expert_cls='ffn', hidden_dim=1024, optim_cls=torch.optim.Adam, scheduler='none', num_warmup_steps=None, num_training_steps=None, clip_grad_norm=None, num_handlers=None, min_batch_size=1, max_batch_size=4096, device=None, initial_peers=(), checkpoint_dir=None, compression=0, stats_report_interval=None, custom_module_path=None, update_period=30, expiration=None, *, start, **kwargs)` | High-level factory used by the CLI. |
| `background_server` | `background_server(*args, shutdown_timeout=5, **kwargs) -> PeerInfo` | Convenient context manager for tests and demos. |
| `ModuleBackend` | `ModuleBackend(name, module, *, optimizer=None, scheduler=None, args_schema=None, kwargs_schema=None, outputs_schema=None, **kwargs)` | Wraps a `torch.nn.Module` for remote access. |
| `ModuleBackend.forward` | `forward(self, *inputs)` | Batch-parallel forward. |
| `ModuleBackend.backward` | `backward(self, *inputs)` | Batch-parallel backward. |
| `ModuleBackend.get_info` | `get_info(self)` | Returns runtime metadata. |
| `ModuleBackend.get_pools` | `get_pools(self)` | Returns the task pools servicing the expert. |

## DHT expert registry helpers

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `declare_experts` | `declare_experts(dht, uids, expiration_time, wait=True)` | Publishes expert UIDs into the DHT. |
| `get_experts` | `get_experts(dht, uids, expiration_time=None, return_future=False)` | Retrieves remote expert handles from the DHT. |
| `register_expert_class` | `register_expert_class(name, sample_input)` | Decorator used to register built-in or custom expert classes. |

## Client-side API

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `RemoteExpert` | `RemoteExpert(expert_info, p2p)` | Proxy for one expert. |
| `RemoteExpert.forward` | `forward(self, *args, **kwargs)` | Forward pass through one hosted expert. |
| `RemoteMixtureOfExperts` | `RemoteMixtureOfExperts(*, in_features, grid_size, dht, uid_prefix, k_best, k_min=1, forward_timeout=None, timeout_after_k_min=None, backward_k_min=1, backward_timeout=None, detect_anomalies=False, allow_zero_outputs=False, **dht_kwargs)` | Gated mixture-of-experts router. |
| `RemoteSwitchMixtureOfExperts` | `RemoteSwitchMixtureOfExperts(*, grid_size, utilization_alpha=0.9, grid_dropout=1.0, jitter_eps=0.01, k_best=1, k_min=0, backward_k_min=0, allow_zero_outputs=True, **kwargs)` | Switch-style MoE router. |
| `RemoteMixtureOfExperts.forward` | `forward(self, input, *args, **kwargs)` | Routes a batch through selected experts. |
| `RemoteSwitchMixtureOfExperts.forward` | `forward(self, input, *args, **kwargs)` | Returns routed output plus balancing loss. |

## Built-in expert classes

The server ships these built-in expert types via `expert_cls`:

- `ffn`
- `transformer`
- `nop`
- `nop_delay`
- `det_dropout`

`custom_module_path` lets the server load more expert classes from a user-provided Python file that uses `register_expert_class(...)`.

## Behavior notes

- `Server.create(...)` is the most convenient route for demos and CLI use.
- `background_server(...)` is the best route when you want a temporary expert host in tests or tutorials.
- `RemoteExpert` is the direct path for one expert; `RemoteMixtureOfExperts` and `RemoteSwitchMixtureOfExperts` are the higher-level routing layers.
- `ModuleBackend` handles checkpointing, optimizer stepping, and batch-parallel compute on the server side.
- On CUDA-capable hosts, `hivemind-server` may default to GPU execution unless you override `--device cpu`.

## Validation sources

- Verified from installed package signatures and CLI help.
- Cross-checked against `docs/modules/server.rst`, `docs/modules/client.rst`, `docs/user/moe.md`, `tests/test_moe.py`, `tests/test_custom_experts.py`, `tests/test_expert_backend.py`, and `tests/test_start_server.py`.

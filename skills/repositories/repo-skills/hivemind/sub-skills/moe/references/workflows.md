# MoE Workflows

## Purpose

Read this for the practical patterns that host experts, fetch them from the DHT, and route tensors through them.

## 1) Start a simple expert server

The package exposes `hivemind-server` for the standard serving workflow.

```bash
hivemind-server --expert_cls ffn --hidden_dim 512 --num_experts 5 --expert_pattern "expert.[0:5]"
```

What to expect:

- the server starts a DHT node in the background
- the console prints the visible multiaddresses to use as initial peers
- each expert is registered into the DHT for discovery

Useful knobs:

- `--num_experts` plus `--expert_pattern` for generated names
- `--expert_uids` when you want exact names
- `--device cpu` if you do not want CUDA to be used on a GPU host
- `--initial_peers` to join an existing expert network
- `--custom_module_path` to load extra expert classes

## 2) Connect to hosted experts from Python

```python
import torch
import hivemind

# dht = hivemind.DHT(initial_peers=[...], start=True)
expert1, expert4 = hivemind.moe.get_experts(dht, ["expert.1", "expert.4"])
assert expert1 is not None and expert4 is not None

x = torch.randn(3, 512)
out = expert1(x)
out.sum().backward()
```

Use this pattern when:

- you already know the expert UIDs
- you want a direct proxy to one expert
- you are composing a larger PyTorch model with remote layers

## 3) Use a routed MoE layer

```python
import torch
import hivemind

dmoe = hivemind.RemoteMixtureOfExperts(
    in_features=512,
    uid_prefix="expert.",
    grid_size=(5,),
    dht=dht,
    k_best=2,
)

out = dmoe(torch.randn(3, 512))
out.sum().backward()
```

When to use this:

- you want Hivemind to pick the best experts automatically
- you need a differentiable router/gating layer
- you are building a mixture-of-experts model rather than calling experts by name

`RemoteSwitchMixtureOfExperts` is the alternative when you want switch-style routing and balancing loss.

## 4) Register custom experts

If you need a custom module, register it with `register_expert_class(...)` or load a file with `custom_module_path`.

Good pattern:

1. define the module in a small standalone Python file
2. use `register_expert_class("your_name", sample_input)`
3. start the server with `--custom_module_path your_file.py`
4. fetch the experts from the DHT and validate a forward/backward pass

The built-in examples in the repository use the same pattern for deterministic dropout and custom expert networks.

## 5) Checkpoint and restore expert state

`ModuleBackend` owns the optimizer/scheduler/checkpoint behavior on the server side.

Use this workflow when:

- you want to persist expert weights across restarts
- you want learning-rate scheduling inside the remote expert host
- you need to debug why the expert's state advanced but the client did not notice

## 6) Temporary servers in tests or small demos

`background_server(...)` is the fastest way to spin up a temporary MoE host.

Use it when you need a short-lived server in a notebook, a smoke test, or a tiny example. It returns peer metadata so you can immediately create a DHT client and fetch experts.

## 7) Readiness check

Before handing the workflow to another agent, run:

```bash
python scripts/check_install.py
```

If you expect CUDA defaults, add `--check-cuda` so you know whether the server will prefer the GPU path on this machine.

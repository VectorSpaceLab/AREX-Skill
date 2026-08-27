# Disaggregated Deployment Workflows

## Main deployment idea

LightX2V can split one generation request into separate roles:

- **controller**: accepts requests, schedules work, and manages resource reuse
- **encoder**: prepares request-side tensors and input buffers
- **transformer**: runs the core denoising / model work
- **decoder**: turns latent outputs into final media

The package entry point for the worker roles is `python -m lightx2v.disagg.examples.run_service`. The controller and user roles use the sibling package entry points or the higher-level shell launcher.

## Common launch patterns

### Controller / encoder / transformer / decoder

Use a config that already declares the disaggregation mode and the role ranks.

```bash
python -m lightx2v.disagg.examples.run_service \
  --service controller \
  --model_cls wan2.2_moe \
  --task i2v \
  --model_path /path/to/model \
  --config_json /path/to/disagg_config.json
```

The `--service auto` path reads the mode from `config_json`. If the config already contains the role, you can omit `--service` and let the entry point resolve it.

### Dynamic multi-node launch

The repository's shell launcher prepares environment variables, cleans stale processes, then starts the controller and worker roles. The detailed shell wrapper is environment-specific, so this skill documents the behavior and the package entry points instead of depending on that script verbatim.

Use this workflow when you need:
- automatic topology selection from a config tree
- temporary cleanup of stale workers or ports
- optional Nsight profiling around the role processes
- centralized request/metrics collection

### Baseline / single-task launch

The baseline launcher is intended for repeatable controller-driven throughput checks. It is more sensitive to GPU count, task source, and request generation count than a normal one-off deployment.

Use it when you want to compare a single model family under a fixed load shape rather than manually orchestrating each role.

## Role-by-role thinking

When a request asks for a disaggregated deployment, answer in this order:

1. Decide whether the user needs the controller flow or only an individual worker role.
2. Confirm the topology (`single_node` or `multi_node`).
3. Confirm the config JSON that defines ranks, ports, and bootstrap addresses.
4. Check which roles need to run on the local machine.
5. If needed, use the planner helper to print the exact entry-point commands.

## Environment notes

- `PYTHONPATH` must include the project tree or the package must be installed.
- Multi-GPU roles depend on the PyTorch distributed stack.
- The transport layer may require `pyzmq`, RDMA-related packages, or Mooncake-related environment settings depending on the config.
- The controller can reuse request and stage metrics across tasks, so avoid restarting roles unless the topology or config really changed.

## What to tell a future agent

A strong answer from this route names:
- the service role(s)
- the config file and the role map inside it
- the topology
- the launch order
- the relevant transport or profiling env vars
- the outputs or logs to watch

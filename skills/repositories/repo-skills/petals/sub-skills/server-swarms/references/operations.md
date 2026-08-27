# Server Operations

Production Petals serving is a networked, long-running operation. Plan device, cache, model access, and cleanup before launching.

## Public capacity

For public contribution, use a GPU-capable environment when possible, authenticate to gated model repositories when needed, choose a stable cache, and expose a reachable port. The server reports throughput and announces hosted blocks to the DHT.

## Docker-style deployment facts

Official container-style operation uses a CUDA base image, installs Python and Torch, installs Petals, mounts a cache volume, and sets a cache environment variable. Treat full image builds as large network/build tasks requiring user approval.

## Cache and disk

Use `--cache_dir` and `--max_disk_space` for predictable disk usage. A server can cache multiple block revisions over time, especially when rebalancing.

## Restart loops

A repository-maintained restart loop kills broad `p2p`/server process patterns and loops forever. Do not copy that pattern blindly. Prefer a real supervisor that tracks exact PIDs, has backoff, preserves logs, and avoids killing unrelated processes.

## Backend choices

- Use `--quant_type none` when bitsandbytes is not verified.
- Use `--tensor_parallel_devices` only after checking device balance and model-family support.
- CPU serving is for tiny private smoke tests, not public performance claims.

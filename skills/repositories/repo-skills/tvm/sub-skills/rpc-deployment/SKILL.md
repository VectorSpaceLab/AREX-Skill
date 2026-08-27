---
name: rpc-deployment
description: "Guides TVM RPC tracker/server/proxy setup, cross-compilation,
  remote module upload/load/run, and deployment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TVM RPC and Deployment

Use this route when a task involves TVM RPC, cross-compilation, remote device
execution, tracker/server/proxy commands, module upload/load, target triples,
remote timing, or RPC-backed meta-schedule runners.

## Route

1. Confirm local TVM import and target compile support. Use
   [`../install-build/SKILL.md`](../install-build/SKILL.md) for build/import
   failures.
2. Decide whether the task needs direct RPC server, tracker-managed devices, or
   a proxy. Read [`references/cli-and-runtime.md`](references/cli-and-runtime.md).
3. For cross-compilation and remote execution, read
   [`references/cross-compilation.md`](references/cross-compilation.md) and keep
   target triple, device runtime, export artifact, upload path, and run device
   explicit.
4. Run [`scripts/rpc_cli_help_probe.py`](scripts/rpc_cli_help_probe.py) for safe
   CLI/API availability. It prints help text and does not start persistent
   services.
5. Use [`references/troubleshooting.md`](references/troubleshooting.md) for port
   conflicts, keys, timeouts, tracker query failures, target-host mismatch,
   module load errors, and remote device availability.

## API anchors

```python
from tvm import rpc

remote = rpc.connect(url, port, key="", session_timeout=0)
tracker = rpc.connect_tracker(url, port)
remote.upload("lib.tar")
func = remote.load_module("lib.tar")
dev = remote.cpu(0)
```

Use `rpc.LocalSession()` for a local smoke that exercises upload/load/run
without opening a network listener.

## CLI anchors

```bash
python -m tvm.exec.rpc_server --host 0.0.0.0 --port 9090
python -m tvm.exec.rpc_tracker --host 0.0.0.0 --port 9190 --port-end 9191
python -m tvm.exec.query_rpc_tracker --host TRACKER_HOST --port 9190
python -m tvm.exec.rpc_proxy --host PROXY_HOST --port 9090 --tracker TRACKER_HOST:9190
```

Start long-lived services only after the user approves host/port/key choices and
knows how to stop the processes.

## Boundaries

- Relax compilation before export: [`../relax-compile/SKILL.md`](../relax-compile/SKILL.md).
- S-TIR/meta-schedule runner selection: [`../s-tir-tuning/SKILL.md`](../s-tir-tuning/SKILL.md).
- TIRx CUDA kernel codegen: [`../tirx-kernels/SKILL.md`](../tirx-kernels/SKILL.md).

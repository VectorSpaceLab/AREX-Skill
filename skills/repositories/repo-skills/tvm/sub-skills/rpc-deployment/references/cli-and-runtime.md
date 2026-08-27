# RPC CLI and Runtime Notes

## API signatures

Verified public APIs:

```python
tvm.rpc.connect(url, port, key="", session_timeout=0, session_constructor_args=None, enable_logging=False)
tvm.rpc.connect_tracker(url, port)
```

Direct `connect` returns a session to an RPC server. `connect_tracker` returns a
tracker client that can request a registered device by key.

## Components

| Component | Purpose | Typical command |
|---|---|---|
| RPC server | Runs on the target device and executes uploaded modules | `python -m tvm.exec.rpc_server --host 0.0.0.0 --port 9090` |
| RPC tracker | Assigns registered servers to clients by key | `python -m tvm.exec.rpc_tracker --host 0.0.0.0 --port 9190 --port-end 9191` |
| Query tool | Lists tracker queues/devices | `python -m tvm.exec.query_rpc_tracker --host HOST --port 9190` |
| RPC proxy | Forwards traffic when clients cannot directly reach servers | `python -m tvm.exec.rpc_proxy --host PROXY --port 9090 --tracker TRACKER:9190` |

Use explicit port ranges in shared environments so services do not silently bind
unexpected ports. Record host, port, key, and timeout in the user's task notes.

## Safe local smoke

Before using real network services, compile and run through a local session:

```python
from tvm import rpc

remote = rpc.LocalSession()
remote.upload("lib.tar")
mod = remote.load_module("lib.tar")
dev = remote.cpu(0)
```

This validates packaging and remote-module APIs without proving remote network
reachability.

## Service lifecycle

1. Confirm the target device has a TVM runtime build compatible with the module
   you will upload.
2. Start tracker if using queued/shared devices.
3. Start server with the expected key or direct host/port.
4. Query tracker and confirm the key/device appears.
5. Compile/export locally for the remote target.
6. Connect, upload, load, create remote tensors, run, then time with
   `time_evaluator` if needed.
7. Stop long-lived processes when the run finishes.

Do not start persistent RPC services just to inspect command availability. Use
`rpc_cli_help_probe.py` for safe help/import validation.

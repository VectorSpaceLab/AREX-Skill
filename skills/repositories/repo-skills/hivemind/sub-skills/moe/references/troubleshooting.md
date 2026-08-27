# MoE Troubleshooting

## Purpose

Read this when a hosted expert server, remote expert client, or custom expert module fails.

## 1) `No experts found` / `None` from `get_experts`

**Symptoms**

- `get_experts(...)` returns `None` for one or more UIDs
- `RemoteMixtureOfExperts` cannot discover any valid experts
- the server logs show that it started, but the client never finds the expected names

**Likely causes**

- the expert UID pattern does not match what the server published
- the client is looking at the wrong DHT or the wrong `initial_peers`
- the expert registration expired before the client looked it up

**Recovery**

1. Compare the exact expert UID strings on both sides.
2. Reuse the server's visible DHT addresses when creating the client DHT.
3. Check that the expert expiration window is long enough for the client to join.
4. Start with `background_server(...)` for a local smoke test before trying a distributed deployment.

## 2) `hivemind-server` starts on the wrong device

**Symptoms**

- the server uses a GPU unexpectedly
- the server fails on a host without a compatible CUDA runtime

**Likely cause**

- the host reports CUDA availability, so the server chose the GPU path by default

**Recovery**

- pass `--device cpu` to force a CPU deployment
- confirm the host's CUDA status with `python scripts/check_install.py --check-cuda`

## 3) Custom module import problems

**Symptoms**

- `--custom_module_path` raises an import or attribute error
- the custom expert name collides with a built-in one
- the server starts but the custom expert never appears

**Likely causes**

- the file does not execute cleanly as a standalone Python module
- the module forgot to call `register_expert_class(...)`
- the registered name duplicates an existing expert class

**Recovery**

1. Make the custom file importable on its own.
2. Register the class with a unique expert name.
3. Make the sample input function match the expert's forward signature.
4. Try the custom expert through `background_server(...)` before moving to the CLI.

## 4) Identity / restart problems

**Symptoms**

- `identity_path` appears to generate a new peer ID every restart
- two servers claim the same identity

**Likely causes**

- the identity file path is shared between live servers
- the path is missing or not writable

**Recovery**

- dedicate one identity file per server when you need a stable peer ID
- restart the same server with the same file only when you intend to preserve the peer identity

## 5) Checkpoint confusion

**Symptoms**

- expert state does not survive a restart
- optimizer or scheduler values revert unexpectedly

**Likely causes**

- checkpointing was not enabled
- the checkpoint directory is not writable
- the restore path does not match the save path

**Recovery**

- confirm `checkpoint_dir` is set and writable
- verify the checkpoint directory contents after a save
- if you are using a helper test, compare the behavior with `tests/test_expert_backend.py`

## 6) Remote call errors or timeouts

**Symptoms**

- the client hangs during forward/backward
- remote calls fail after a long pause
- a router layer returns an empty output unexpectedly

**Likely causes**

- the server is overloaded or batch settings are too aggressive
- the expert selection timeout is too short for the current network
- the client and server disagree on the expected input shapes

**Recovery**

- lower the batch size or increase the timeout values
- verify the expert input shape against the server's registered sample input
- test one `RemoteExpert` first before moving to a routed MoE layer

## 7) When to stop

Stop local debugging and escalate when the issue depends on:

- a custom module you are not allowed to edit
- a network route you cannot make reachable
- a CUDA dependency mismatch on the host
- a missing checkpoint directory that lives outside the current workspace

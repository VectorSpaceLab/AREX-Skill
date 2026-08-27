# Disaggregated Deployment Troubleshooting

## Role startup fails

### Symptoms
- `run_service` exits before the role starts.
- The controller cannot create or contact the worker roles.
- A worker loop exits immediately with a transport or distributed error.

### Likely causes
- The config JSON is missing `disagg_mode` or has the wrong role map.
- `WORLD_SIZE`, `LOCAL_RANK`, or role ranks do not match the launch plan.
- The environment is missing `pyzmq`, RDMA-related packages, or another transport dependency.

### Recovery
- Re-check the topology reference and the config file.
- Confirm that each role is using the expected rank and port.
- Start with a single-node dry run before moving to multi-node.

## Port or bind failures

### Symptoms
- Address-in-use errors.
- The controller or worker never binds its socket.
- Health / metric probes never connect.

### Likely causes
- A stale process from a previous run is still alive.
- The launch script and config disagree about the port plan.

### Recovery
- Stop the stale process tree and retry.
- Re-run the planner helper to confirm the intended ports and role bindings.

## Mooncake / RDMA failures

### Symptoms
- Errors mention Mooncake, RDMA buffers, or handshake timeouts.
- The controller starts but request transfer never completes.

### Likely causes
- The environment is missing the expected transport support.
- The config points at a network interface or bootstrap address that does not exist on the machine.

### Recovery
- Verify `RDMA_IFACE`, `MOONCAKE_DEVICE_NAME`, and the bootstrap address.
- Use a local topology first.
- Keep `SYNC_COMM` or other transport shortcuts consistent across the roles.

## Request / workload failures

### Symptoms
- The controller reports no requests or the user stops too early.
- The load shape finishes before the model path is exercised.

### Likely causes
- The workload request count is too small.
- The user and controller disagree about the stage spec or request source.

### Recovery
- Re-read the workflow reference.
- Increase the request count only after the baseline sequence is working.

## What not to do

- Do not collapse a disaggregation transport failure into a generic inference failure.
- Do not use the HTTP server route to debug an RDMA / Mooncake issue.
- Do not assume the controller topology is correct just because the process started; confirm the role bindings and ports.

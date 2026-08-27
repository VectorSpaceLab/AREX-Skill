# Deployment troubleshooting

## Port already in use

### Symptoms
- The process exits with an address-in-use error.
- A retry appears to start but the new process never binds cleanly.

### Recovery
- Check which port the role expects from the deployment matrix.
- Stop stale processes before retrying.
- Keep separate logs per role so you can identify which process collided.

## PD master / worker registration failure

### Symptoms
- `prefill` or `decode` does not join the PD graph.
- The master starts, but the workers keep retrying or timing out.

### Likely causes
- The roles were started in the wrong order.
- `PD_MASTER_IP` or `PD_MASTER_PORT` does not match the master process.
- Proxy settings interfered with local traffic.
- The model path or GPU assignment differs between the roles.

### Recovery
- Re-check the startup order in the deployment matrix.
- Clear `http_proxy` and `https_proxy` for local traffic.
- Verify that the master is listening before the worker roles start.

## GPU assignment or topology mismatch

### Symptoms
- A role sees too few GPUs.
- The `tp` / `dp` / `visual_tp` / `visual_dp` plan does not match the host.

### Recovery
- Recount the available GPUs.
- Revisit the topology choice before increasing the tensor or data parallel
  degree.
- Keep prefill and decode GPU assignments distinct when the topology expects
  distinct device groups.

## RDMA / UCX / NIXL issues

### Symptoms
- The launch path hangs or throws transport errors when split processes try to
  communicate.

### Likely causes
- `UCX_NET_DEVICES` is wrong for the host.
- `nvidia_peermem` is not loaded when the path expects it.
- The transport mode is set to a backend the host cannot use.

### Recovery
- Verify the host-specific transport requirements before retrying.
- Keep the transport choice explicit in the launch log.
- If the host does not provide the required transport, narrow the topology
  claim or switch to a supported path.

## MPS caveats

### Symptoms
- The deployment works but performs much worse than expected.

### Likely causes
- MPS is disabled in a topology that benefits from it.
- Another process is already occupying the GPUs.

### Recovery
- Treat MPS as a performance optimization, not a correctness requirement.
- Record whether MPS was enabled when comparing runs.

## Shared memory or cache issues

### Symptoms
- Warnings about shared memory, cache allocation, or cache reuse.

### Likely causes
- The cache or shared-memory budget is too small.
- The multimodal worker and the main server disagree on cache settings.

### Recovery
- Confirm the cache-related flags and the model's modality requirements.
- Check whether the deployment path needs a larger shared-memory budget.

## Successful but wrong topology

### Symptoms
- The service is up, but the chosen role split does not match the user's
  intended workflow.

### Recovery
- Re-read the deployment matrix.
- Confirm whether the user wants a single server, split PD topology, or a
  multimodal worker path.

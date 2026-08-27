# Deployment notes

Use this reference for how Xinference is usually deployed and what each mode
needs before it can serve traffic safely.

## Local deployment

- The default host binding is loopback. Use a public host binding only when you
  intentionally want remote access.
- Persist `XINFERENCE_HOME` if you want logs, auth state, caches, and launch
  history to survive restart.
- If you provide a custom Web UI export, set `XINFERENCE_FRONTEND_DIST_DIR` to
  the directory that contains the built static files.
- Authentication is enabled by default even in local mode; create the first
  admin account before sharing the endpoint broadly.

## Docker image

Prerequisites:
- NVIDIA Container Toolkit for GPU acceleration.
- A host CUDA/driver stack compatible with the image family you chose.
- Enough shared memory for multi-GPU or heavy model backends.

Operational rules:
- Publish the API/UI port from the container to the host.
- Bind the service to all interfaces inside the container if the host should
  reach it.
- Mount `XINFERENCE_HOME` to a host directory if you want durable state.
- Mount the host Hugging Face and ModelScope caches if you want offline reuse
  of downloaded model files.
- Increase shared memory when the backend or model family needs it.

## Docker Compose

Docker Compose is the easiest path for a single-node deployment with persistent
state.

Keep in mind:
- Environment overrides belong in the Compose environment section or a local
  `.env` file.
- `XINFERENCE_HOME_DIR`, `XINFERENCE_HF_CACHE_DIR`, and
  `XINFERENCE_MODELSCOPE_CACHE_DIR` should point at durable host paths when you
  want reused caches.
- Offline deployments need a private wheel source or mirror so per-model
  virtual environments can be created without network access.
- Authentication is still enabled by default; set
  `XINFERENCE_AUTH_ADVANCED=false` only when the deployment is intentionally
  open.

Typical Compose concerns:
- GPU hosts need the same NVIDIA prerequisites as the raw container image.
- CPU-only hosts should use the CPU variant of the image.
- Shared-memory size matters for large-model inference.
- The built-in private PyPI mirror is an external prerequisite for offline
  model installs, not a replacement for model caches.

## Kubernetes

Use Kubernetes when you need scheduling, node isolation, or multiple workers.

Minimum prerequisites:
- A working Kubernetes cluster.
- GPU support enabled if the workload needs acceleration.
- Helm installed and configured.

Common Helm-level knobs:
- Model source selection.
- Image selection.
- Worker count and GPUs per worker.
- Storage and cache persistence through your cluster storage class.

For more complex deployments, prefer your own values file rather than a long
chain of ad hoc overrides.

## External service prerequisites

Some deployments depend on more than Xinference itself:

- OIDC provider for single sign-on.
- Elasticsearch when audit search should query centralized logs.
- Hugging Face credentials for gated repositories.
- ModelScope or CSGHub access when those are your model sources.
- Private PyPI or internet access when per-model virtual environments install
  extra engine packages at launch time.

Treat these as deployment prerequisites, not as Xinference runtime defaults.

## Exposure checklist

- Decide whether the service is private, internal-only, or public.
- Prefer ingress, reverse proxy, or service mesh controls over direct exposure.
- Use IP restrictions and trusted proxy settings when the network boundary is
  not enough.
- Keep the Web UI export, auth store, logs, and caches persistent if the
  deployment is expected to survive restarts.

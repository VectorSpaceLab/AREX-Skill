# Build and Deployment

## Choose the smallest adequate path

| Goal | Preferred path | When to avoid |
| --- | --- | --- |
| Use released Triton with common backends | Pull the matching NGC server container | Avoid when custom backend/core changes are required. |
| Reduce image size using released components | Compose a custom image from released min/full images | Avoid if the component is not available in release artifacts or needs custom compilation. |
| Build custom core/backend/features | Source build in an approved build host | Avoid for routine deployment; it is slow and disk-heavy. |
| Deploy to Kubernetes/cloud | Use organization-approved manifests/Helm/operator/platform recipes | Avoid running cloud commands without credentials and cluster approval. |

## Dry-run build planning

Use the bundled build planner to produce safe command templates. It does not run Docker or build anything:

```bash
python3 scripts/plan_triton_build.py --mode compose --backend onnxruntime --repoagent checksum --container-version 26.07 --json
python3 scripts/plan_triton_build.py --mode source-build --backend onnxruntime --enable-gpu --json
```

Run the printed command only in a Triton source tree selected by the user for that build, and only after confirming disk, network, compiler, Docker, and GPU/CUDA requirements.

## Deployment checklist

- Pin a Triton container tag and backend/container variant, especially for LLM backends.
- Mount model repositories from a controlled location; prefer read-only mounts except during explicit management/update workflows.
- Expose only required ports; protect repository-control, statistics, trace, logging, shared-memory, and model-config APIs from untrusted clients.
- Configure readiness/liveness separately. Decide whether strict readiness should fail the whole service when one model is unavailable.
- Configure metrics scraping for `:8002/metrics` if Prometheus metrics are enabled.
- For GPU deployments, verify node driver, NVIDIA Container Toolkit or device plugin, CUDA compatibility, and memory capacity for the selected models.

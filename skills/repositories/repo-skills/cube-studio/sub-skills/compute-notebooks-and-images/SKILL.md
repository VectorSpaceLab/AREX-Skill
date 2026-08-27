---
name: compute-notebooks-and-images
description: "Route CubeStudio notebook, registry, image catalog, GPU resource,
  and monitoring questions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Compute notebooks and images

Use this sub-skill for CubeStudio questions about:
- project, resource group, and cluster placement
- notebook / IDE lifecycle and URLs
- Docker image registry management and online image builds
- notebook, Theia, Jupyter, and GPU image catalogs
- GPU resource strings, selector switching, and monitoring / resource views

Do not use this sub-skill for:
- platform install, Kubernetes bring-up, or offline cluster setup → `deploy-and-operate`
- pipeline or job-template authoring → `pipelines-and-job-templates`
- serving / inference image deployment → `serving-aihub-and-llm`
- generic backend or FAB customization → `backend-and-configuration`

Read first:
- [`references/resource-and-kubernetes-api.md`](./references/resource-and-kubernetes-api.md)
- [`references/notebook-workflows.md`](./references/notebook-workflows.md)
- [`references/image-catalog.md`](./references/image-catalog.md)
- [`references/troubleshooting.md`](./references/troubleshooting.md)
- [`scripts/parse_resource_gpu.py`](./scripts/parse_resource_gpu.py)

Router notes:
- notebook placement is driven by project / org / cluster config, `resource_gpu`, and selector labels
- `resource_gpu` strings are authoritative only when they pass the bundled parser
- notebook / IDE lifecycle questions map to create, open, reset, renew, stop, and save behavior
- image registry questions map to `Repository`, `Images`, `Docker`, and `NOTEBOOK_IMAGES`
- monitoring questions map to Grafana, Prometheus, `total_resource`, and GPU plugin caveats

When a request needs platform installation or image families outside notebooks, route it to the sibling sub-skill instead of expanding this one.
Do not require the original checkout in answers; use the bundled references and helper script only.

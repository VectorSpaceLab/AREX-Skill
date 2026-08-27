---
name: deploy-and-operate
description: "Operate CubeStudio deployment workflows safely: Docker Compose
  development, Kubernetes installation sequencing, offline/private registry
  preparation, manifest inventory, overlays, and triage."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# deploy-and-operate

Use this sub-skill when the task is about installing, packaging, deploying, upgrading, inventorying, or triaging CubeStudio runtime infrastructure.

## Read when

- Preparing local Docker Compose development or debugging a local compose stack.
- Planning a production Kubernetes installation, upgrade, or manifest review.
- Moving CubeStudio to an offline network or private registry.
- Locating where deployment overlays, kubeconfigs, image names, namespaces, PVCs, and secrets belong.
- Building a read-only manifest/image inventory before an operator runs Docker or Kubernetes commands.

## Start here

1. For local development, read [references/deployment-guide.md](references/deployment-guide.md).
2. For Kubernetes ordering, namespaces, CRDs, PVCs, and component roles, read [references/kubernetes-operations.md](references/kubernetes-operations.md).
3. For offline or private-registry work, read [references/offline-and-private-registry.md](references/offline-and-private-registry.md).
4. For symptoms and triage paths, read [references/troubleshooting.md](references/troubleshooting.md).
5. Before applying or rebuilding anything, run the bundled safe helper on the candidate checkout or manifest directory:

   ```bash
   python scripts/cube_studio_manifest_inventory.py --help
   python scripts/cube_studio_manifest_inventory.py /path/to/cube-studio-or-manifests
   ```

## Safety contract

This sub-skill may recommend operator procedures, but do not run cluster- or host-mutating commands until the operator has reviewed the inventory, target cluster, credentials, registry, storage, and rollback plan. Treat CubeStudio's original install scripts as examples to inspect, not as generic one-shot installers.

Never run these blindly: `start.sh`, `start-with-kubesphere.sh`, `uninstall.sh`, `init_node.sh`, `install_docker.sh`, Rancher reset scripts, image pull/save/push scripts, Docker builds, image pulls, `kubectl apply/delete/create/patch/label`, or package install/build commands.

## Route elsewhere

- Backend configuration, FAB app lifecycle, auth, model/view registration, Celery internals, and frontend source customization: `backend-and-configuration`.
- Notebook image catalog, online image builds, resource selectors, GPU resource strings, and project/resource management: `compute-notebooks-and-images`.
- Pipeline DAGs, Argo workflow generation, job-template authoring, NNI/HPO templates: `pipelines-and-job-templates`.
- Datasets, SQLLab, metadata, dimensions, ETL data workflows: `data-metadata-and-sqllab`.
- Internal services, inference services, AIHub, chat/LLM gateways, service canary/shadow details: `serving-aihub-and-llm`.

## Expected operating output

Return an operator-ready plan with:

- selected path: local compose, Kubernetes, offline/private registry, or triage;
- manifest and image inventory results;
- files/overlays to edit and the order to stage them;
- commands that remain read-only versus commands that require explicit operator approval;
- expected observations and rollback/triage checkpoints;
- sibling sub-skill routes for non-deployment work.

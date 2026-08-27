# Offline and private-registry operations

CubeStudio supports private and fully offline deployments, but the source scripts are intentionally side-effectful: they generate shell scripts, pull/tag/push/save/load images, edit host runtime settings, and mutate cluster resources. Use this reference and the safe inventory helper before running any image or cluster command.

## First inventory the target bundle

Run a read-only inventory against the checkout or manifest bundle that will be deployed:

```bash
python scripts/cube_studio_manifest_inventory.py /path/to/cube-studio-or-install/kubernetes --format text
python scripts/cube_studio_manifest_inventory.py /path/to/cube-studio-or-install/kubernetes --format json
```

Use the output to build three lists:

1. Kubernetes and Compose images found in manifests.
2. Images embedded in config files or generated from seed catalogs/job templates.
3. Shell scripts that would pull/push/build/save/load images or mutate hosts/clusters.

The repository's `all_image.py` covers more than manifest image fields: it combines Kubernetes core images, dashboard images, GPU plugin/monitoring images, Prometheus/Grafana images, Istio, Volcano, Argo, CubeStudio web images, notebook/base images, internal-service/inference images, user base images, job-template images from seed JSON, and example images from initialization JSON. Treat the helper's manifest inventory as a safe baseline, then compare it with the source image generator before the final registry mirror.

## Fully offline workflow

The documented offline path assumes one machine can connect to the public internet and the deployment machines cannot.

### On a connected staging machine

Prepare an offline package:

- `kubectl` binary appropriate for the deployment architecture/version.
- Harbor offline installer if using self-hosted registry.
- Optional model and demo data archives required by built-in inference, AIHub, or pipeline examples.
- Image-transfer scripts generated after setting the internal registry in the image generator.

Do not rely on public URLs during the actual offline deployment. The documented examples download model files, datasets, Harbor, and kubectl from public endpoints; in a hardened environment those must be mirrored and checksummed by the operator.

### On the offline network

1. Install or stage `kubectl` from the offline package.
2. Install an internal registry such as Harbor and create at least separate projects/namespaces for Rancher/base cluster images and CubeStudio images.
3. Configure every node's Docker/containerd runtime to trust or verify the internal registry. For HTTP or self-signed registries, the operator must deliberately configure insecure registries or certificates.
4. Copy optional offline model/data archives into a stable user workspace, conventionally under the admin workspace below `/data/k8s/kubeflow/pipeline/workspace/admin/`.
5. Transfer Rancher/Kubernetes images and CubeStudio images using reviewed scripts or a controlled registry replication process.
6. Rewrite CubeStudio deployment overlays and config fields to the internal registry and offline paths.
7. Deploy Kubernetes and CubeStudio using the normal ordered Kubernetes plan, with all public downloads disabled.

## Image transfer script model

The source image generator writes scripts with these purposes:

| Script style | Intended environment | Side effects |
| --- | --- | --- |
| `pull_images.sh` | Internet-connected machine or non-offline node. | Pulls public images. |
| `push_harbor.sh` | Internet-connected staging machine with access to internal registry. | Logs into registry, pulls public images, tags them with internal registry names, pushes them. |
| `pull_harbor.sh` | Offline deployment nodes with registry access. | Logs into internal registry, pulls internal images, tags them back to expected public names for selected bootstrap images. |
| `image_save.sh` | Connected staging machine. | Pulls public images and writes compressed image tarballs. |
| `image_load.sh` | Offline deployment nodes. | Loads compressed image tarballs into local runtime. |
| Rancher image scripts | Rancher/Kubernetes bootstrap path. | Similar pull/push/save/load behavior for Rancher/RKE/RKE2 images. |

Review and edit registry hostnames, credentials, image names, and concurrency before running generated scripts. Generated scripts often contain backgrounded operations and `wait`, so failures can be interleaved or easy to miss.

## Private registry rewrite checklist

When migrating CubeStudio images to an internal registry, inspect and update these surfaces:

### Kustomize image names

In the cube overlay kustomization, rewrite backend and frontend image `newName` and `newTag` to internal registry names/tags:

- backend: `kubeflow-dashboard`
- frontend: `kubeflow-dashboard-frontend`

Also inspect all selected Kubernetes manifests for literal images, including MySQL, Redis, dashboard, Argo, MinIO, Prometheus, Grafana, Istio, Volcano, GPU plugin, DCGM exporter, training operator, and utility images.

### Runtime config image fields

In the mounted `config.py` overlay, update at least:

- `REPOSITORY_ORG`
- `PUSH_REPOSITORY_ORG`
- `USER_IMAGE`
- `NOTEBOOK_IMAGES`
- `DOCKER_IMAGES`
- `NERDCTL_IMAGES`
- `NNI_IMAGES`
- `WAIT_POD_IMAGES`
- `INFERNENCE_IMAGES`
- any service, template, AIHub, or example image fields selected for the deployment

Detailed notebook image catalog and training/serving image choices belong to sibling sub-skills, but deployment operators must ensure the registry values they depend on are reachable.

### Secrets and namespaces

- Recreate `hubsecret` or equivalent image pull secrets with internal registry credentials in every namespace where pods pull images: `infra`, `pipeline`, `automl`, `jupyter`, `service`, `aihub`, plus any system namespace that needs private images.
- Confirm secret type is Docker registry auth and points to the internal registry endpoint.
- Avoid leaving placeholder username/password values from examples.

### Host/runtime registry trust

- Docker: configure mirrors/insecure registries or trusted CA, then restart Docker in a planned maintenance window.
- containerd/RKE2/K3S: configure registry mirrors and certificate trust in the runtime-specific registry config, then restart runtime components deliberately.
- Rancher-managed clusters: account for Rancher agent and internal containerd behavior separately from host Docker.

### Offline data and command rewrites

Built-in examples may use `wget` to fetch datasets/models at runtime. In a fully offline deployment, rewrite those pipeline or service commands to copy from mounted offline data instead, for example from an admin workspace or PVC-mounted offline directory. Keep the data path consistent with CubeStudio's workspace conventions.

## Disable public downloads in install scripts

Before adapting the deployment scripts for offline use:

- Remove or comment public `wget`/`curl` downloads of kubectl or other binaries.
- Replace image pull scripts with internal registry pulls or local image loads.
- Replace public package-source setup with internal mirrors if host/container package installs are unavoidable.
- Do not run Docker builds that fetch package managers, pip, npm, apt, yum, or model files unless all sources are mirrored and approved.

## Internal egress/proxy pattern

For networks with one egress/proxy host, the docs describe:

- running an HTTP/HTTPS proxy such as nginx on the egress host;
- mapping common public package/model/registry domains to that host in `/etc/hosts` on internal machines;
- adding CoreDNS `hosts` mappings for pods;
- configuring pip, apt, and yum to use reachable mirrors.

This can reduce registry mirroring but expands operational risk: DNS, TLS, package provenance, and caching behavior must be controlled. Do not run the sample proxy container or iptables rewrites without network-owner approval.

## Rancher-specific notes

CubeStudio includes Rancher deployment guidance and image lists. Rancher is useful for building or operating the Kubernetes cluster, but it adds its own image set, bootstrap state, certificates, clock-sensitivity, and recovery procedures.

High-risk Rancher operations include:

- `reset_docker.sh`, `reset_rancher.sh`, RKE2 reset scripts, and node cleanup scripts;
- cluster creation commands copied from Rancher UI;
- editing kubelet extra args and bind mounts;
- changing service/pod CIDRs;
- manipulating Rancher server containers, certificates, or cluster registration tokens.

Use Rancher docs as operator evidence, not as a CubeStudio application-level action. If the task is only to deploy CubeStudio onto an already prepared cluster, do not recreate Rancher or Kubernetes.

## Offline readiness review

Before execution, the handoff should include:

- internal registry endpoint(s), credentials owner, and TLS/insecure policy;
- image inventory and rewrite map from public name to internal name;
- which scripts were generated, inspected, edited, and approved;
- namespaces requiring image pull secrets;
- offline data/model archive locations and command rewrites;
- removal of public downloads from install paths;
- CoreDNS/host/proxy changes, if any;
- test plan for read-only inventory, image availability, PVC readiness, and staged rollout;
- rollback plan for registry names, secrets, configmaps, and deployments.

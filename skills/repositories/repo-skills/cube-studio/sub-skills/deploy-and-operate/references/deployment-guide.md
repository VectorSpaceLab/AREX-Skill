# CubeStudio deployment guide

This reference distills CubeStudio's deployment evidence into a self-contained operating guide. Path names such as `install/docker/docker-compose.yml` identify conventional files in a CubeStudio checkout or release bundle; this skill does not require the original checkout to be present unless you are deliberately inventorying or operating one.

## Deployment modes owned here

| Mode | Use when | Primary operator concerns |
| --- | --- | --- |
| Local Docker Compose development | Backend developers need a local MySQL/Redis/backend/frontend stack and may connect to an existing Kubernetes dev cluster. | Compose service health, mounted overlays, entrypoint lifecycle, port conflicts, frontend/static volumes, optional kubeconfig. |
| Production Kubernetes | Operators deploy the full platform onto a prepared Kubernetes cluster. | Namespace and secret bootstrap, node labels, PVC/storage readiness, CRD ordering, component dependencies, overlay placement, ingress. |
| Offline/private registry | The cluster cannot pull from the public internet or must use an internal registry. | Image inventory, registry rewrite, hub secrets, offline data/model placement, proxy/CoreDNS fixes, generated image-transfer scripts. |
| Operations triage | A running or partially deployed platform fails. | Distinguish app config, DB/Redis, PVC, CRD, image pull, node label, ingress, GPU plugin, and offline-registry failures. |

Route workflow-specific platform use to sibling sub-skills. For example, notebook image catalog and resource selectors belong to `compute-notebooks-and-images`; template and Argo workflow authoring belongs to `pipelines-and-job-templates`; inference service behavior belongs to `serving-aihub-and-llm`.

## Local Docker Compose development

CubeStudio's local compose stack is a development scaffold, not the production topology. The compose file defines four active services:

| Service | Image / role | Important details |
| --- | --- | --- |
| `redis` | `ccr.ccs.tencentyun.com/cube-studio/redis:7.4` | Password defaults to `admin`; port `6379` is published. |
| `mysql` | `mysql:8.0.32` | Creates database `kubeflow`; root password defaults to `admin`; port `3306` is published; data persists in a local `data/mysql` volume; a repo-provided MySQL config is mounted. The `myapp` service waits for this service's healthcheck. |
| `myapp` | `ccr.ccs.tencentyun.com/cube-studio/kubeflow-dashboard:2026.06.01` | Backend container. Defaults to `STAGE=dev`, `ENVIRONMENT=DEV`, MySQL URL `mysql+pymysql://root:admin@mysql:3306/kubeflow?charset=utf8mb4`, and Redis host `redis`. It mounts source code, job templates, optional AIHub material, data storage, entrypoint, `config.py`, `project.py`, and kubeconfig. |
| `frontend` | `ccr.ccs.tencentyun.com/cube-studio/kubeflow-dashboard-frontend:2026.06.01` | Nginx frontend on host port `80`; depends on backend start; mounts static/frontend directories and nginx config. |

### Safe local preflight

Before any compose run, inventory the target directory without starting containers:

```bash
python scripts/cube_studio_manifest_inventory.py /path/to/cube-studio-or-install/docker
```

Then manually review:

- host port conflicts for `80`, `3306`, and `6379`;
- whether `install/docker/config.py`, `install/docker/project.py`, `install/docker/entrypoint.sh`, and frontend nginx config exist in the release being operated;
- whether mounted storage targets should be bind mounts, volumes, or adjusted for the operator's machine;
- whether a kubeconfig is needed. CubeStudio expects per-environment kubeconfig files under a mounted `kubeconfig` directory named like `<environment>-kubeconfig`, for example `dev-kubeconfig` when `ENVIRONMENT=DEV`.

Do not use local compose as proof that Kubernetes deployment is valid. It verifies only local app boot, DB/Redis wiring, and frontend/backend proxying.

## Container entrypoint lifecycle

Both Docker Compose and Kubernetes mount or bake an entrypoint with the same lifecycle:

1. Recreate static symlinks:
   - `/home/myapp/myapp/static/mnt` -> `/data/k8s/kubeflow/pipeline/workspace`
   - `/home/myapp/myapp/static/dataset` -> `/data/k8s/kubeflow/dataset`
   - `/home/myapp/myapp/static/aihub` -> `/cube-studio/aihub`
   - `/home/myapp/myapp/static/global` -> `/data/k8s/kubeflow/global`
2. Set `FLASK_APP=myapp:app`.
3. Run database creation and migration:
   - `python myapp/create_db.py`
   - `myapp db upgrade`
4. Create or refresh the default admin account and FAB permissions:
   - username `admin`, password `admin`, email `admin@tencent.com`
   - `myapp init` seeds roles, permissions, menus, and platform catalogs.
5. Branch by `STAGE`:
   - `build`: runs frontend/package builds inside the backend container. This requires npm/yarn and network/cache availability; do not run during safe inspection.
   - `dev`: runs `python myapp/check_tables.py` and `python myapp/run.py`.
   - `prod`: runs `python myapp/check_tables.py` then gunicorn on port `80` with gevent workers.
   - other value: prints `myapp --help`.

Implications:

- First boot is not a passive health check; it mutates DB schema, creates users/roles, and writes static symlinks.
- Repeated boot can surface idempotency or permission issues around the admin user, migrations, static symlinks, and mounted directories.
- If the backend starts but login/frontend fails, inspect the stage branch, DB migration result, frontend static volume, Nginx config, and cookie/proxy path before changing application code.

## Configuration and project overlays

The checkout's root `myapp/config.py` and `myapp/project.py` can be empty placeholders. Runtime deployments rely on overlay files:

| Target mode | Overlay files | Runtime mount/placement |
| --- | --- | --- |
| Docker Compose | `install/docker/config.py`, `install/docker/project.py`, `install/docker/entrypoint.sh` | mounted into `/home/myapp/myapp/config.py`, `/home/myapp/myapp/project.py`, and `/entrypoint.sh` inside the backend container. |
| Kubernetes | `install/kubernetes/cube/overlays/config/config.py`, `project.py`, `entrypoint.sh` | collected by a `kubeflow-dashboard-config` ConfigMap and mounted into the backend, worker, scheduler, and watch pods. |

The mounted `project.py` is the active auth/login overlay, not a placeholder. In the source evidence it defines the `Myauthdbview` login view, token/username login endpoints, auto-registration behavior, and first-login workspace bootstrap. If login, registration, or seeded example workspace behavior is wrong, check the mounted `project.py` before editing core app code.

Important overlay keys and conventions:

- `ENVIRONMENT` selects the active cluster entry from `CLUSTERS` and normally defaults to `DEV` / `dev`.
- Core namespaces default to `pipeline`, `automl`, `jupyter`, `service`, and `aihub` for user workloads, plus `infra` for CubeStudio control-plane components.
- `HUBSECRET` defaults to `['hubsecret']`; image pull secrets must exist in workload namespaces.
- Registry/image fields include `REPOSITORY_ORG`, `PUSH_REPOSITORY_ORG`, `USER_IMAGE`, `NOTEBOOK_IMAGES`, `DOCKER_IMAGES`, `NERDCTL_IMAGES`, `NNI_IMAGES`, `WAIT_POD_IMAGES`, and `INFERNENCE_IMAGES`.
- Monitoring and navigation fields include `PROMETHEUS`, Grafana paths, `K8S_DASHBOARD_CLUSTER`, `K8S_DASHBOARD_USER`, `SERVICE_DOMAIN`, and `SERVICE_EXTERNAL_IP`.
- `CLUSTERS` entries name kubeconfig paths such as `/home/myapp/kubeconfig/dev-kubeconfig` and can include service domain and host settings.

When changing deployment behavior, edit the overlay that is actually mounted in the target mode. Editing an empty placeholder in the source package may have no effect.

## Image build and pull evidence

The repository includes Dockerfiles for:

- backend base image: Ubuntu 22.04, Python 3.9, supervisor, operations tools, Node/Yarn, fonts/locales, and Python requirements;
- backend production image: copies `myapp`, static frontend assets, AIHub material, and `entrypoint.sh` onto the base image;
- frontend image: Nginx serving `/frontend` and `/static` material with CubeStudio nginx config.

These files contain package installs, network downloads, and large build steps. Treat them as image recipe evidence. Do not run `docker build`, `docker pull`, `npm install`, `npm run build`, or `yarn` during read-only skill verification or preflight inventory.

## What not to run blindly

- The compose stack: starts services, writes volumes, opens ports, runs DB migrations, and creates an admin account.
- The entrypoint: mutates mounted filesystem and DB.
- Dockerfiles and frontend build commands: require network/cache and can take a long time.
- Kubernetes install scripts: mutate nodes, namespaces, secrets, RBAC, CRDs, PVCs, configmaps, deployments, and ingress.
- Image-transfer scripts generated by `all_image.py`: pull, tag, save, load, push, and login to registries.

Use the bundled manifest inventory helper first, then decide which operator-approved commands remain necessary.

# Platform overview

CubeStudio is a cloud-native AI platform that combines MLOps, MaaS, notebook development, pipeline orchestration, model serving, AIHub catalogs, SQLLab-style data access, and Kubernetes-based runtime management.

## Top-level repository areas

| Area | Main evidence | What it represents |
| --- | --- | --- |
| `myapp/` | Flask AppBuilder backend, models, views, tasks, utilities | Core platform application and UI/API layer |
| `install/docker/` | Compose stack, backend container entrypoint, runtime config overlays | Local development and production container boot path |
| `install/kubernetes/` | Cluster install scripts, manifests, offline/private-registry notes | Kubernetes deployment and operations path |
| `job-template/` | Template families, launchers, and registration docs | Reusable task templates for pipeline execution |
| `images/` | Notebook, GPU, serving, and tool image recipes | Platform image catalog and build guidance |
| `myapp/init/` | Seed JSON catalogs | Default projects, templates, images, pipelines, services, inference, AIHub, and chat examples |
| `myapp/frontend/`, `myapp/vision/`, `myapp/visionPlus/` | Frontend packages and route proxies | UI bundles and pipeline editor frontends |

## Major platform surfaces

- **Backend / UI**: Flask AppBuilder app, auth, permissions, views, REST APIs, and request hooks.
- **Notebook and development**: project groups, notebook services, image registry, GPU selectors, and monitoring links.
- **Pipelines**: job templates, DAG JSON, workflow generation, task history, and NNI/HPO templates.
- **Data**: datasets, metadata tables, dimension tables, SQLLab queries, ETL pipelines, and data movement templates.
- **Serving**: generic services, inference services, trained-model deployment, AIHub cards, and chat scenarios.
- **Infrastructure**: Docker Compose, Kubernetes install order, offline registry prep, and cluster add-ons such as GPU plugins, Prometheus, Istio, Argo, and Volcano.

## Runtime overlay model

The repository's checked-in `myapp/config.py` and `myapp/project.py` are placeholders. Real runtime settings are injected by the Docker and Kubernetes overlay mechanism. This is a core CubeStudio behavior, not a bug in the generated skill.

## Route map to the sub-skills

- `deploy-and-operate` for container, cluster, and offline deployment work
- `backend-and-configuration` for app startup, auth, RBAC, and backend customization
- `compute-notebooks-and-images` for notebooks, image catalog, and GPU resource routing
- `pipelines-and-job-templates` for task templates, DAGs, Argo workflows, and NNI/HPO
- `data-metadata-and-sqllab` for datasets, metadata, SQLLab, and ETL
- `serving-aihub-and-llm` for model serving, AIHub, chat, and gateway behavior

## Common task families

- "How do I deploy CubeStudio locally?"
- "Why does my notebook land on the wrong node selector?"
- "How does a job template become a pipeline task?"
- "Why does SQLLab reject this engine or URI?"
- "Which service type should I use for a TensorFlow or TorchServe model?"
- "How do I read or edit the AIHub / chat catalog?"

Each of those questions should be routed to the specific sub-skill above rather than answered from the root alone.

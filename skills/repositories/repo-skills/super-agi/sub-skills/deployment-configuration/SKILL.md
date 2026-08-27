---
name: deployment-configuration
description: "Guides SuperAGI Docker, local runtime, configuration, migrations,
  GUI proxy, and optional GPU/local LLM deployment tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SuperAGI Deployment and Configuration

Use this sub-skill when the task asks how to install, configure, start, debug,
or choose between SuperAGI runtime modes. Prefer static checks and config
validation before starting services.

## Read First

- [references/configuration.md](references/configuration.md) for `config.yaml`,
  environment overrides, credential placeholders, and service hostnames.
- [references/docker-stack.md](references/docker-stack.md) for Docker Compose
  service topology, default vs GPU deployment, startup order, and migrations.
- [references/local-runtime.md](references/local-runtime.md) for non-Docker
  launchers and why they are side-effectful.
- [references/troubleshooting.md](references/troubleshooting.md) for runtime,
  Docker, DB/Redis, GUI, NLTK, and GPU/local LLM failures.
- [scripts/check_compose_files.py](scripts/check_compose_files.py) to statically
  inspect a user's compose files without running containers.

## Main Decisions

1. **Cloud vs local:** Cloud use only needs provider/API keys in the hosted UI.
   Local use needs a checkout, config, Docker or Python dependencies, database,
   Redis, backend, worker, GUI, and proxy.
2. **Docker vs host-local:** Prefer Docker Compose for ordinary local operation
   because the repo's Dockerfiles encode Python 3.10, system packages, NLTK
   downloads, entrypoint order, and service hostnames.
3. **Default vs GPU Compose:** Use the GPU compose path only when the user
   explicitly needs local LLM/GPU support and has NVIDIA Docker runtime ready.
   Ordinary OpenAI/hosted-provider workflows do not require CUDA.
4. **Service startup authorization:** Starting the stack can build images,
   download Python/npm packages and NLTK data, run migrations, create volumes,
   and start long-running services. Ask/confirm unless the downstream task
   clearly authorizes this.

## Safe Workflow

1. Confirm a target checkout has `config_template.yaml`, `docker-compose.yaml`,
   `main.py`, and `superagi/`.
2. Create or inspect `config.yaml`. Run the root config checker before using
   real credentials or starting services.
3. Use the compose checker here to verify expected services and optional GPU
   reservations.
4. If starting the default stack is authorized, ensure Docker/Compose is
   available, then use the checkout's default compose file. Expect public GUI
   access through the proxy on port `3000` and backend app startup on port
   `8001` inside the stack.
5. If using GPU/local LLM, read the GPU notes in `docker-stack.md` first; do not
   treat visible host GPUs as proof that Docker GPU passthrough works.

## Boundary Notes

- Endpoint semantics, auth, webhooks, and SQLAlchemy models belong to
  `api-service`.
- Agent execution, workflow seeds, prompt parsing, and Celery job behavior
  belong to `agents-workflows`.
- Toolkit downloads and dependency installer behavior belong to
  `toolkits-integrations`.
- Provider keys, resources, and vector stores belong to
  `models-resources-vector`.

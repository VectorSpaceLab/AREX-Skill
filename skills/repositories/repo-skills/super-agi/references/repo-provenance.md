# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a SuperAGI checkout.
If the current repo commit, dirty state, package metadata, or major evidence
paths differ from this snapshot, run `refresh-repo-skill` before relying on
fine-grained API or configuration claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T14:44:10Z",
  "repository": {
    "name": "SuperAGI",
    "remote_url": "https://github.com/TransformerOptimus/SuperAGI.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c3c1982e7bd6a11cfed53c5a193ea502f924b1b6",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["superagi"]
    }
  ],
  "evidence": {
    "source_roots": ["superagi"],
    "docs": ["README.MD", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md"],
    "configs": ["config_template.yaml", "alembic.ini", "docker-compose.yaml", "docker-compose-gpu.yml", "docker-compose-dev.yaml", "docker-compose.image.example.yaml"],
    "deployment": ["Dockerfile", "Dockerfile-gpu", "DockerfileCelery", "DockerfileRedis", "entrypoint.sh", "entrypoint_celery.sh", "run.sh", "run.bat", "nginx/default.conf", "gui/package.json"],
    "api": ["main.py", "superagi/controllers", "superagi/controllers/api"],
    "agents": ["superagi/agent", "superagi/jobs", "superagi/worker.py"],
    "tools": ["superagi/tools", "superagi/helper/tool_helper.py", "superagi/tool_manager.py", "tools.json", "install_tool_dependencies.sh"],
    "models_resources_vector": ["superagi/llms", "superagi/image_llms", "superagi/resource_manager", "superagi/vector_store", "superagi/vector_embeddings"],
    "tests": ["tests/unit_tests", "tests/integration_tests"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and refresh it.
- If the checkout's dirty state differs materially from `dirty_paths`, refresh
  before relying on exact endpoint, model, or config guidance.
- If a future checkout adds Python package metadata (`pyproject.toml`,
  `setup.py`, or `setup.cfg`), public entry points, or a different source root,
  refresh the skill.
- If Docker, controller, workflow, toolkit, model-provider, resource, or vector
  store files move or change substantially, refresh the skill.

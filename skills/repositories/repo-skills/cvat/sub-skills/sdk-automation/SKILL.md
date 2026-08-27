---
name: sdk-automation
description: "Automate CVAT with the Python SDK, high-level repositories,
  authentication helpers, and safe task/project data scripts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CVAT SDK automation

Use this sub-skill when a task needs Python code against a CVAT server: login with a Personal Access Token or password, reuse CLI profiles, create/list/update/delete tasks or projects, upload local/remote/shared data, import/export annotations or datasets, download frames/previews/backups, use organization context, or fall back to generated low-level REST API wrappers.

## Route first

- Read `references/api-reference.md` for confirmed public classes, signatures, defaults, auth/profile helpers, and repository/entity relationships.
- Read `references/workflows.md` for copyable SDK patterns for task/project creation, frame download, import/export, backups, profile-compatible scripts, and low-level API fallback.
- Read `references/troubleshooting.md` when imports, authentication, server compatibility, background requests, SSL, organization context, or cache/filesystem behavior fail.
- Run or adapt `scripts/sdk_task_smoke_template.py` for a safe import/signature smoke by default, or for an explicit authenticated list/download workflow when the user supplies server credentials.

## Use SDK instead of CLI when

- The user needs branching logic, error handling, Python data structures, or integration into an ML pipeline.
- A workflow needs `Client`, `Task`, `Project`, `Job`, `Organization`, `Issue`, or generated API model objects.
- The task must compose CVAT calls with local data processing, model inference, or dataset conversion.
- Repeated background operations should use `wait_for_completion()` rather than shell polling.

Use `../cli-automation/SKILL.md` for terminal-only commands, `../dataset-ops/SKILL.md` for format and PyTorch dataset choices, `../auto-annotation/SKILL.md` for AA function protocols, and `../deployment-admin/SKILL.md` for starting or administering a CVAT service.

## Minimal install and import checks

```bash
pip install cvat-sdk
python - <<'PY'
from cvat_sdk import make_client, Client, Config
from cvat_sdk.core.proxies.tasks import ResourceType
print(Client, Config, [str(x) for x in ResourceType])
PY
```

Use extras only when needed:

```bash
pip install "cvat-sdk[masks]"     # mask encode/decode helpers needing NumPy
pip install "cvat-sdk[pytorch]"   # PyTorch dataset adapter and built-in torchvision AA functions
```

## Safe authentication defaults

- Prefer PAT authentication (`access_token=`) or CLI-compatible profiles rather than hard-coded passwords.
- If using password auth, pass it as a secret runtime value, not in code committed to a repository.
- Include the scheme in the server URL (`http://` or `https://`); SDK defaults and compatibility checks are stricter in recent releases.
- Set `organization_slug` or use `organization_context(slug)` when the workflow must operate inside an organization workspace.
- Treat `config.allow_unsupported_server=True` warnings seriously: SDK/server minor versions should normally match or be adjacent.

## Core pattern

```python
from cvat_sdk import make_client, models
from cvat_sdk.core.proxies.tasks import ResourceType

with make_client("https://cvat.example.com", access_token=token) as client:
    client.organization_slug = "team-slug"  # omit for personal workspace
    task = client.tasks.create_from_data(
        spec=models.TaskWriteRequest(
            name="demo",
            labels=[{"name": "car", "type": "rectangle"}],
        ),
        resource_type=ResourceType.LOCAL,
        resources=["image1.jpg", "image2.jpg"],
    )
    print(task.id, task.size)
```

Keep scripts explicit about side effects: creating tasks/projects, importing annotations, deleting resources, and downloading frames all mutate or read server state and need user-approved credentials/server targets.

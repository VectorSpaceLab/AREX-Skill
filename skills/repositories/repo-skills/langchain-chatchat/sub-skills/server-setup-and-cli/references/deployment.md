# Deployment Notes

## Deployment choices

| Mode | Best for | Cautions |
| --- | --- | --- |
| Pip install | Normal package users and simple local service deployments | Still needs provider and data-root configuration. |
| Source/editable install | Repository development or reproducing a specific checkout | Use the server package root; avoid treating root docs/lint pyproject as the runtime package. |
| Docker Compose | Fast separation of Chatchat and Xinference/provider services | Requires Docker, external images, network access, port planning, and often NVIDIA runtime for GPU providers. |
| Provider-managed service | Cloud or enterprise provider endpoints | API key/proxy/security configuration becomes the main risk. |

## Pip deployment skeleton

```bash
python -m venv .venv-chatchat
. .venv-chatchat/bin/activate
python -m pip install -U langchain-chatchat
export CHATCHAT_ROOT=/srv/chatchat-data
chatchat init
# edit generated YAML files
chatchat kb -r
chatchat start -a
```

Use platform-equivalent activation commands on Windows. The important invariant is that the `chatchat` executable and `python -c "import chatchat"` use the same environment.

## Source deployment skeleton

Use source/editable install when the user is developing the repository or must match a specific commit. Install the server package, not just the monorepo root metadata.

```bash
python -m pip install -e path/to/server-package
python -c "import chatchat, langchain_chatchat; print(chatchat.__version__)"
chatchat --help
```

For the SDK package, verify `import open_chatcaht` after installation.

## Docker/Xinference topology

The repository's Docker Compose evidence uses two services:

```text
xinference provider service  ->  exposes provider API, usually port 9997
chatchat service             ->  runs chatchat -a, API port 7861, WebUI port 8501
```

The Chatchat service depends on the provider having models loaded. Starting containers is not enough: load/register both an LLM and embedding model, then match names in Chatchat settings.

When GPU-backed Xinference is used, Docker must have NVIDIA Container Toolkit/runtime configured. Without GPU passthrough, a container can be "running" while model loading fails.

## Why AutoDL scripts are not bundled as runnable helpers

The repository includes AutoDL shell scripts for model download, provider startup, and process cleanup. They are intentionally not bundled as runtime scripts here because they:

- Assume hard-coded `/root` paths and named conda environments.
- Download models and hit provider endpoints.
- Kill existing Xinference/Chatchat processes.
- Write PID/log files in the current directory.
- Need user-specific model paths and GPU/runtime decisions.

Use them as conceptual evidence only. For a user deployment, rewrite commands to the user's paths and require explicit approval for downloads, process kills, or Docker/GPU changes.

## Production checklist

- Separate Chatchat, provider, and database/vector-store state directories.
- Bind hosts deliberately: local-only for development; public bind only behind appropriate firewall/proxy/auth.
- Make `public_host/public_port` match externally reachable API links if Chatchat generates document URLs.
- Persist `CHATCHAT_ROOT` across restarts.
- Persist provider model cache separately from Chatchat data.
- Confirm API docs load and `/v1/models` or provider health works before testing RAG.
- Back up knowledge-base content and DB before destructive KB commands.

# Environment and Cache Reference

## When to read

Read this when diagnosing installation, OpenLLM home directories, model dependency environments, or cleanup side effects.

## Home layout

OpenLLM uses `OPENLLM_HOME` when it is set; otherwise it defaults to a user home directory named `.openllm`.

Under that home, OpenLLM creates:

- `repos/` for cloned model repositories.
- `temp/` for temporary files.
- `venv/` for per-Bento virtual environments.
- `config.json` for repository aliases and defaults.

The default config contains two repository aliases:

- `default`: the main public OpenLLM model repository on `main`.
- `nightly`: the same public repository on `nightly`.

## Per-Bento venv lifecycle

When serving or running a model Bento, OpenLLM resolves a venv specification from the Bento's Python requirements and env variables:

1. Prefer `env/python/requirements.lock.txt` under the Bento.
2. Fall back to `env/python/requirements.txt`.
3. Read `image.python_version` from `bento.yaml`.
4. Include required Bento env values when computing the environment key.
5. Create a hashed directory under the OpenLLM venv cache.
6. Use `uv venv` and `uv pip install` to install `bentoml` and the Bento requirements.
7. Write a `DONE` marker after successful installation.

If a venv directory exists without `DONE`, OpenLLM deletes and recreates it.

## Cleanup commands

- `openllm clean model-cache` removes Hugging Face hub model cache.
- `openllm clean venvs` removes OpenLLM-created virtual environments.
- `openllm clean repos` removes cloned model repositories.
- `openllm clean configs` resets OpenLLM configuration.
- `openllm clean all` runs the cleanup group.

Treat cleanup as destructive. Inspect before deleting whenever the user may rely on cached models or repositories.

## Analytics opt-out

Use `--do-not-track` or set `BENTOML_DO_NOT_TRACK=true` to disable BentoML analytics tracking around OpenLLM CLI commands.

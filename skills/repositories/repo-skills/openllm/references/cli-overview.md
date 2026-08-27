# OpenLLM CLI Overview

## When to read

Read this for a root-level map of OpenLLM commands before jumping into a sub-skill.

## Command groups

| Command | Purpose | Owning sub-skill |
| --- | --- | --- |
| `openllm hello` | Interactive starter: updates model repository cache, detects local hardware, lets a user select a model/version/action, then routes to run/serve/deploy. | `local-serving` plus `model-repositories` |
| `openllm serve MODEL[:VERSION]` | Start a local BentoML server for a model and expose a browser chat UI plus OpenAI-compatible API. | `local-serving` |
| `openllm run [MODEL[:VERSION]]` | Start a local model server, wait for readiness, and run a terminal chat loop. | `local-serving` |
| `openllm deploy [MODEL[:VERSION]]` | Deploy an OpenLLM model Bento to BentoCloud, selecting an instance type when needed. | `cloud-deployment` |
| `openllm repo list/add/remove/update/default` | Manage the Git-backed model repository catalog used to discover Bentos. | `model-repositories` |
| `openllm model list/get` | List model Bentos and inspect one model's metadata. | `model-repositories` |
| `openllm clean model-cache/venvs/repos/configs/all` | Remove cached Hugging Face models, OpenLLM-created venvs, cloned repos, config, or all caches. Some commands are destructive. | `environment-maintenance` |

## Shared option patterns

- `--repo` on model/serve/run/deploy commands selects a configured OpenLLM model repository alias instead of the default repository.
- `--env NAME` passes an environment variable from the current environment; `--env NAME=value` passes a literal value. Use this for `HF_TOKEN` or model-required Bento environment variables.
- `--arg key=value` forwards Bento arguments to the underlying `bentoml` command.
- `--verbose` increases OpenLLM output verbosity for several commands.
- `--do-not-track` or `BENTOML_DO_NOT_TRACK=true` disables BentoML analytics tracking.

## Side-effect classes

| Action | Side effects |
| --- | --- |
| `--help`, `--version`, parser-only helpers in this generated skill | Safe; no model download or service startup. |
| `openllm repo update` | Network and disk side effects: refreshes configured Git model repositories. |
| `openllm serve` / `openllm run` | May update repos, install per-model dependencies, download weights, allocate GPU/CPU resources, and start a long-running server. |
| `openllm deploy` | Requires BentoCloud credentials/config, may copy cloud config into a repo cache, and creates or updates cloud deployments. |
| `openllm clean ...` | Deletes caches or config. Ask before running destructive cleanup in a user's environment. |

## Model identifiers

OpenLLM generally accepts model tags like `llama3.2:1b`. When a model comes from a non-default repository, source code supports slash-qualified tags of the form `repo_alias/model:version` for API-level listing, and CLI commands also accept `--repo repo_alias`.

A missing or ambiguous model usually means one of these is true:

1. The model repository cache is missing or stale.
2. The selected repository alias is wrong.
3. The tag has multiple matching versions and needs an explicit `model:version`.
4. The custom model repository does not have the expected `bentoml/bentos/<model>/<version>/bento.yaml` layout.

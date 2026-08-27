# CLI reference

## When to read

Read this for the verified top-level command map and route decisions. Detailed command-family workflows live in the sub-skills.

## Top-level CLI

The public package exposes both `sam` and `solace-agent-mesh`; use `sam` in examples unless the user explicitly asks for the long form.

```bash
sam --help
sam --version
```

Top-level command families verified from installed CLI help:

| Command | Purpose | Route |
| --- | --- | --- |
| `sam init` | Initialize a new SAM application project | `sub-skills/project-bootstrap/` |
| `sam add` | Create templates for agents, gateways, or proxies in a project | `sub-skills/project-bootstrap/` |
| `sam plugin` | Manage SAM plugins: create, add components, install, catalog, and build | `sub-skills/plugin-lifecycle/` |
| `sam run` | Run SAM app YAML files, with optional discovery and environment loading | `sub-skills/runtime-operations/` |
| `sam task` | Send tasks to a Web UI gateway or start SAM for one task | `sub-skills/runtime-operations/` |
| `sam docs` | Serve packaged SAM documentation locally | `sub-skills/runtime-operations/` |
| `sam tools` | Manage and inspect SAM built-in tools | `sub-skills/runtime-operations/` |
| `sam eval` | Run an evaluation suite from a config file | `sub-skills/evaluation/` |

## Command-family notes

### Project bootstrap

Use `sam init` for project-level layout and `sam add` for project components. These commands write files, can prompt interactively, and may launch the GUI configuration portal.

Common safe preflight pattern:

```bash
sam init --help
sam add --help
sam add agent --help
sam add gateway --help
sam add proxy --help
```

Then validate generated projects with `sub-skills/project-bootstrap/scripts/inspect_project.py` before live runtime startup.

### Plugin lifecycle

Use `sam plugin create` for new plugin package skeletons, `sam plugin add` to add a component from an installed plugin into a project, `sam plugin install` to install or verify a plugin package, `sam plugin catalog` for the browser catalog, and `sam plugin build` for artifacts.

Safe preflight pattern:

```bash
sam plugin --help
sam plugin create --help
sam plugin add --help
sam plugin install --help
sam plugin catalog --help
sam plugin build --help
```

Plugin commands can modify projects or Python environments; inspect first with `sub-skills/plugin-lifecycle/scripts/inspect_plugin.py`.

### Runtime operations

Use `sam run` only when the user wants a live app startup. It may discover or accept YAML config files, load environment files, and connect to configured services.

Use `sam task` only when a Web UI gateway is available or when the user wants one-shot task execution:

```bash
sam run --help
sam task --help
sam task send --help
sam task run --help
```

For dry gateway checks, prefer `sub-skills/runtime-operations/scripts/check_gateway.py` because it performs only safe GET probes by default.

### Built-in docs and tools

`sam docs` serves packaged docs locally and can require an available port/browser. `sam tools` inspects registered built-in tools and supports the tool discovery workflow documented under runtime operations.

```bash
sam docs --help
sam tools --help
sam tools list --help
```

### Evaluation

`sam eval` accepts an evaluation suite/config file and can run local or remote evaluation. The live run may start services or contact a gateway/LLM depending on mode.

```bash
sam eval --help
python sub-skills/evaluation/scripts/validate_eval_inputs.py path/to/suite.json
```

## REST client CLI

The separate `sam-rest-client` package exposes:

```bash
sam-rest-cli --help
```

Use it for REST gateway task invocation when a gateway URL, target agent name, prompt, optional bearer token, optional file attachments, mode (`async` or `sync`), and timeout are known. See `sub-skills/runtime-operations/references/rest-client.md` before installing it alongside the main SAM package because their pinned dependency versions can conflict.

## Safety matrix

| Command | Dry-safe with `--help` | Writes files | Starts local services/browser | Contacts broker/LLM/gateway/network |
| --- | --- | --- | --- | --- |
| `sam init` | yes | yes | maybe (`--gui`) | no by default |
| `sam add` | yes | yes | maybe for web add flows | no by default |
| `sam plugin create` | yes | yes | no | no by default |
| `sam plugin install` | yes | environment/package mutation | no | maybe |
| `sam plugin catalog` | yes | catalog/cache state | yes | maybe |
| `sam plugin build` | yes | `dist/` artifacts | no | maybe for build deps |
| `sam run` | yes | logs/state | yes | yes |
| `sam task send` | yes | maybe uploaded files/session data | no | yes |
| `sam task run` | yes | logs/state | yes | yes |
| `sam docs` | yes | no | yes | no by default |
| `sam tools list` | yes | no | no | no by default |
| `sam eval` | yes | results tree | maybe | yes |
| `sam-rest-cli` | yes | optional log file | no | yes |

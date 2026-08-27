# Plugin lifecycle troubleshooting

Use this guide to diagnose SAM plugin creation, inspection, install/add, catalog, and build failures without running live SAM apps.

## Quick triage

1. Confirm which command failed: `plugin create`, `install`, `add`, `catalog`, or `build`.
2. If a plugin directory/package is involved, run:

   ```bash
   python sub-skills/plugin-lifecycle/scripts/inspect_plugin.py path/to/plugin --component-name desired-name --project-dir path/to/project
   ```

3. Separate structural issues from side-effect issues:
   - Structural: missing `pyproject.toml`, missing `config.yaml`, unknown metadata type, invalid YAML/TOML, absent package files.
   - Side-effect: package-manager failure, Git/network failure, catalog port/browser failure, build backend failure, target file overwrite.
4. Do not start brokers, gateways, LLM providers, tasks, or evaluations while debugging plugin packaging.

## Symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Invalid plugin type` during create | `--type` is not one of `agent`, `gateway`, `tool`, `workflow`, `custom` | Use a supported type. If the target is a reusable agent, use `agent`; if it is project-only scaffolding, route to `project-bootstrap`. |
| Plugin name conflicts with an official plugin | Create checks official registry names | Choose a different name, usually namespaced by team/product. If network failed during the check, confirm the intended name is not official before publishing. |
| Created directory already had files and contents changed | `sam plugin create` writes templates into an existing directory | Restore from backup/version control. Re-run create only into a new empty directory or after intentionally moving old files aside. |
| `pyproject.toml not found` during add/build | Source is not a plugin root or package omitted the file | Point at the plugin root, rebuild with package force-includes, or use an installed package that includes `pyproject.toml`. |
| `config.yaml not found` during add | Plugin package did not include the config template | Add root `config.yaml`; ensure build metadata force-includes it into the installed module; rebuild/reinstall. |
| Add writes under `configs/plugins` unexpectedly | Metadata type is missing/unknown or under the wrong tool table | Set `[tool.<project_name_with_underscores>.metadata] type = "agent"|"gateway"|"tool"|"workflow"|"custom"`. |
| Add overwrote an existing config | CLI writes the target YAML with normal write mode | Recover the previous file, diff desired changes manually, then rerun only after backing up or deleting the target intentionally. |
| Component placeholders remain in generated config | Plugin config used unsupported/misspelled placeholders | Use only the supported `__COMPONENT_*__` placeholders listed in `plugin-workflows.md`, then rerun add. |
| Plugin placeholders remain in plugin package files | Template replacement did not run or files were copied manually | Regenerate or replace `__PLUGIN_*__` tokens before building/installing. |
| Local `.tar.gz` source is rejected | Source distribution extension detection is not reliable in this version | Build and use a wheel, install from local directory, or use Git/pip package syntax. |
| Plain package name is not installed automatically | Non-official names without slashes are treated as already installed modules | Install with your package manager first, use a local wheel/path, or provide Git URL syntax. |
| Install command says placeholder is required or installs the wrong target | `--install-command`/`SAM_PLUGIN_INSTALL_COMMAND` is malformed | Use a command containing literal `{package}`, such as `uv pip install {package}`. Avoid shell-only syntax because the command is split on whitespace. |
| Package-manager command fails | Missing package, network/auth issue, dependency conflict, wrong environment | Retry in an isolated environment; run the exact formatted install command manually; check index credentials; prefer wheel/local path for offline installs. |
| Install succeeds but SAM cannot find module | `[project].name` does not match import package name after `-` -> `_` normalization, or package files not installed | Align project name and package/module directory; ensure the wheel includes the module and force-included plugin files. |
| Git source fails | `git` missing, clone/auth/network failure, wrong URL, wrong subdirectory | Install Git, verify repository access, use `git+https://...#subdirectory=<plugin>`, or clone/build a wheel manually. |
| Official plugin lookup is empty or slow | Default registry requires network and GitHub API access | Treat official lookup as best-effort; use the explicit package name/wheel/Git URL if known; retry when network is available. |
| Catalog backend missing | The installed package lacks catalog backend modules or was installed incompletely | Reinstall the SAM CLI/package in a clean environment and rerun `sam plugin catalog --help` before launching. |
| Catalog port already in use | Default `5003` is occupied | Use `sam plugin catalog --port <free-port>` or stop the process using the port. |
| Catalog browser does not open | Headless environment, browser not configured, or server did not become ready | Open the printed URL manually from a browser that can reach the host/port; for remote environments, bind intentionally with `CONFIG_PORTAL_HOST` and tunnel if appropriate. |
| Catalog exits with non-shutdown status | Backend startup failure, registry failure, or interrupted child process | Read the CLI output, free the port, check registry network access, then rerun. Do not assume plugin installation happened. |
| Build reports `pyproject.toml not found` | Wrong build directory | Run from plugin root or pass the plugin root to `sam plugin build`. |
| Build reports missing `build` package | Python build frontend is absent | Install it in the active environment: `python -m pip install build`, then rerun. |
| Build succeeds but add fails later | Wheel omitted `config.yaml`, `README.md`, or `pyproject.toml` from installed module | Add force-include entries to build metadata, rebuild, reinstall, and inspect the installed package tree. |

## Invalid names and normalization

SAM normalizes plugin and component names instead of applying strict validation:

- Separators (`space`, `_`, `-`) collapse into words.
- Camel-case boundaries are split.
- Directory/filename uses kebab-case.
- Python module uses snake_case.
- Class/display strings use Pascal/spaced forms.

Practical rules:

- Avoid leading/trailing punctuation, path separators, shell metacharacters, and names that normalize to empty strings.
- Prefer lowercase kebab names for plugin directories and component filenames.
- Use organization prefixes for published plugins to avoid official/community collisions.
- Inspect the normalized target path before running commands that write files.

## Missing metadata/config checklist

For a plugin root or installed package directory, verify:

```text
pyproject.toml
config.yaml
README.md                       # recommended; included by generated template
src/<module>/__init__.py         # source layout, or package files in installed layout
```

In `pyproject.toml`:

```toml
[project]
name = "my_plugin"
version = "0.1.0"

[tool.my_plugin.metadata]
type = "agent"
```

If `[project].name = "my-plugin"`, the metadata table should be `[tool.my_plugin.metadata]` because SAM normalizes the project name by replacing hyphens with underscores when looking up metadata.

## Existing target files

`sam plugin add demo --plugin ./my-plugin` writes one of:

```text
configs/agents/demo.yaml      # agent/tool
configs/gateways/demo.yaml    # gateway
configs/workflows/demo.yaml   # workflow
configs/plugins/demo.yaml     # custom/unknown
```

Before running add:

1. Compute the target path with `inspect_plugin.py --component-name demo --project-dir .`.
2. If the file exists, copy or commit it first.
3. Decide whether to merge manually or overwrite intentionally.
4. After add, review the generated YAML for environment placeholders and plugin-specific configuration fields before any live run.

## Catalog/network side effects

`sam plugin catalog` is intentionally interactive and side-effectful:

- It starts a local backend process.
- It may contact GitHub/registries and clone or pull registry repositories.
- It writes cache and registry state under the SAM CLI home directory.
- It attempts to open a browser.
- Catalog installation shells out to `sam plugin add` and can modify the project and Python environment.

If you only need to decide whether a plugin package is structurally valid, do not launch catalog. Use the bundled inspection helper instead.

## Build/package side effects

`sam plugin build` runs `python -m build`; the build backend may create an isolated build env and download/build dependencies. Keep this separate from live SAM runtime verification.

For repeatable builds:

- Pin plugin dependencies intentionally in `pyproject.toml`.
- Clean or review `dist/` before publishing.
- Inspect the built wheel contents if add/install cannot find `config.yaml` or `pyproject.toml` after installation.
- Treat broad release automation, signing, publishing, and CI policy as outside this sub-skill.

## When to route elsewhere

- If the user wants a component inside one project and does not need a reusable Python package, route to `project-bootstrap`.
- If the user wants to run the project, send tasks, activate gateway listeners, or validate runtime connectivity, route to `runtime-operations`.
- If the user wants to author internal workflow DAG YAML, route workflow details to `workflow-authoring`; this sub-skill only covers packaging a workflow as a plugin.

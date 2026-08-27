# CLI and Configuration Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `jina` command raises import error before showing help | Broken package install or incompatible dependency. | Run `python -c "import jina"`, `python -m pip check`, and see root install troubleshooting. |
| `ModuleNotFoundError: pkg_resources` | Hubble dependency still imports `pkg_resources`. | Install or pin setuptools that provides `pkg_resources`. |
| `jina flow --uses ...` says a valid `--uses` is required | The CLI command starts from a YAML file; no default Flow is created from CLI. | Pass a Flow YAML path or use Python `Flow()` directly. |
| YAML `${{ ENV.X }}` remains unresolved | The environment variable was missing or the syntax was wrong. | Export the variable before loading, or pass `context` for `${{ CONTEXT.X }}`. |
| `py_modules` class cannot be found | The class is not in the declared file/module, or relative paths are wrong. | Use explicit `py_modules`, `extra_search_paths`, and top-level class definitions. |
| Shell rc files changed after install | Jina autocomplete registration updated shell completion blocks. | Install in an isolated environment or redirect home/config during automated tests. |
| `jina cloud` or `jina hub` hangs or asks for auth | Remote service command needs network and credentials. | Use help-only checks unless the user explicitly authorizes login/token/network operations. |

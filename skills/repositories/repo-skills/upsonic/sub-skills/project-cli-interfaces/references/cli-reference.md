# CLI Reference

## Verified commands

| Command | Purpose |
| --- | --- |
| `upsonic init` | Scaffold a new agent project with `main.py` and `upsonic_configs.json`. |
| `upsonic add <library> <section>` | Add a dependency to the project config. |
| `upsonic remove <library> <section>` | Remove a dependency from the project config. |
| `upsonic install [section]` | Install the project requirements for a selected section or the default set. |
| `upsonic run [--host HOST] [--port PORT]` | Start the generated project as a server. |
| `upsonic zip [output.zip]` | Package the project for transport or upload. |

## Config notes

- The CLI expects `upsonic_configs.json` next to `main.py`.
- The config stores environment variables, machine specs, dependencies, and input/output schemas.
- `upsonic run` uses the config to build either a FastAPI app or an `InterfaceManager` server.

## Example flow

```bash
upsonic init
upsonic install
upsonic run --host 0.0.0.0 --port 8000
```

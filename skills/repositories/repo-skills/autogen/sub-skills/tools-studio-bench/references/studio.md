# AutoGen Studio

AutoGen Studio is a research/prototype UI for prototyping AutoGen teams and workflows. It is useful for existing AutoGen users, demos, and migration investigation, but it is not a production-ready application and AutoGen itself is in maintenance mode.

## Package and Commands

- Distribution: `autogenstudio`.
- Console script: `autogenstudio`.
- Source CLI is Typer-based and exposes `ui`, `serve`, `version`, and `lite` commands.
- Current package metadata requires Python `>=3.9` and depends on web/database packages such as `fastapi`, `uvicorn`, `sqlmodel`, `psycopg`, `alembic`, and `pydantic-settings`.

## Compatibility Boundary

AutoGen Studio metadata in this repository pins core AutoGen libraries below modern 0.7.x lines:

- `autogen-core>=0.4.9.2,<0.7`
- `autogen-agentchat>=0.4.9.2,<0.7`
- `autogen-ext[magentic-one, openai, azure, mcp]>=0.4.2,<0.7`

Do not install Studio into an environment that must keep `autogen-core`, `autogen-agentchat`, or `autogen-ext` at 0.7.x unless you intentionally resolve the dependency boundary. Prefer a separate Studio environment aligned to Studio’s package metadata.

## Safe Checks

Safe checks:

```bash
python -m pip show autogenstudio
python -c "import importlib.metadata as m; print(m.version('autogenstudio'))"
autogenstudio --help
autogenstudio version
```

Avoid these unless explicitly approved because they start services or touch app state:

```bash
autogenstudio ui --port 8081 --appdir ./my-app
autogenstudio serve --team ./team.json
autogenstudio lite
```

## UI Command Planning

`autogenstudio ui` starts a local web application. Important options include:

- `--host`: default loopback host in the source CLI.
- `--port`: web server port.
- `--workers`: Uvicorn workers.
- `--reload`: development reload mode.
- `--appdir`: directory for Studio data, including database and generated files.
- `--database-uri`: explicit database URL; SQLite is simplest for local use, PostgreSQL needs a reachable server and credentials.
- `--auth-config`: path to auth configuration.
- `--upgrade-database`: request schema upgrade.

Before starting UI, verify the app directory is disposable or backed up, the port is free, and secrets are not committed in `.env` files.

## Serve and Lite

- `autogenstudio serve --team <team-file>` serves an API endpoint from a team JSON file and validates the file exists before Uvicorn startup.
- `autogenstudio lite` launches a lightweight local Studio session and may auto-open a browser. It still starts a service and should not be treated as a harmless import check.

## Production Caution

Studio does not replace application-level authentication, authorization, sandboxing, jailbreak evaluation, secret handling, or deployment hardening. For production applications, prefer direct AutoGen framework code for existing maintenance work or Microsoft Agent Framework for new projects.

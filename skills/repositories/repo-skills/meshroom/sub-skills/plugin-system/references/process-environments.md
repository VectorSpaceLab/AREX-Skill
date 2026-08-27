# Plugin Process Environments

## Directory-Tree Plugins

The default `DirTreeProcessEnv` looks for plugin-local `bin`, `lib`/`lib64`, and optional `venv` directories. It builds a process environment with plugin paths and config defaults while preserving explicitly set user environment variables.

Use this layout when a plugin has Python or binary dependencies that should travel with the plugin:

```text
plugin-root/
  meshroom/
    nodes/
    config.json
  venv/
  bin/
  lib/
```

The plugin node process may run with a dedicated runtime environment. A node descriptor's provider exposes the runtime environment, command prefix, and command suffix used by `Node.processChunkInEnvironment()` or `CommandLineNode` execution.

## Rez Plugins

`RezProcessEnv` is selected for a `package=folder` mapping in `MESHROOM_REZ_PLUGINS` or `MESHROOM_USER_REZ_PLUGINS`. It resolves plugin subrequires and wraps commands with `rez env` when Rez is configured.

Use Rez only when the host has a working Rez installation and the plugin documents its package URI/subrequires. Do not assume a normal Python virtualenv can satisfy Rez-specific process wrappers.

## Configuration Precedence

1. Start with the process environment.
2. Load `config.json` entries as defaults.
3. Resolve existing relative path entries against the plugin root.
4. Preserve explicit values from the current environment over config values.

When debugging a node launched in a dedicated environment, compare the plugin's `configEnv`, `configFullEnv`, and provider process env rather than only printing the parent shell's environment.

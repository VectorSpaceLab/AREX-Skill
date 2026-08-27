# Cross-Cutting Troubleshooting

## `wren: command not found`

**Likely cause:** `wrenai` is not installed into the Python environment on
PATH, or the environment is not active.

**Recover:** install the base package in the intended environment, then rerun:

```bash
pip install wrenai
wren --version
```

Use a virtual environment on systems that reject global `pip` writes. Do not
work around an externally managed Python by scattering packages across the
system interpreter.

## A command cannot find the Wren project

**Symptoms:** an error asking for `wren_project.yml`, or an operation uses an
unexpected project.

**Recover:** run from the project root, pass the command's explicit project/path
option when available, or set `WREN_PROJECT_HOME` deliberately for the current
session. Confirm the target has `wren_project.yml`; after editing source files,
run `wren context validate` and `wren context build`.

## `target/mdl.json` is missing or stale

**Likely cause:** the project was initialized but not built, or source YAML has
changed since the last build.

```bash
wren context validate
wren context build
```

A stale target can still be served by some runtime surfaces; treat warnings as a
prompt to rebuild rather than as proof the latest models are active.

## Profile or secret resolution fails

**Symptoms:** no profile, unknown datasource, missing `${VAR}`, authentication
failure, or connection refused.

**Recover:** inspect the selected profile with `wren profile debug`; query field
requirements using `wren docs connection-info <datasource>`; put sensitive
values in an environment file or shell environment, not in project YAML or CLI
history. Check the project-bound profile before assuming the globally active
profile applies.

## Missing optional dependency

**Symptoms:** import errors for a connector, MCP, UI, or memory operation.

**Recover:** identify the owning feature, install its smallest matching extra,
and retry. Examples:

```bash
pip install "wrenai[postgres]"
pip install "wrenai[memory]"
pip install "wrenai[mcp]"
```

Do not install every extra as a generic first response. The failing command and
its workflow owner determine the required dependency.

## Plan succeeds but execution fails

A successful `wren dry-plan` proves semantic planning and dialect generation; it
does not prove database permissions, network reachability, dialect support, or
query cost. Inspect the planned SQL, verify the profile/connector, and use the
query-engine troubleshooting reference for the specific failure layer.

## Do not leak secrets into GenBI or agent tooling

Static GenBI apps can expose every shipped file. MCP and framework agents should
receive only the tools/data they need. Never include database credentials,
provider tokens, or `.env` files in a static app or command argument.

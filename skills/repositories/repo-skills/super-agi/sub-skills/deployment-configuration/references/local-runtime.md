# Local Runtime Notes

## When to Read

Read this when a user wants to launch SuperAGI directly on a host, not through
Docker Compose.

## Host-Local Paths in the Checkout

The repository includes host-local helpers such as `run.sh`, `run.bat`, `ui.py`,
`run_gui.py`, and `run_gui.sh`. They are useful as evidence but are not ideal as
future-agent runtime instructions because they:

- install dependencies into a local virtual environment,
- may clone external frontend sources,
- prompt interactively for agent details,
- and can start long-running listeners or worker processes.

## Safer Host-Local Approach

If a downstream user explicitly wants host-local operation, use the smallest
repeatable set of steps that the helper scripts imply:

1. Create an isolated Python 3.10 environment.
2. Install the repository requirements that are actually needed for the chosen
   workflow.
3. Create or validate `config.yaml`.
4. Confirm PostgreSQL and Redis connectivity.
5. Run the desired host-local service command only after the user accepts the
   long-running side effect.

## Caveats

- `run.sh` expects `config.yaml` and can clone `text-generation-webui` into the
  checkout if the TGWUI directory is absent.
- `install_tool_dependencies.sh` is container-oriented and may run `apt update`
  and install arbitrary apt/pip requirements. Treat it as a Docker entrypoint
  artifact, not a normal host helper.
- `cli2.py` is interactive and starts several processes. It is better used as a
  behavior reference than as a bundled automation target.

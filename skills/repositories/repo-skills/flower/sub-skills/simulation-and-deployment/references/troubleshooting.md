# Troubleshooting

Use this page for predictable CLI, profile, runtime, and deployment failures.

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `database is locked` or similar SQLite errors during local runs | The managed local SuperLink is storing state on a slow or shared filesystem such as NFS | Stop the background local SuperLink, switch the local profile to `address = ":local-in-memory:"`, and rerun `flwr run`. Prefer local disk if you need persistence. |
| `flwr run` or `flwr log` seems to use the wrong SuperLink | The default profile in Flower Configuration is not the one you expected, or the named profile was not passed explicitly | Run `flwr config list`, check `[superlink].default`, and pass the desired profile name explicitly. Remember that `flwr run` must be launched from the app directory for local app paths. |
| `UNAUTHENTICATED` from `flwr run`, `flwr list`, `flwr log`, `flwr stop`, or `flwr pull` | The profile is not logged in, or the connection is pointed at a remote SuperLink that needs authentication | Run `flwr login <profile>`, verify the selected profile, and retry. |
| `flwr login` fails immediately | The selected profile is marked `insecure = true`, or the TLS material is wrong | Use a secure profile with `root-certificates` or the default TLS trust path. `flwr login` requires TLS. |
| Simulation does not start on the current machine | Ray is missing, the current OS is not well supported, or the backend resources are not available | Install the simulation dependency set, prefer Linux or macOS, and use WSL2 on Windows when needed. Revisit `flwr federation simulation-config` for the resource settings. |
| `flower-supernode --help` prints an INFO line before the usage text | Expected startup noise from the executable | Ignore the line if the help command still exits with code 0 and shows the usage block. |
| Local runs fail to start or keep failing after a restart | A stale background local SuperLink is still running, or the local Control API port is occupied | Inspect `"$FLWR_HOME/local-superlink/superlink.log"`, stop the matching `flower-superlink` process, and retry. If you changed `FLWR_LOCAL_CONTROL_API_PORT`, use that port in the process match. |
| A profile uses both `root-certificates` and `insecure = true` | TLS settings conflict | Remove one of the settings. Use `root-certificates` for TLS, or use `insecure = true` only for local testing. |
| `flwr config list` shows an unexpected or missing connection | The config file is new, was not migrated, or the profile name was mistyped | Confirm the file path printed by `flwr config list`, then add or fix the matching `[superlink.<name>]` entry. The file is created automatically on first use if missing. |

## Quick recovery hints

- Local history needed? Keep `:local:` and move `FLWR_HOME` to a local disk.
- No history needed? Switch to `:local-in-memory:`.
- Remote deployment? Use TLS and `flwr login` before retrying the command.
- Simulation resource issues? Re-check `flwr federation simulation-config` and per-run `--federation-config` overrides.
- Deployment process startup issues? Re-check the `flower-superlink` and `flower-supernode` logs, not only the `flwr` command output.

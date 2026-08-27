# Flower CLI Reference

This reference covers the command surface for local Flower runs, Simulation Runtime
configuration, and deployment-oriented SuperLink/SuperNode workflows.

## Command family map

| Surface | What it does | Key notes |
| --- | --- | --- |
| `flwr run [APP] [SUPERLINK]` | Run a Flower App | Local paths build a FAB from the app directory. Remote app specs like `@account/app` are accepted as-is and skip the local build step. Use `--stream` for live logs. |
| `flwr list [SUPERLINK]` | List runs | Add `--run-id`, `--limit`, or `--format json`. |
| `flwr log RUN_ID [SUPERLINK]` | Read run logs | `--stream` streams continuously; `--show` prints once. |
| `flwr stop RUN_ID [SUPERLINK]` | Stop a run | Sends a stop request through the Control API. |
| `flwr login [SUPERLINK]` | Authenticate to a SuperLink | Requires TLS-enabled connections. Fails if the selected profile is marked `insecure = true`. |
| `flwr pull RUN_ID [SUPERLINK]` | Get artifact download URL | Only applies to completed runs. |
| `flwr build [--app PATH]` | Build a Flower App Bundle | Bundles the app into a `.fab` archive. |
| `flwr install SOURCE.fab` | Install a Flower App Bundle | Installs into `"$FLWR_HOME/apps/"` or `"$HOME/.flwr/apps/"`. |
| `flwr config list` | Show SuperLink profiles | Displays the config file path and the available `superlink.*` entries. |
| `flwr federation ...` | Federation admin commands | Includes `list`, `archive`, `create`, `add-supernode`, `remove-supernode`, `remove-account`, `invite`, and `simulation-config`. |
| `flwr supernode ...` | SuperNode registry management | Distinct from the `flower-supernode` process. It manages registry entries only. |
| `flower-superlink` | Start the long-lived SuperLink process | Handles the Control API, Runtime API, and Fleet API. |
| `flower-supernode` | Start the long-lived SuperNode process | Connects to the SuperLink and runs client-side app work. |
| `flwr federation simulation-config` | Set simulation defaults | Persists Simulation Runtime defaults for the selected SuperLink profile. |

## `flwr` command notes

### `flwr run`

- Use a local app directory to run app code from disk.
- Use a remote app spec like `@account_name/app_name` when the app already lives on
  Flower.
- The first positional `superlink` argument selects a named SuperLink profile.
- `--federation` must use the `@<account>/<federation-name>` format.
- `--run-config` overrides app config values from `pyproject.toml`.
- `--federation-config` overrides Simulation Runtime values for that run.
- `--stream` follows logs in the same terminal.
- `--format json` is available for machine-readable output.

### `flwr list`, `flwr log`, `flwr stop`, `flwr pull`

- These commands can be used from anywhere once the relevant profile exists.
- They all accept an optional `superlink` profile name.
- `flwr list` shows run ID, federation, app, status, elapsed time, and status change.
- `flwr log` defaults to streaming mode; use `--show` for a single fetch.
- `flwr stop` stops the run only; it does not stop a background local SuperLink.
- `flwr pull` returns a download URL for artifacts.

### `flwr login`

- Use this before remote commands when account authentication is required.
- It queries the selected SuperLink for the auth flow and then stores tokens locally.
- The selected connection must not be `insecure = true`.

### `flwr build` and `flwr install`

- `flwr build` creates a `.fab` archive from the current app directory unless `--app`
  points elsewhere.
- `flwr install` validates the `.fab` file and installs it into the Flower apps
  directory under `FLWR_HOME`.
- Use these when you want to move a Flower App as a bundle rather than as a source
  tree.

### `flwr config list`

- Shows the active Flower Configuration file and the available `superlink.*`
  profiles.
- On first use, Flower creates the config file automatically if it is missing.
- The built-in default config normally includes `supergrid` and a local profile.

### `flwr federation`

- `flwr federation simulation-config` is the command this sub-skill cares about most.
- The other federation commands manage federation records, invitations, and members.
- Use the federation group when the user is asking about federation lifecycle, not app
  authoring.

### `flwr supernode`

- This is the registry-management group inside `flwr`.
- It is not the same thing as the `flower-supernode` runtime executable.
- Use it only when the user needs to list, register, or unregister SuperNodes.

## Flower Configuration and profile selection

The Flower Configuration file lives under `"$FLWR_HOME/config.toml"` and defaults to
`"$HOME/.flwr/config.toml"` when `FLWR_HOME` is unset.

Typical profiles:

```toml
[superlink]
default = "local"

[superlink.local]
address = ":local:"

[superlink.local-in-memory]
address = ":local-in-memory:"

[superlink.local-deployment]
address = "127.0.0.1:9093"
insecure = true

[superlink.remote]
address = "superlink.example.com:9093"
root-certificates = "/absolute/path/root-ca.crt"
```

Notes:

- `:local:` launches or reuses the managed local SuperLink with on-disk state.
- `:local-in-memory:` launches or reuses the managed local SuperLink with in-memory
  state.
- `root-certificates` must be an absolute path.
- `root-certificates` and `insecure = true` do not belong together.
- `flwr run` must be executed from the app directory for local app paths.
- `flwr list`, `flwr log`, `flwr stop`, `flwr pull`, and `flwr login` can use the
  selected profile from anywhere.

## `flower-superlink`

The runtime executable starts the server-side processes.

Common flags:

| Flag | Meaning |
| --- | --- |
| `--insecure` | Disable TLS for the server-side APIs. |
| `--ssl-certfile`, `--ssl-keyfile`, `--ssl-ca-certfile` | TLS material for the Fleet API and Control API. |
| `--isolation subprocess|process` | Control whether app processes run in subprocesses or separate processes. |
| `--database` | Path to the SuperLink database file. Omit it for in-memory state. |
| `--serverappio-api-address` | Runtime API address. `--simulationio-api-address` is a deprecated alias. |
| `--control-api-address` | Control API address. `--exec-api-address` is deprecated. |
| `--fleet-api-type grpc-rere|grpc-adapter` | Choose the Fleet API transport. |
| `--fleet-api-address` | Fleet API address. |
| `--simulation` | Enable Simulation Runtime behavior. |
| `--enable-supernode-auth` | Require SuperNode authentication. Needs TLS and `grpc-rere`. |
| `--disable-runtime-dependency-installation` | Disable runtime dependency installation. |
| `--log-file` | Write SuperLink logs to a file. |
| `--log-rotation-interval-hours` / `--log-rotation-backup-count` | Rotate the SuperLink log file. |
| `--superexec-auth-secret-file` | Shared secret for SuperExec auth. |
| `--appio-ssl-certfile`, `--appio-ssl-keyfile`, `--appio-ssl-ca-certfile` | TLS for the Runtime API. |
| `--health-server-address` | Optional health server address. |

Behavior notes:

- A bare `flower-superlink` invocation uses the default Control, Fleet, and Runtime
  addresses from the executable.
- The managed local runtime started by `flwr run` uses a fixed local Control API port
  and writes logs under `"$FLWR_HOME/local-superlink/"`.
- If the command is run in simulation mode without a database path, the SuperLink uses
  in-memory state.
- The `--allow-runtime-dependency-installation` flag is deprecated.

## `flower-supernode`

The runtime executable starts the client-side process.

Common flags:

| Flag | Meaning |
| --- | --- |
| `--insecure` | Disable HTTPS for the client-side process. |
| `--grpc-rere` / `--grpc-adapter` | Choose the transport layer. |
| `--root-certificates` | Root CA certificate for verifying the SuperLink. |
| `--superlink` | SuperLink Fleet API address. |
| `--max-retries`, `--max-wait-time` | Connection retry limits. |
| `--auth-supernode-private-key` | Enable SuperNode authentication. |
| `--auth-supernode-public-key` | Deprecated authentication flag. |
| `--node-config` | Space-separated key/value node configuration. |
| `--isolation subprocess|process` | Control how ClientApps are launched. |
| `--clientappio-api-address` | Runtime API address for SuperExec and ClientApp. |
| `--appio-ssl-certfile`, `--appio-ssl-keyfile`, `--appio-ssl-ca-certfile` | TLS material for the Runtime API. |
| `--trusted-entities` | YAML file with trusted public keys. |
| `--superexec-auth-secret-file` | Shared secret for SuperExec auth. |
| `--allow-runtime-dependency-installation` | Allow runtime dependency installation. |
| `--health-server-address` | Optional health server address. |

Behavior notes:

- `flower-supernode --help` emits a short INFO line before the usage block. That is
  expected parser/startup noise, not a runtime failure.
- The command defaults to `subprocess` isolation and to a runtime API on port 9094.
- `--allow-runtime-dependency-installation` is the opt-in flag for runtime installs.

## `flwr federation simulation-config`

This command persists the Simulation Runtime defaults for a SuperLink profile.

| Flag | Meaning |
| --- | --- |
| `--num-supernodes` | Number of simulated SuperNodes. |
| `--client-resources-num-cpus` | CPUs assigned to each ClientApp worker. |
| `--client-resources-num-gpus` | GPU share assigned to each ClientApp worker. |
| `--verbose` | Enable verbose runtime logs. |
| `--backend-name ray` | Backend name; Ray is the supported choice. |
| `--init-args-num-cpus` | Cap total CPUs visible to the Simulation Runtime. |
| `--init-args-num-gpus` | Cap total GPUs visible to the Simulation Runtime. |
| `--init-args-logging-level` | Control backend logging level. |
| `--init-args-log-to-driver` | Control whether runtime logs propagate to the driver. |

Important notes:

- This is the supported place to set Simulation Runtime defaults.
- The command accepts optional `FEDERATION` and `SUPERLINK` positional arguments plus
  `--format default|json`.
- New guidance should avoid storing Simulation Runtime options under `options.` in the
  Flower Configuration.
- Per-run overrides use `flwr run ... --federation-config="..."`.
- The runtime resource values are soft concurrency controls, not strict memory limits.

## Quick defaults

- Local managed SuperLink Control API: `127.0.0.1:39093`
- SuperLink Runtime API: `0.0.0.0:9091`
- SuperLink Fleet API: `0.0.0.0:9092`
- SuperLink Control API: `0.0.0.0:9093`
- SuperNode Runtime API: `0.0.0.0:9094`
- Local managed SuperLink state root: `"$FLWR_HOME/local-superlink/"`

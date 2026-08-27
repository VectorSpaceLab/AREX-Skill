# CLI and integration troubleshooting

## Install/import failures

1. Confirm the invoking interpreter and console script agree:

   ```bash
   python -c 'import sys; print(sys.executable)'
   command -v scl
   scl --help
   ```

2. Probe `import smarts`, `import cli.cli`, and the needed leaf module in the
   same environment. A missing `scl` means the package/entry point is not
   installed; a missing optional module means select the narrow extra in an
   isolated environment.
3. Run `pip check` before changing versions. Do not install `all`, modify a
   shared environment, or run the repository's host setup installer merely to
   fix a help command.
4. If an editable install resolves local source unexpectedly, treat that as an
   inspection detail, not a runtime dependency. The operating workflow needs a
   normal installed package or an intentionally configured project checkout.
5. For camera/Envision failures, distinguish missing Python packages from
   display/X11/browser/server issues. Core headless CLI use does not require a
   browser.

## Optional dependency and service failures

- **SUMO/TraCI:** read [sumo-traci.md](sumo-traci.md). Check the executable,
  `SUMO_HOME`, `sumolib`/`traci`, map compatibility, and port owner in that
  order. A missing SUMO stack is an explicit optional gap.
- **OpenDRIVE:** confirm `opendrive2lanelet`, Rtree, a readable map source, and
  scenario metadata. Import success does not validate the file.
- **Waymo:** confirm Scenario-proto versus `tf.Example`, protobuf compatibility,
  a readable TFRecord, and an existing scenario ID from `overview`. Do not
  regenerate generated protobuf code automatically.
- **Argoverse:** confirm `av2`, Rtree, and both matching scenario/map files in
  the expected directory. The base package has no dataset to fall back to.
- **ROS:** probe Python packages, ROS installation, master/node availability,
  and message versions separately. No `scl` command starts ROS for you.
- **Envision:** confirm the server endpoint, port listener, websocket path, and
  JSONL record format. `scl scenario replay` does not start the server; `scl
  envision start` stays in the foreground.
- **Ray/RLlib/zoo:** route policy and locator errors to rl-agent-zoo. Core CLI
  help cannot establish algorithm, checkpoint, or worker compatibility.

## Data and configuration failures

- `Invalid value for <scenario>` or a missing argument usually means the path
  is relative to the current cwd or the source directory does not exist. Print
  `pwd`, use a known path, and inspect `--help`.
- A scenario can contain valid source files while generated `build/`, map,
  traffic, mission, bubble, or cache artifacts are stale/missing. Use the
  scenario-studio validation/build workflow in a disposable copy; `--clean`
  removes derived artifacts and is not a read-only repair.
- If behavior differs between shells, inspect `SMARTS_*` variables. They
  override engine INI settings. Check especially SUMO mode/host/port and
  TraCI retry count.
- For Waymo/Argoverse/OpenDRIVE, report the exact missing file/data shape rather
  than treating it as a generic SMARTS import problem.

## CLI/API misuse

- Start at the leaf help. `scl run` uses a required script path and passes
  unprocessed trailing arguments to the script; put script options after that
  path.
- `--envision_port` without `--envision` only emits a warning and does not start
  a server. If another process already owns the port, choose a free port rather
  than killing it blindly.
- `scenario replay` needs directories containing `*.jsonl`, a running Envision
  websocket endpoint, and a sensible timestep. It is not the same as replaying
  a dataset or running a scenario.
- `benchmark_id` accepts an optional `==VERSION`; the agent locator must be
  registered/installed for the selected benchmark. List first and avoid
  `--auto-install` unless the listing is trusted.
- `zoo build` and `zoo install` change files/environments. A successful Click
  parse is not a successful wheel or policy installation.
- `waymo export` creates a scenario file beneath the requested output folder;
  check for collisions before invoking it.

## Workflow-specific failures

| Symptom | Likely boundary | Recovery |
|---|---|---|
| `scl scenario build` fails before running | cwd or missing scenario path | Check path existence, map/source layout, and scenario-studio's build contract. |
| Build succeeds but run cannot find map/artifacts | stale/incomplete generated output | Rebuild in a disposable copy with the intended seed; do not repeatedly add `--clean` to valuable data. |
| `scl run` exits and also closes a seemingly unrelated child | process-group cleanup and shared process group | Run in an isolated terminal/process group; do not nest unrelated long-lived services in the experiment. |
| Envision starts but replay cannot connect | port/endpoint/record mismatch | Check listener and endpoint scheme, then inspect one JSONL record and use a tiny replay. |
| Central TraCI client refuses connection | central server port/host/firewall/mode mismatch | Follow the port-conflict sequence in [sumo-traci.md](sumo-traci.md); core CLI help should still pass. |
| Diagnostic reports cannot be written | missing diagnostic extra, package permissions, or invalid packaged case | Use a writable isolated installation and one known case; do not run it as a core import probe. |
| Benchmark list parses but run fails | entrypoint/requirements/agent locator mismatch | Pin and inspect the listing, verify the locator, and run without auto-install only in a prepared environment. |
| Zoo manager hangs or worker cannot connect | expected long-lived service, port, or optional worker stack | Check port and worker prerequisites; terminate the manager deliberately after the test. |
| Waymo preview raises display/plot errors | optional plotting/display/data dependency | Use `overview` first; run preview with a supported display or headless plotting setup. |

## Stop conditions

Stop and report a gap when the core `scl --help`, `scl scenario --help`, or
`scl run --help` command fails after interpreter/package alignment; when a
required scenario/data contract is absent; or when resolving a port would
require killing an unknown service. Missing optional SUMO/ROS/Waymo/Argoverse/
RL stacks do not block the core route, but they must not be presented as
verified capabilities.

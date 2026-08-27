# Setup, Build, and Environment Reference

## Purpose

Use this reference when preparing a target openpilot checkout or diagnosing setup/build failures. openpilot is not a pure-Python wheel-only project: the Python package, submodules, and SCons-built native extensions all matter.

## Supported baseline

- Python: `>=3.12.3,<3.13` from `pyproject.toml`.
- Primary setup tooling: `uv` with `uv.lock`.
- Primary build tooling: SCons from package dependencies.
- Important submodules: `msgq_repo`, `opendbc_repo`, `panda`, `rednose_repo`, `teleoprtc_repo`, `tinygrad_repo`.
- Development target documented by the repo: Ubuntu 24.04; macOS usually works for most tools; Windows should use WSL 2/Ubuntu.

## Safe preparation sequence

In a target checkout, inspect before mutating:

```bash
python3 --version
git submodule status
python skills/disco/openpilot/scripts/openpilot_skill_doctor.py --repo-root .
```

If submodules are empty or prefixed with `-` in `git submodule status`, initialize them before syncing dependencies:

```bash
git submodule update --init --recursive
```

Then sync selected development extras and build common native extensions:

```bash
uv sync --frozen --extra tools --extra testing
scons -u openpilot/common/libparams_c.so msgq_repo/msgq/ipc_pyx.so msgq_repo/msgq/visionipc/visionipc_pyx.so
```

The full repo wrapper may run broader setup and host package changes. Use it only when you intentionally want the repository's managed PC setup behavior.

## What native build products unlock

| Built target | Failure it prevents | Common users |
| --- | --- | --- |
| `openpilot/common/libparams_c.so` | `libparams_c.so: cannot open shared object file` when importing `openpilot.common.params` or manager code | Params, manager, runtime services |
| `msgq_repo/msgq/ipc_pyx.so` | `No module named 'msgq.ipc_pyx'` | cereal messaging, PubMaster/SubMaster, logmessaged |
| `msgq_repo/msgq/visionipc/visionipc_pyx.so` | `No module named 'msgq.visionipc.visionipc_pyx'` | camera/VIPC, simulator, loggerd encoder tests |

## Setup commands and side effects

- `uv sync --frozen --extra tools --extra testing` mutates the target environment and installs package dependencies from the lock.
- `tools/op.sh setup` also checks OS/git/submodules, installs shell aliases/hooks, syncs dependencies, pulls LFS files, and may install host packages through setup scripts.
- `tools/setup_dependencies.sh` can install package-manager dependencies and udev rules; treat it as a host-mutating command.
- `git lfs pull` downloads large model/data artifacts; skip unless the selected workflow needs them.
- `op switch`, update scripts, release scripts, and start/stop device commands are state-mutating and should not be run as routine validation.

## Docs build

The docs tree can be built from a prepared checkout. Prefer one-shot build mode for validation; avoid long-running serve mode unless the user asks for a local preview.

## Good verification order

1. Read-only checkout checker.
2. Import help checks (`tools/test_runner.py -h`, car-port helper `-h`).
3. Small CPU-safe unit tests.
4. SCons native test targets if selected.
5. Route/network/GUI/hardware cases only when prerequisites and user intent are explicit.

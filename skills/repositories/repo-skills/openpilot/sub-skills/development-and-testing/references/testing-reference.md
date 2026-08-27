# Testing, Linting, and Docs Reference

## Test runner contract

openpilot's Python test runner accepts files, directories, dotted IDs, and `path.py::Class::test`-style targets. It supports worker control (`-j`), keyword filtering (`-k`), live output (`-s`), verbose output (`-v`), durations, and warning policy.

Examples to adapt in a target checkout:

```bash
python tools/test_runner.py openpilot/tools/lib/tests/test_route_library.py -j1
python tools/test_runner.py openpilot/common/tests/test_simple_kalman.py -j1
python tools/test_runner.py openpilot/selfdrive/controls/tests/test_longcontrol.py -j1
python tools/test_runner.py openpilot/selfdrive/car/tests/test_docs.py -j1
python tools/test_runner.py openpilot/selfdrive/car/tests/test_car_interfaces.py -k toyota -j1
```

Prefer focused targets over `tools/test_runner.py` with no target. The default traversal can collect many process, route, GUI, simulator, and hardware-sensitive tests.

## Native/hardware classification

| Candidate | Use when | Skip when |
| --- | --- | --- |
| `openpilot/common/tests/*` | Lightweight common behavior or setup smoke | Native extension prerequisites are missing |
| `openpilot/tools/lib/tests/test_route_library.py` | Route/segment parsing guidance changed | None; this is CPU-safe |
| `openpilot/tools/lib/tests/test_logreader.py` selected local cases | LogReader docs/scripts changed | Cases need network route downloads |
| `openpilot/cereal/messaging/tests/*` | msgq/cereal guidance changed | `msgq.ipc_pyx` is not built, or host C++ tools such as `clang++` are unavailable for generated-header checks |
| `openpilot/selfdrive/car/tests/test_docs.py` | car docs generation changed | opendbc import is broken |
| `openpilot/selfdrive/car/tests/test_car_interfaces.py` | car interface/port changes | Full all-platform fuzzing is too broad; use `-k` |
| `process_replay/test_processes.py` | process replay behavior changed and route data/cache are available | No network/cache/time budget |
| `test_onroad.py`, `test_power_draw.py`, hardware/comma tests | On comma/AGNOS hardware with explicit intent | Generic CPU host |
| PlotJuggler/Cabana/UI/simulator tests | Display, Qt, binary, route, or MetaDrive available | Headless/no GUI/no optional dep |

## Linting

The lint wrapper can run ruff, ty, codespell, indentation, shebang, large-file, and no-merge-comment checks. It supports fast mode and skipping named checks. Keep lint runs focused when a task edits a small area.

Common patterns:

```bash
bash scripts/lint/lint.sh --fast
bash scripts/lint/lint.sh ruff
bash scripts/lint/lint.sh --skip ty codespell
```

If lint tools are missing, verify the `testing` extra was installed. If lint reports a banned API such as `time.time`, follow the repo-specific rule in `pyproject.toml` rather than generic style advice.

## Docs validation

Use docs build when documentation files, supported cars docs, or site templates change. For car support table generation, see the car-port sub-skill.

Avoid launching a long-running docs server unless the user asks for a preview. A build check is enough for most agent verification.

## Release scripts

Release scripts and checklists are maintainer-only. They may mutate branches, build stripped artifacts, tag releases, or depend on Jenkins/staging branches. Mention them as context, but do not run them during ordinary skill verification.

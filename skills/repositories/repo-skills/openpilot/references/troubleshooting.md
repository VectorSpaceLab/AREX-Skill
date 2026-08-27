# openpilot Cross-Cutting Troubleshooting

Use this reference before diving into a sub-skill when the failure crosses setup, imports, native build products, route data, hardware, or safety boundaries.

## Import/setup failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'msgq.ipc_pyx'` | `msgq_repo` was not initialized or the Cython extension was not built. | Confirm submodules, then build `msgq_repo/msgq/ipc_pyx.so` and `msgq_repo/msgq/visionipc/visionipc_pyx.so` with SCons in the target checkout. |
| `libparams_c.so: cannot open shared object file` | `openpilot/common/libparams_c.so` was not built. | Build the SCons target for `openpilot/common/libparams_c.so`; avoid treating a pure `uv sync` as a complete runtime build. |
| `ModuleNotFoundError: opendbc` or mismatched car interfaces | Empty or stale `opendbc_repo` submodule, or Python path does not expose the submodule package. | Initialize submodules and re-sync the environment; keep opendbc aligned with the recorded openpilot submodule commit. |
| uv installs into `.venv` unexpectedly | uv project environment was not the intended prefix or active environment. | Use a deliberate private environment; inspect which Python `uv sync` used before trusting imports. |
| `capnp` duplicate schema errors | Mixing different opendbc/cereal package copies in one process. | Use one aligned openpilot checkout and submodule set. Avoid mixing PyPI `opendbc` with a different source checkout. |
| git-lfs or model files missing | Fresh shallow clone did not pull LFS artifacts. | Run the repo's documented LFS pull only when the selected task needs model/data artifacts. Log-analysis and many CPU tests do not need every LFS file. |

## Hardware, route, and GUI prerequisites

- A normal CPU host can inspect APIs, run many unit tests, parse local qlogs/rlogs, and generate car docs.
- Live car/device validation needs a comma device, AGNOS, Panda/Panda Jungle, or vehicle-specific setup. Do not claim it passed from CPU checks.
- Remote route workflows may require comma account authentication, public routes, network access, and cache space. Prefer local or synthetic qlog tests for routine verification.
- Cabana, PlotJuggler/JotPluggler, UI, and simulator workflows may need a display/Qt/OpenGL/MetaDrive. Use help/layout checks when GUI prerequisites are absent.
- Joystick and manual-control tools can write debug Params and publish control messages. Require explicit user intent and safe offroad/live-device state.

## State-mutating commands to avoid by default

Do not run these unless the user explicitly requests them and understands the effects:

- Branch/reset/update helpers such as `op switch`, update scripts, or release scripts.
- Device start/stop/restart/update flows.
- Params writers such as scripts that write `CarParams`, `JoystickDebugMode`, or persistent device state.
- Live CAN replay to Panda/Jungle hardware.
- Long process-replay reference updates or route downloads.

## Sub-skill routing for failures

- Setup/build/test/lint failures: [development-and-testing](../sub-skills/development-and-testing/SKILL.md).
- Route ID, LogReader, missing logs, cache, or message filtering failures: [route-log-analysis](../sub-skills/route-log-analysis/SKILL.md).
- Car fingerprints, missing signals, safety mismatches, controls, or process replay failures: [car-ports-and-controls](../sub-skills/car-ports-and-controls/SKILL.md).
- msgq/Params/manager/loggerd/service timing failures: [core-services-and-runtime](../sub-skills/core-services-and-runtime/SKILL.md).
- Replay/Cabana/PlotJuggler/simulator/joystick/UI failures: [simulator-and-visual-tools](../sub-skills/simulator-and-visual-tools/SKILL.md).

---
name: openpilot
description: "Guides development, route/log analysis, car-porting, runtime
  services, simulator, and visual-debug workflows for comma.ai openpilot."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# openpilot Repo Skill

Use this operating skill when a task involves the comma.ai **openpilot** repository, package, developer tooling, route logs, car ports, controls, runtime services, simulator, or visualization/debug tools. openpilot is an open source driver-assistance/robotics system with Python, C/C++, Cython, Cap'n Proto, SCons, uv, and several submodule packages such as opendbc and msgq.

Read [references/repo-provenance.md](references/repo-provenance.md) before treating this skill as current for a checkout. Read [references/troubleshooting.md](references/troubleshooting.md) first when installs, imports, native extensions, submodules, or hardware assumptions fail.

## First decisions

1. **Is the task about editing or validating the repo?** Use [development-and-testing](sub-skills/development-and-testing/SKILL.md).
2. **Is the task about route IDs, rlogs/qlogs, message filtering, alerts, or LogReader?** Use [route-log-analysis](sub-skills/route-log-analysis/SKILL.md).
3. **Is the task about a car port, fingerprint, DBC/opendbc interface, controller behavior, process replay, or maneuver report?** Use [car-ports-and-controls](sub-skills/car-ports-and-controls/SKILL.md).
4. **Is the task about cereal/msgq, Params, manager processes, loggerd/uploader/deleter, service timing, or hardware abstraction?** Use [core-services-and-runtime](sub-skills/core-services-and-runtime/SKILL.md).
5. **Is the task about replay, Cabana, PlotJuggler/JotPluggler, simulator, joystick, UI, camera streams, or CTF-style tool exploration?** Use [simulator-and-visual-tools](sub-skills/simulator-and-visual-tools/SKILL.md).

## Safe baseline setup for a target checkout

In a target openpilot checkout, prefer the repository's uv/SCons workflow and Python 3.12 line:

```bash
# Inspect before mutating anything
python3 --version
git submodule status

# Typical developer setup from a fresh checkout
uv sync --frozen --extra tools --extra testing
scons -u openpilot/common/libparams_c.so msgq_repo/msgq/ipc_pyx.so msgq_repo/msgq/visionipc/visionipc_pyx.so
```

Use the bundled [scripts/openpilot_skill_doctor.py](scripts/openpilot_skill_doctor.py) or the development sub-skill's [scripts/openpilot_dev_check.py](sub-skills/development-and-testing/scripts/openpilot_dev_check.py) to inspect a checkout without running mutable setup commands.

## Important constraints

- openpilot metadata requires Python `>=3.12.3,<3.13`.
- Empty submodule directories are a common cause of install/import failure. Required submodules include `msgq_repo`, `opendbc_repo`, `panda`, `rednose_repo`, `teleoprtc_repo`, and `tinygrad_repo`.
- Many imports need native outputs from SCons, especially `openpilot/common/libparams_c.so`, `msgq_repo/msgq/ipc_pyx.so`, and `msgq_repo/msgq/visionipc/visionipc_pyx.so`.
- A CPU developer host can validate package imports, route/log parsing, unit-test collection, car docs, and many controller tests. It cannot validate in-car safety, Panda USB, AGNOS, camera/encoder power, GUI, simulator, or authenticated remote-route behavior by itself.
- Treat live car/device commands, joystick control, `op switch`, updater/start/stop flows, and Params writes as state-mutating. Do not run them unless the user explicitly asks and prerequisites are clear.

## Sub-skill map

| Need | Read |
| --- | --- |
| Setup, build, lint, tests, docs, CI-like checks | [development-and-testing/SKILL.md](sub-skills/development-and-testing/SKILL.md) |
| Route/segment formats, LogReader, qlog/rlog summaries, filtering | [route-log-analysis/SKILL.md](sub-skills/route-log-analysis/SKILL.md) |
| Car porting, fingerprints, controls, process replay, maneuvers | [car-ports-and-controls/SKILL.md](sub-skills/car-ports-and-controls/SKILL.md) |
| cereal/msgq, Params, manager, loggerd, service diagnostics | [core-services-and-runtime/SKILL.md](sub-skills/core-services-and-runtime/SKILL.md) |
| Replay, Cabana, PlotJuggler, simulator, joystick, UI flags | [simulator-and-visual-tools/SKILL.md](sub-skills/simulator-and-visual-tools/SKILL.md) |

## Repo-level references and scripts

- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured router metadata for managed imports.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting failures and escalation rules.
- [scripts/openpilot_skill_doctor.py](scripts/openpilot_skill_doctor.py) checks a target checkout's structure and import/build prerequisites without mutating it.

## Verification posture

CPU import/build preparation was verified for the selected developer workflows. Hardware, remote-route network, GUI, and simulator capabilities are documented as optional or unverified unless the user provides the required device, route access, display, or dependency stack.

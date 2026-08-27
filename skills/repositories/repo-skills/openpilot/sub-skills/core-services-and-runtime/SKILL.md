---
name: core-services-and-runtime
description: "Guides cereal/msgq messaging, Params, manager processes, loggerd,
  service timing, and runtime service diagnostics in openpilot."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# core-services-and-runtime

Use this sub-skill for openpilot's runtime internals: cereal messaging, msgq pub/sub, `Params`, `managed_processes`, loggerd/uploader/deleter, hardware paths, service timing, and CPU-safe runtime diagnostics.

## Read first

- [references/messaging-and-params.md](references/messaging-and-params.md) for message/Params APIs and native-extension prerequisites.
- [references/service-runtime.md](references/service-runtime.md) for manager, loggerd, service timing, and filesystem path behavior.
- [references/troubleshooting.md](references/troubleshooting.md) for msgq/Params/native-extension/service failures.

## Bundled helpers

- [scripts/check_service_names.py](scripts/check_service_names.py): print service names, frequencies, and decimation information from `SERVICE_LIST`.
- [scripts/params_key_probe.py](scripts/params_key_probe.py): inspect known Params keys and default/type guidance without writing values.

## Workflow

1. Confirm the native extension state first. If `msgq.ipc_pyx` or `libparams_c.so` is missing, fix the build before deeper analysis.
2. Use `cereal.messaging` tests or helper scripts to understand socket/update semantics.
3. Treat `Params` writes as state-mutating; prefer read-only probes and clear warnings.
4. For loggerd/uploader/deleter or service timing, choose small focused tests and temporary directories.
5. For camera/encoder or full onroad tests, check whether hardware prerequisites are present; if not, document the skip instead of claiming failure.

## Boundaries

- Route route/log parsing questions to [route-log-analysis](../route-log-analysis/SKILL.md).
- Route car-interface and control behavior to [car-ports-and-controls](../car-ports-and-controls/SKILL.md).
- Route replay/simulator/GUI tools to [simulator-and-visual-tools](../simulator-and-visual-tools/SKILL.md).

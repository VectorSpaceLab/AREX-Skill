# Service Runtime Reference

## Runtime surfaces

This sub-skill covers openpilot's runtime service layer:

- `openpilot/system/manager/process_config.py` and `managed_processes`
- `openpilot/system/loggerd/*` uploader/deleter/configuration
- `openpilot/system/tests/test_logmessaged.py`
- `openpilot/system/loggerd/tests/*`
- `openpilot/selfdrive/test/test_onroad.py` and `test_power_draw.py`
- `openpilot/common/hardware/hw.py` path helpers
- `openpilot/common/hardware/comma/*` hardware-specific utilities

## Paths and environment

`Paths` helpers derive log, cache, config, and shared-memory roots from the host/device environment. Common pitfalls are:

- `LOG_ROOT` overriding the expected location.
- `OPENPILOT_PREFIX` influencing comma-home paths.
- Device vs PC branches changing `log_root`, `swaglog_root`, `persist_root`, and `config_root`.

## Loggerd workflows

Loggerd tests and runtime code validate:

- bootlog content and init metadata,
- segment rotation and encode outputs,
- upload ordering and xattrs,
- deletion order and preserve/lock behavior,
- logmessaged routing to file/socket outputs.

These workflows are safe to reason about on a CPU host, but many require temporary filesystem state and live managed processes.

## Service timing and diagnostics

`tools/scripts/watch_timings.py` and `tools/scripts/live_cpu_and_temp.py` monitor live services, CPU, memory, and temperature. They are useful diagnostics but run indefinitely and require a live openpilot runtime. Prefer a finite script or a unit test if the task only needs service names and expected frequencies.

# Process Replay Reference

Process replay runs selected openpilot processes against route logs and compares or saves resulting messages. Use it for regression analysis only after route access, environment, and native extensions are ready.

## Key controls

- Whitelist processes with options such as `--whitelist-procs controlsd`.
- Blacklist processes with options such as `--blacklist-procs modeld`.
- `run_process_on_route.py` replays a route through chosen processes and saves a new log file.
- `test_processes.py` compares replay output against reference logs and can update refs only when the full regression scope is intended.
- `test_fuzzy.py` fuzzes selected processes with synthetic messages; it is good for safety and edge-case reasoning, not route fidelity.

## Example workflow

```bash
python tools/scripts/run_process_on_route.py <route> --whitelist-procs controlsd
python tools/test_runner.py openpilot/selfdrive/test/process_replay/test_processes.py -k controlsd -j1
```

## Practical guidance

- Keep the process set small when diagnosing a port or runtime regression.
- Prefer a representative route and one process at a time before broadening the matrix.
- Use CPU-safe replay as an analysis tool; do not treat it as in-car validation.
- When reference artifacts are stale, update them deliberately and record the commit used for comparison.

# Development/testing troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import from checkout fails after source changes | Editable build not performed or compiled extensions stale | Reinstall/rebuild editable package in the test environment before pytest. |
| Cython extension compile fails | Missing compiler, Cython, NumPy/SciPy headers, Meson/Ninja, or incompatible Python | Install build dependencies and use a supported Python; prefer reproducible envs. |
| Pytest rejects configured options | Required pytest plugins from test extras are missing | Install test extras/plugins or run a minimal command with documented option overrides. |
| Focused tests pass but examples fail | Docs/examples depend on optional matplotlib, pandas-datareader, notebook tooling, or network | Install docs/example dependencies only when needed; avoid network-dependent examples by default. |
| Warning becomes error in tests | Project warning filters intentionally turn selected warnings into failures | Fix the warning cause or update policy deliberately; do not silence broadly. |
| Release/deploy script looks relevant | Maintainer-only side effects, credentials, or external services | Do not run release/deploy tooling unless the user explicitly authorizes that maintenance task. |

# Extension Development Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `check_estimator` constructor failure | Parameters not written to `self`, mutable defaults, or no test params | Fix constructor contract and add low-runtime `get_test_params`. |
| Public method override breaks tests | Base class validation/conversion bypassed | Move logic into private hooks and tags. |
| Input conversion mismatch | Wrong `X_inner_mtype` or `y_inner_mtype` tag | Set inner mtype tags to what private hooks actually accept. |
| Missing dependency at import time | Soft dependency imported at module level | Move import into method and set dependency tags. |
| Fitted state failure | Private hook did not set fitted attributes or return `self` | Store learned state with trailing `_` and return `self` from `_fit`. |
| Test too slow | Defaults too large | Provide small `get_test_params` and use focused checks first. |

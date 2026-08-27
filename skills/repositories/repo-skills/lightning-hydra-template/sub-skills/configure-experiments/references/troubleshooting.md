# Configuration Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `MissingConfigException: Could not find ...` | Wrong config group option, removed YAML, or defaults list references a file that no longer exists. | Run `render_config_summary.py --list-groups`; fix the defaults entry or CLI override. |
| `Key 'x' is not in struct` | Adding a new key without Hydra's `+` prefix or with strict structured config behavior. | Use `+path.to.key=value` for new keys, or add the key to the correct config YAML. |
| `InterpolationResolutionError` for `${paths.root_dir}` | `PROJECT_ROOT` is absent or rootutils did not run. | Use entry points that call rootutils, or set `cfg.paths.root_dir` in tests/scripts after composition. |
| Tag prompt blocks CI or non-interactive runs | `extras.enforce_tags=True` and `tags=[]`. | Set `extras.enforce_tags=false` for automation or provide non-empty `tags=[...]`. |
| `optimized_metric` not found | Hparam search or `get_metric_value` asks for a metric key the model never logged. | Use the default `val/acc_best` only if the model logs it; update model logging or `optimized_metric`. |
| Online logger config fails during a config smoke | Logger package missing or credential env var absent. | Use `logger=null` or `logger=csv` for smoke tests; install/configure online loggers only for real tracking runs. |
| `_target_` import fails after package rename | Config still points to `src.*`. | Run `check_hydra_targets.py` from the data/model sub-skill and update every stale target. |
| Sweep tests skip unexpectedly | Optional `sh` package unavailable, Windows platform, or optional logger package missing. | Use `select_smoke_tests.py` from the maintenance sub-skill to choose the right profile. |

## Stop conditions

Stop and ask for user/environment input when a requested sweep requires external services, cluster launchers, online logger credentials, large data downloads, or hardware-specific trainer execution that is not available in the current environment.

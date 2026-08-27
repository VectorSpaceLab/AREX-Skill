# Mobile-Agent-E Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: provide either instruction or tasks_json` | Both or neither task input supplied | Use exactly one of `--instruction` or `--tasks_json`. |
| Task JSON accepted but behavior mismatches expectation | Bare list loses scenario metadata or tasks missing app context | Use object root with `length`, `scenario`, `scenario_id`, and `tasks`; validate with the bundled validator. |
| Evolution repeats the same action then stops | Model/perception loop stuck; `max_repetitive_actions` triggered | Inspect task logs and screenshots; seed corrected tips/shortcuts; retry one task in individual mode first. |
| Consecutive failures stop a task | `max_consecutive_failures` reached | Inspect failure cause before raising the limit. Often ADB, typing, or API output format is wrong. |
| Persistent tips seem stale | Reusing an old `log_root/run_name` | Use a new private run name, delete/reset persistent files intentionally, or seed corrected files. |
| Live run cannot see phone | ADB path/device config in runtime checkout is wrong | Verify ADB/device authorization before running; command builder does not connect. |
| Model or perception import fails | Runtime dependencies/config not installed | Prepare only the Mobile-Agent-E environment, not the whole monorepo. |
| Logs contain user data | Screen/task logs and memory files persist private content | Use private log roots and redact before sharing. |

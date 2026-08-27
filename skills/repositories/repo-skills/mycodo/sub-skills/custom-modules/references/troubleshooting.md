# Custom Module Troubleshooting

Read this when a custom Input, Output, Function, Action, or Widget fails validation, import, update, activation, or runtime behavior.

## Validation/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Validator says metadata dictionary missing | wrong dictionary name for kind, dictionary built dynamically, syntax error | use the exact contract name; keep top-level metadata inspectable when possible |
| Upload/import fails immediately | syntax error, missing required import, side effect at import time, wrong class name | run static validator; move hardware imports into `initialize()`; check Mycodo logs |
| Module appears as a different module | unique name changed | restore original unique name for updates or intentionally add as new module |
| Dependency prompt repeats | dependency tuple wrong, package unavailable on architecture, apt/pip install failed | inspect dependency log; install only selected dependency; verify import on target host |
| Custom options not visible | `custom_options` malformed, option type unsupported, missing `options_enabled` | compare with contract and examples; validate option ids/types/defaults |

## Runtime failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Input activates but stores no values | missing measurement/unit, `get_measurement()` returns wrong shape, channel mismatch | verify `measurements_dict`, UI measurement selection, and returned channel indices |
| Output activates but state unknown | `is_on()`/`output_states` not implemented consistently, wrong channel | implement channel-aware `is_on()` and update `output_states` in `output_switch()` |
| Function loop never runs | period/start offset logic wrong, initialization failed, controller inactive | log `initialize()` and `loop()` timings; validate custom options and daemon status |
| Function status widget blank | `function_status()` missing wrong return shape | return `{'string_status': ..., 'error': [...]}` style data |
| Action fails with missing measurement | selected measurement not configured or `dict_vars['value'][channel]` absent | add defensive checks and user-facing message; verify action application |
| Widget renders blank | endpoint/template/static asset mismatch, JavaScript error, missing data | inspect frontend log/browser console; simplify widget render path |

## Unsafe patterns to remove

- Top-level code that opens serial/GPIO/I2C/camera devices.
- Top-level code that starts threads, subprocesses, or network clients.
- Hard-coded API keys, passwords, Wi-Fi credentials, or private paths.
- Broad `except: pass` hiding hardware or database errors.
- Command execution from user input without validation.
- Dependencies copied from an unrelated example.

## When to restart

Frontend reload may be enough for some UI updates, but active controller code changes often require daemon restart/reload. Restarting the daemon can stop live control. Confirm safe Output/PID state before approving a restart on a real system.

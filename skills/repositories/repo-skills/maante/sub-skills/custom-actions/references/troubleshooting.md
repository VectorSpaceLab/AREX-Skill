# Custom Action Troubleshooting

## Unknown Custom Action or Recognition

Symptoms:

- Pipeline reaches a `Custom` node and MaaFramework reports the action/recognition is missing.
- A new class works in direct imports but not in the running agent.

Checks:

1. Decorator name equals the Pipeline string exactly.
2. Module is imported from `agent/custom/action/__init__.py`.
3. Class is included in `__all__` if the package exposes it as part of the public action surface.
4. The module import does not fail due to optional/platform dependencies before registration.

Run:

```bash
python sub-skills/custom-actions/scripts/check_custom_action_registry.py --repo-root .
```

## Import Fails on Linux but Runtime is Windows

Symptoms:

- `ctypes.windll` missing.
- `soundcard` asserts or cannot connect to PulseAudio/PipeWire.
- Coordinate `.pyd` cannot load.

Do not convert these into source bugs automatically. Determine whether the import happens too early for a cross-platform static check. For runtime behavior, MaaNTE is Windows-oriented and may legitimately require Windows APIs, audio loopback, or a packaged ABI-specific module. For import-time registry stability, consider moving platform-specific access into runtime methods or guarding it with clearer error messages.

## Long Loop Never Stops

Symptoms:

- User presses stop but keys remain held.
- Task continues after stop signal.
- WebSocket/audio/OpenCV resources linger.

Fix pattern:

```python
try:
    while not context.tasker.stopping:
        ...
finally:
    release_controls()
    close_services()
```

Use short sleeps with stop polling, not one long `time.sleep()` inside critical loops.

## Parameter Parsing Bugs

Symptoms:

- `AttributeError: 'str' object has no attribute 'get'`.
- JSON decode traceback from empty parameter.
- Option values arrive as strings but code expects numbers/bools.

Use a normalization helper, then cast each value with defaults and error handling. For bool options, accept true/false, numeric, and common string forms if user-facing config can pass strings.

## Direct Recognition Returns Unexpected Result

Symptoms:

- `result.status == 0` logic fails after MaaFramework binding changes.
- Code sees `result` but `result.hit` is false.

Use compatibility checks like PinkPaw Core3 `_is_hit`: check `status.succeeded` if present, then numeric status, then `hit` as a last resort. Avoid relying on only one representation across all MaaFramework versions.

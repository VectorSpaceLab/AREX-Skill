# Logging and User Messages

## Purpose

Use this reference when adding or reviewing MaaNTE Python logs and user-visible progress messages.

## Logger Stack

`agent/utils/logger.py` configures a unified `logger` object:

- Prefer `loguru` when installed.
- Fall back to standard `logging` with a rotating file handler.
- Console formatting changes by PI client:
  - MXU outputs HTML-colored messages and usually hides INFO/DEBUG from users.
  - MFAAvalonia uses short level prefixes.
  - Other contexts use ANSI colors.
- File logs are retained for about two weeks under the debug/custom log area in the runtime package.

Import pattern:

```python
from utils.logger import logger
```

Some action submodules use `custom.action.Common.logger.get_logger(__name__)` to preserve module names; this is also acceptable.

## Developer Logs vs User Messages

Use developer logs for diagnostics:

```python
logger.debug("识别结果: score=%.2f", score)
logger.warning("模板缺失，功能降级: %s", template_name)
logger.error("动作失败: %s", exc)
```

Use maafocus for messages the user should see in MXU/MaaFramework task output:

```python
from utils.maafocus import PrintT
PrintT(context, "sound_dodge.started")
```

For raw text where no translation key exists:

```python
from utils.maafocus import Print
Print(context, "Dataset recorder started: ...")
```

Do not rely on `logger.info()` for user-facing status because MXU can suppress INFO-level console output.

## Formatting Rules

- Prefer `%`-style placeholders in logger calls.
- Avoid f-strings in logger calls when following repository style.
- Do not log API keys, private file paths, or sensitive config values.
- Avoid high-volume INFO logs in per-frame loops; use DEBUG/TRACE-style diagnostics or interval throttling.
- For exceptions, include enough context to identify action, node, parameter, or backend.

Good:

```python
logger.info("Navi coordinate capture started: backend=%s", backend)
logger.debug("候选丢弃: lane=%s target=%.3f reason=min_interval", lane, target)
logger.warning("Invalid sound dodge config: %s", exc)
```

Bad:

```python
print("task started")
logger.info(f"API key={api_key}")
logger.info("frame=" + str(frame))
```

## Focus Message Notes

`utils.maafocus.Print` implements a temporary Pipeline action override for `_MAANTE_FOCUS_` and emits MaaFramework focus events. It catches failures and logs a warning instead of crashing the action.

Use `PrintT(context, key, *args)` when a translation key exists. If you add new keys, update the appropriate locale files.

## Known Current Inconsistencies

Some existing modules still use `print()` for developer/demo output or dataset recorder status. Treat these as existing behavior; when modifying nearby code, prefer `logger` plus `Print`/`PrintT` for new messages rather than expanding raw `print()` usage.

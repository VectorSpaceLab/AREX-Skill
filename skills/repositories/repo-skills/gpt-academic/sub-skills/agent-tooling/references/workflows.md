# Agent Tooling Workflows

## Void Terminal

Void Terminal maps natural-language intent to GPT Academic actions such as calling plugins or changing configuration. It is useful when the user does not know the exact plugin name, but it can also be risky because intents like “modify API key” or “clear cache” are writes.

Safe flow:

1. Restate the intended action and the target plugin/config/file.
2. If the action is a write, ask for explicit confirmation and require a backup where appropriate.
3. Prefer direct domain plugin guidance when the desired plugin is obvious.
4. Keep secrets out of chat; tell the user to edit `config_private.py` locally instead of pasting keys.

## Code Interpreter

Use Code Interpreter when GPT Academic should generate and run Python over an uploaded file or small dataset. Confirm:

- the file path is visible to the server;
- code execution is acceptable to the user;
- output files and side effects are expected;
- dependencies are installed or can be safely installed with approval.

Do not use it for untrusted destructive code, broad filesystem scans, credential extraction, or long-running jobs.

## Commandline Assistant

Use this when the user wants command help or controlled shell execution. In agent form, separate command generation from execution: show the command, explain side effects, and ask before running anything destructive or network-heavy.

## Dynamic function generation

Dynamic function demos can generate custom plugin-like behavior. Treat these as experimental: scope inputs tightly, avoid broad permissions, and prefer existing plugins when available.

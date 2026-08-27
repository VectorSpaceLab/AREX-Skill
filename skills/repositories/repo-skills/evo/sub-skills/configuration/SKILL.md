---
name: configuration
description: "Routes evo package-info, settings, logfile, and IPython shell workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# configuration

Use this sub-skill for the non-trajectory, non-metric, non-result workflows around evo's global settings, package metadata, logfile access, and preloaded IPython shell.

## Routes here
- `evo_config show`, `set`, `generate`, `reset`
- `evo pkg --info`, `--version`, `--pyversion`, `--license`, `--location`, `--logfile`, `--open_log`, `--clear_log`
- `evo cat_log`
- `evo_ipython`

## Do not use for
- Trajectory, metric, or result semantics. Route those to the dedicated workflow sub-skills.
- Custom application embedding or notebook recipes. Route those to `../python-api/SKILL.md`, except for simple cross-links.
- Implicit or hidden settings mutations. Keep edits explicit and user-confirmed.

## Start here
1. Read `references/cli-reference.md` for exact flags and output shapes.
2. Read `references/settings.md` for settings paths, default values, and merge/reset rules.
3. Use `references/workflows.md` for noninteractive recipes.
4. Use `references/troubleshooting.md` when a command fails or behaves unexpectedly.

## Safe operating rules
- The package settings file is `~/.evo/settings.json`; the global logfile is `~/.evo/evo.log`.
- `show --brief --no_color` is the safest read-only settings check.
- `generate` is read-only unless you pass `-o/--out`.
- `set` and `reset` mutate the chosen settings file and require write access.
- `evo_ipython` requires IPython on PATH and will create the `evo` profile on first launch if needed.
- `evo cat_log` is unavailable on Windows.
- The interactive source-tree demo `test/demos/config_demo.sh` was intentionally not bundled because it mutates settings and waits for stdin; the CLI recipes above are the safe replacement.

## Bundled helper
No `scripts/config_smoke.py` is bundled. The safe verification paths are already covered by the CLI itself (`show`, `generate`, `pkg`, `cat_log`, `evo_ipython`), and a helper that edits settings would add mutation risk without adding safety.

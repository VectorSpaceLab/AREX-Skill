---
name: simulator-and-visual-tools
description: "Guides replay, Cabana, PlotJuggler/JotPluggler, simulator,
  joystick, UI, camera-stream, and visual-debug workflows in openpilot."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# simulator-and-visual-tools

Use this sub-skill for route replay, Cabana, PlotJuggler/JotPluggler, simulator bridge, joystick debug, UI flags, camera-stream helpers, and CTF/tool exploration.

## Read first

- [references/replay-visualization.md](references/replay-visualization.md) for replay, Cabana, PlotJuggler, and camera/watch workflows.
- [references/simulator-and-joystick.md](references/simulator-and-joystick.md) for MetaDrive, keyboard/joystick control, and offroad/device safety.
- [references/ui-debugging.md](references/ui-debugging.md) for raylib UI flags and widget style guidance.
- [references/troubleshooting.md](references/troubleshooting.md) for auth, route, GUI, display, binary, and optional-dependency failures.

## Bundled helper

- [scripts/plan_visual_tool_command.py](scripts/plan_visual_tool_command.py): print a finite recommendation for replay/Cabana/PlotJuggler/simulator/joystick commands and prerequisites without launching long-running tools.

## Workflow boundaries

- For route parsing, local log access, or log summaries, use [route-log-analysis](../route-log-analysis/SKILL.md).
- For car-port or process-replay validation using routes, use [car-ports-and-controls](../car-ports-and-controls/SKILL.md).
- For device/stateful commands such as start/stop/update or Params writes, require explicit user intent and safety preconditions.

## Safe use

Most visual tools are optional and can be help-checked from the command line, but actual replay/simulator/GUI usage can require routes, auth, display, Qt, PlotJuggler binaries, or MetaDrive. Treat those as separate prerequisites rather than assuming a CPU import proves they work.

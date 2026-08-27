# UI Debugging Reference

The openpilot UI uses raylib. Useful environment flags documented by the repo include:

- `BIG=1` for the comma 3X UI.
- `SHOW_FPS=1` to show frame rate.
- `STRICT_MODE=1` to exit on large frame drops.
- `SCALE=1.5` to scale the UI.
- `BURN_IN=1` for burn-in heatmap.
- `GRID=50` for grid overlay.
- `MAGIC_DEBUG=1` for dropped frames on device.
- `RECORD=1` and `RECORD_OUTPUT` for screen recording.

UI development should follow the widget-oriented style guide in the repo docs: graphical elements should subclass `Widget`, and internal names should be prefixed with `_`.

For agent tasks, this means:

- Use help/layout checks or static inspection when the display stack is unavailable.
- Treat actual GUI launch as optional and environment-sensitive.
- Route UI-specific bug fixes to the UI module, but keep this sub-skill as the router for launch/debug flags and visual-tool selection.

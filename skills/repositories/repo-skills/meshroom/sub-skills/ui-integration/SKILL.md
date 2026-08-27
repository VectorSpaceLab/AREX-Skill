---
name: ui-integration
description: "Guides Meshroom PySide6/QML application startup, Scene/UIGraph
  integration, QML imports, viewers, status monitoring, and display-dependent
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom UI Integration

Use this route for launching Meshroom's desktop UI, inspecting `MeshroomApp`, connecting QML to the graph/scene model, or diagnosing PySide6/QML/display failures.

## Read First

- [UI reference](references/ui-reference.md)
- [QML and scene workflows](references/qml-and-scene-workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- Run [scripts/check_ui_imports.py](scripts/check_ui_imports.py) for headless import/QML-path checks; it does not start the event loop by default.

## Launch Choices

```bash
# Source checkout, Unix-like
PYTHONPATH=$PWD python meshroom/ui
# or
./start.sh
```

The UI parser accepts an optional project `.mg` path or image folder plus `--import`, `--importRecursive`, `--save`, `--new`, `--latest`, `--output`, `--pipeline`, `--submitLabel`, and `--env-help`.

## Initialization Model

`MeshroomApp` initializes pipelines, parses arguments, initializes PySide6, registers UI component types, creates a `QmlInstantEngine`, creates a `Scene`/`UIGraph`, and exposes graph/viewer helpers as QML context properties. The UI is a bridge over the core graph engine, not a second graph implementation.

## Headless Boundary

- Importing `meshroom.ui.app` verifies Python/PySide6 module compatibility only.
- Full launch can require a display server, OpenGL/native drivers, QML Scene3D modules, and optional QtAliceVision plugins.
- Use `MESHROOM_OUTPUT_QML_WARNINGS=1` when the only visible message is `QQmlApplicationEngine failed to load component`.
- Use `MESHROOM_INSTANT_CODING=1` only during QML development; it enables file watching/reload and adds resource overhead.

For graph mutation, serialization, and status semantics route to [core-graph-engine](../core-graph-engine/SKILL.md). For CLI startup/import/save options route to [cli-pipeline-execution](../cli-pipeline-execution/SKILL.md).

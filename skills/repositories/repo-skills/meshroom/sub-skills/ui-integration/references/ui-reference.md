# Meshroom UI Reference

## Startup Parser

`meshroom.ui.app.createMeshroomParser(args)` returns the UI argument namespace. `MeshroomApp(inputArgs)` initializes the application and event loop is started by `meshroom/ui/__main__.py`.

Useful startup forms:

```bash
meshroom project.mg
meshroom --new
meshroom --pipeline photogrammetry --import /images --save /work/project.mg
meshroom --importRecursive /dataset --output /results
meshroom --env-help
```

A project positional argument must be an existing file; a folder should be passed through `--import`/`--importRecursive`. Saving a new project refuses to overwrite an existing `.mg` file and expects the parent path to exist.

## UI/Core Bridge

- `Scene` owns the active project and wraps a `UIGraph`.
- `UIGraph` exposes core `Graph` state through Qt models, commands, and task-manager integration.
- `NodeStatusMonitor` polls node/chunk status files so local or externally submitted jobs can update the UI.
- `QmlInstantEngine` can watch QML/JS files and reload the component during development.
- `MeshroomApp` exposes `_currentScene`, `_nodeTypes`, `Filepath`, `Scene3DHelper`, `Transformations3DHelper`, `Clipboard`, `ThumbnailCache`, and other helpers to QML context.

## QML Import Paths

The app adds its bundled QML directory and the PySide6 `Qt/qml` directory to the QML import path. Optional QtAliceVision plugins add their own `QML2_IMPORT_PATH`/`QT_PLUGIN_PATH` entries.

## Logging

Qt messages are routed through Python logging where supported. QML warnings are intentionally filtered unless `MESHROOM_OUTPUT_QML_WARNINGS` is truthy. When debugging a component load failure, enable warnings before changing unrelated graph code.

## Recent Projects

Recent project paths are stored through `QSettings`. Meshroom attempts to retrieve a thumbnail from the first CameraInit viewpoint when the project is readable; missing/corrupt files remain in the list with a missing/error status and are not a graph engine failure.

# QML and Scene Workflows

## Opening or Creating a Project

- Pass an existing `.mg` file positionally to load it.
- Use `--new` to create an empty scene.
- Use `--pipeline NAME` to select a template for a new scene.
- Use `--import` or `--importRecursive` to populate input nodes from files/folders.
- Use `--save PATH` to persist a newly created scene; output folders can be configured with `--output` when output nodes are retained.
- `--latest`, `--latest2`, and `--latest3` select recent projects stored in QSettings.

## QML Development

When editing QML/JS in a development checkout:

1. Set `MESHROOM_INSTANT_CODING=1`.
2. Start the UI with detailed logging.
3. Keep the watched tree limited to the QML source to reduce reload overhead.
4. If a save operation deletes/replaces a file, let `QmlInstantEngine` re-add it after the short reload cooldown.
5. Disable instant coding for production runs.

## Scene Status and External Jobs

The UI does not assume all status changes happen in-process. `NodeStatusMonitor` polls status files for submitted/external jobs and updates the scene when the files change. If the UI shows stale status:

1. verify the graph's cache/status files are on a shared/visible filesystem;
2. inspect `meshroom_status` from the same project/cache;
3. check whether the poller is disabled or in minimal mode;
4. reload the project only after preserving current unsaved edits.

## Viewer Boundary

2D/3D viewers consume output paths and reconstruction metadata from active nodes. Viewer import failures can be caused by missing Qt3D/QtAliceVision modules or invalid output files even when graph computation succeeded. Separate graph status, output existence, and viewer plugin errors when diagnosing.

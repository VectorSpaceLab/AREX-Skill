# UI Integration Troubleshooting

- **`ModuleNotFoundError: PySide6`:** install the runtime requirements in the same Python that launches Meshroom; do not mix system Python and a source-checkout environment.
- **`QQmlApplicationEngine failed to load component`:** set `MESHROOM_OUTPUT_QML_WARNINGS=1`; the suppressed warning normally names the missing import/file.
- **QtQuick Scene3D plugin missing:** PySide6's Qt distribution may lack a platform-specific Scene3D library. Install the documented system package or compatible Qt/PySide6 component before debugging Meshroom QML.
- **Window does not open but import passes:** check `DISPLAY`/Wayland, OpenGL/native driver libraries, and Qt platform plugins. Importing `meshroom.ui.app` is not a GUI smoke test.
- **Viewer is blank after successful compute:** distinguish missing output files, unsupported format/QtAliceVision plugin, and graph status. Inspect output paths and viewer logs separately.
- **Recent project thumbnail is missing:** the project may be unreadable, malformed JSON, missing CameraInit viewpoints, or the image path may no longer exist. The project can still load without a thumbnail.
- **QML changes do not reload:** verify `MESHROOM_INSTANT_CODING=1`, that files are within the watched QML tree, and that the editor save operation eventually recreates the file.
- **UI shows stale remote status:** ensure the status files are visible and modified on the shared filesystem; then inspect poller mode and use `meshroom_status` before restarting the UI.

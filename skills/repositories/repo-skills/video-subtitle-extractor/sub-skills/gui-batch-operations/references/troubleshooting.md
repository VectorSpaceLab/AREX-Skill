# GUI Troubleshooting

## GUI does not launch

- Confirm PySide6, qfluentwidgets, and qframelesswindow dependencies are
  installed.
- Do not launch GUI in a headless environment unless a display server is
  available; use source CLI/planning helpers instead.
- If icons/assets are missing, run from a complete VSE source checkout or
  official release bundle.

## Opened video has wrong preview or selection

- Confirm OpenCV can read the first frame.
- Re-draw the selection after resizing or changing videos.
- For batch runs, ensure videos share the same resolution if reusing a selection.

## Output file not found

By default, task output is beside the input video. If Save Directory is set, the
output is in that directory. The context menu only opens subtitle location after
the task is completed.

## Stop button leaves processes running

The GUI tracks process objects and PIDs, then terminates child process groups.
If a platform binary ignores termination, kill the process group externally,
clear temporary caches, and retry with simpler paths or fewer worker cores.

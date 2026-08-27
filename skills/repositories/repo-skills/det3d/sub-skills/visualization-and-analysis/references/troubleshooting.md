# Visualization Troubleshooting

- **Qt/X display error**: use a non-interactive backend or
  `QT_QPA_PLATFORM=offscreen`, save files, and avoid `--show`.
- **VTK/Open3D import error**: install the optional visualization dependency only
  for that workflow; log analysis and core inference should remain headless.
- **Boxes appear rotated/offset**: verify coordinate frame, calibration,
  dimension order, yaw convention, and center convention before changing data.
- **Empty rendering**: inspect score threshold, class filter, point range, and
  whether predictions were accumulated from all ranks.
- **Malformed JSON log**: parse line by line, record skipped lines, and do not
  treat a partially written final line as a zero-valued metric.
- **FLOPs build failure**: route missing `spconv`/extensions or config-builder
  problems to `runtime-ops` and `configuration-and-models`.

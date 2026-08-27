# Annotation UI Troubleshooting

## Launch and display problems

| Symptom | Likely cause | Action |
|---|---|---|
| GUI fails on a headless server with Qt platform errors. | No graphical display or Qt platform plugin cannot connect. | Use a real desktop, virtual display, or X/Wayland forwarding. For noninteractive checks, use the bundled preview script instead of launching the GUI. |
| WSL/Wayland launch reports xcb/wayland plugin problems. | Qt picked a platform that does not match the available display bridge. | Try `xanylabeling --qt-platform xcb`. Ensure an X server/display is running and `DISPLAY`/Wayland variables match your environment. |
| Very large image fails to display or reports allocation limit. | Qt image allocation limit defaults to 256 MB. | Launch with `--qt-image-allocation-limit 0` to disable or set a larger MB value. Keep imageData embedding off for large datasets. |
| GUI opens with broken layout or stale window state. | Persisted Qt settings became inconsistent. | Run `xanylabeling --reset-config`, then relaunch. |
| Non-fatal PipeWire/QtMultimedia warnings appear. | Local multimedia stack prints warnings while Qt probes audio/video services. | Ignore if image annotation and video playback/export still work. Act only if video loading/playback fails; then check multimedia packages and ffmpeg availability. |

## Config and label validation

| Symptom | Likely cause | Action |
|---|---|---|
| `--config` value is treated unexpectedly. | Values that parse as YAML mappings are inline config; other values are opened as file paths. Invalid YAML can fail before path fallback. | For inline config, pass a valid mapping string. For a path, pass a path that is not itself a YAML mapping literal and ensure the file exists. |
| Warnings say config keys are skipped. | The config contains keys not present in the default configuration. | Remove or rename unexpected keys. Skipped keys are not applied. |
| Launch exits with label-validation error. | `validate_label`/`--validatelabel exact` is enabled but no labels were configured. | Provide `--labels label1,label2`, `--labels classes.txt`, or config `labels: [...]`; then relaunch. |
| Duplicate labels are rejected. | Config validation rejects duplicate `labels` entries. | Deduplicate class lists. Preserve intended order with `--nosortlabels` if needed. |
| A new/edit label is rejected in the dialog. | Exact validation is active and the label is not in the configured unique label list. | Add the label to the list first, correct spelling/case, or disable exact validation for exploratory labeling. |
| Attribute upload/config is rejected. | Attribute config shape is invalid, widget type is unsupported, or group-id widget options are not empty. | Use label-to-attribute mappings, supported widget types, unique labels, and empty option lists for group-id selectors. |

## Label JSON and media problems

| Symptom | Likely cause | Action |
|---|---|---|
| Label file opens with “valid label file” error. | JSON is malformed, shape fields have invalid types, bad `kie_linking`, or image bytes/path cannot load. | Validate JSON syntax, ensure `shapes` is a list, ensure `kie_linking` is a list of integer pairs, and confirm the image exists or `imageData` is valid. |
| Image cannot be found when labels are in a separate directory. | `imagePath` is relative to the label file directory and no longer points to the image. | Restore the relative image layout, regenerate labels with the correct output directory, or update `imagePath` carefully. |
| Labels are huge and slow to diff/load. | `imageData` embeds base64 image bytes. | Turn off Save With Image Data or launch with `--nodata`. For existing labels, remove `imageData` only if `imagePath` still resolves to the image. |
| Image dimensions in JSON do not match image. | File was resized/replaced or imageData and fields disagree. | Reload/save in the GUI to refresh dimensions, or update `imageHeight`/`imageWidth` to actual image size. |
| Corrupt/truncated images cause load failures. | Image reader cannot decode bytes or Pillow flags a decompression issue. | Re-export the image, reduce image size, or remove the bad sample from the active list before batch review. |

## Canvas/editing surprises

| Symptom | Likely cause | Action |
|---|---|---|
| Shape can be selected but not moved, resized, brush-edited, or deleted. | Shape is locked. | Use the canvas or Shapes-panel context menu to unlock it. Locked shapes still allow label/attribute edits. |
| Pose/keypoint export associates keypoints with the wrong object. | Box and keypoints use different or missing `group_id` values. | Assign the same group id to all shapes belonging to one object. Use Group ID Manager for batch repair. |
| Search results look incomplete. | File list is filtered by text, index, regex, or attribute search. | Clear the search box and any label/group filters. Remember `checked::false` includes images with no label files. |
| Some shapes disappear on canvas. | Label Manager visibility, global shape visibility, label/group filter, or hidden selected-shape state is active. | Use `Ctrl+H`, Label Manager visibility, Show Hidden Shapes (`W`), and shape-list filters to restore visibility. |
| Magic wand creates noisy polygons. | Color tolerance or local region is too broad/narrow. | Drag less/more to adjust tolerance; cancel with `Esc`; confirm only when preview matches the object. Adjust after creation with polygon/brush-edit tools. |
| Brush edit changes are lost. | Brush edit was canceled by `Esc`, image switch, or tool switch before commit. | Right-click or turn off Edit Brush to commit; use stroke undo/redo while still in brush edit. |
| Rectangle wheel editing does nothing. | Hover auto-highlight disables wheel rectangle editing. | Disable hover auto-highlight or use handles instead. |

## Video classifier issues

| Symptom | Likely cause | Action |
|---|---|---|
| Video sidecar is ignored. | Sidecar `type` is present and not `video_classification`. | Use a video-classifier sidecar with `type: "video_classification"`, or keep unrelated JSON sidecars separate. |
| Sidecar load reports unsupported version. | `version` differs from the supported sidecar schema version. | Back up the sidecar, then migrate fields to the supported schema before loading. |
| Sidecar load reports invalid schema. | `labels` is not an array, `label_colors` is not an object, `segments` is not an array, or segment timing fields are not integers. | Repair those fields. Invalid segment entries may be skipped or rejected depending on the error. |
| Dataset export fails. | `ffmpeg` cannot be found or a segment/media path is invalid. | Install/provide a system ffmpeg or `imageio-ffmpeg`, verify video path, and ensure segments have non-empty labels and valid time ranges. |

## Preview script diagnosis

The bundled `scripts/preview_xlabel_annotations.py` never installs packages.
It exits clearly if required packages are unavailable.

| Symptom | Likely cause | Action |
|---|---|---|
| Script says `cv2` or `numpy` is missing. | Preview dependencies are not installed in the current Python environment. | Install `opencv-python` and `numpy` in an appropriate environment, or use the GUI preview. The script will not auto-install. |
| No shapes appear in previews. | `--classes` or `--shape-types` filtered them out, labels are missing, or label JSON has no matching shapes. | Re-run without filters, inspect skipped-label warnings, and verify label files are matched by image stem. |
| Script exits with JSON errors. | One or more label files are malformed. | Open the reported label, fix syntax/schema, and re-run. Valid images may still have preview frames written before the nonzero exit. |
| Video preview fails after image previews succeed. | Output frames differ in size or VideoWriter cannot open the requested path/codec. | Use a writable `.mp4` path; the script resizes frames to the first preview size but cannot fix an unavailable codec. |

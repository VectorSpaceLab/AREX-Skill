# Deployment troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `CUDA_VER is not set` | Build invoked before selecting the DeepStream release | Export the matching `CUDA_VER` and rerun the build wrapper |
| `deepstream-app: command not found` | DeepStream SDK not installed or not on PATH | Install or activate the DeepStream runtime before trying the app command |
| Build succeeds but the app keeps rebuilding the engine | Wrong `model-engine-file`, batch size, or precision | Match the engine path and the config template to the exact model family |
| Boxes are shifted or clipped | Wrong resize/padding settings | Compare `maintain-aspect-ratio` and `symmetric-padding` against the family matrix |
| Output labels are wrong | `labels.txt` does not match the exporter output or the class count | Regenerate the labels file and correct `num-detected-classes` |
| GStreamer / GLib error on startup | Host GLib or multimedia stack issue | Follow the root troubleshooting note for the GLib or RTSP fix |

## When to stop and reroute

- If the checkpoint still needs conversion, stop here and route to `model-conversion`.
- If the app needs more than one detector, stop here and route to `multi-gie`.
- If the problem is calibration or NMS tuning, stop here and route to `int8-benchmarking`.

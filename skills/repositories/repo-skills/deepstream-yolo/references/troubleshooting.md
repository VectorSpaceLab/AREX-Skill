# Troubleshooting

## Build and runtime blockers

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `deepstream-app: command not found` | DeepStream SDK is not installed or not on PATH | Install the matching DeepStream stack and rerun the deployment checks |
| `CUDA_VER is not set` | The build wrapper or `make` was launched without the required version variable | Export the correct `CUDA_VER` for the chosen DeepStream release before building |
| Build fails in `nvdsinfer_custom_impl_Yolo` | CUDA toolkit, DeepStream headers, or compiler mismatch | Recheck the version matrix and run the build wrapper again |
| `GLib (gthread-posix.c): Unexpected error from C library during 'pthread_setspecific': Invalid argument. Aborting.` | Ubuntu 22.04 ships an older GLib that the repo notes as problematic | Upgrade GLib to a newer version as described in the repository notes |
| RTSP stream reaches EOS and hangs | `rtpjitterbuffer` issue in the GStreamer stack | Apply the repo's `update_rtpmanager.sh` guidance on a DeepStream host |
| Calibration build does not enable `OPENCV=1` | OpenCV dev headers are missing | Install `libopencv-dev` and rebuild the custom library with `OPENCV=1` |

## Configuration mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Wrong class count or label order | `num-detected-classes` or `labels.txt` does not match the exported model | Rebuild labels from the exporter and set the config template that matches the family |
| Boxes look offset or squashed | Wrong `maintain-aspect-ratio` / `symmetric-padding` / `model-color-format` values | Compare the chosen config against the model-family matrix and use the family-specific knobs |
| Engine file is not reused | `model-engine-file` points at the wrong path or the cached engine was created for a different batch size / precision | Delete the stale engine or move it to the correct folder and rebuild with the intended settings |
| Multiple GIEs collide | `gie-unique-id`, `YOLOLAYER_PLUGIN_VERSION`, or `operate-on-gie-id` is duplicated or mismatched | Increment the plugin version and rewire the primary/secondary IDs consistently |

## Exporter issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import error in an exporter script | The upstream framework stack for that family is missing | Install the documented upstream repo and dependencies, or use the reference-only matrix entry instead |
| `labels.txt` is missing after export | The exporter was not run from the expected upstream repo or the weights file has no class metadata | Re-run the exporter helper and confirm the output directory |

## Notes

- The deployment sub-skill should handle single-model runtime issues.
- The multi-GIE sub-skill owns the duplicated-folder and secondary-GIE errors.
- The calibration sub-skill owns INT8 and OpenCV-specific build failures.
- When the host lacks the DeepStream SDK, prefer documenting the missing prerequisite instead of inventing a runtime result.

# INT8 troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Calibration build fails when `OPENCV=1` is set | OpenCV dev headers are missing | Install `libopencv-dev` and rebuild the custom library with `OPENCV=1` |
| `calib.table` is not written | `int8-calib-file` was not enabled or the calibration image list was wrong | Check `INT8_CALIB_IMG_PATH`, `INT8_CALIB_BATCH_SIZE`, and the infer config edits |
| Calibration images are ignored | `calibration.txt` contains stale or relative paths | Rebuild the list with absolute image paths using the helper script |
| Accuracy drops after INT8 conversion | The family-specific resize or normalization knobs were not preserved | Compare the infer config to the family matrix and benchmark notes |
| Benchmark numbers are not comparable | The model family uses different NMS / cluster settings | Use the benchmark notes and the correct family template instead of comparing unrelated templates directly |

## Notes

- If the host cannot build the OpenCV-backed calibration path, stop and document the missing prerequisite.
- If the host cannot run DeepStream, the calibration run remains a documented workflow rather than a verified one.

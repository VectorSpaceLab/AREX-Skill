# Native C++ Troubleshooting

## `--tracker-backend cpp` fails to build

Check the toolchain first:

- C++17 compiler
- CMake 3.16+
- OpenCV 4.x
- Eigen3 3.3+

If any of those are missing, install them before retrying `boxmot build` or the first `cpp` backend run.

## Tracker not supported natively

Only the supported native trackers can use the C++ backend. If the user asks for a tracker outside the native set, use the Python backend instead.

## Native backend silently falls back

For some ReID paths, BoxMOT may fall back to the Python implementation if the native C ABI is unavailable. Treat that as a backend issue, not as a tracker bug.

## OBB / AABB switching

Native trackers should not switch between AABB and OBB inputs mid-run. If the detection layout changes, recreate the tracker or reset the sequence-local state.

## Native ReID issues

- `botsort` and `occluboost` can export `.pt` weights to ONNX for native use.
- If the user expects native ReID but sees Python timing, check the backend mode and native runtime availability.
- Environment knobs such as `BOXMOT_REID_BACKEND` and `BOXMOT_REID_DEVICE` affect native ReID behavior.

## Good recovery path

If the user only needs a yes/no backend availability check, run the bundled probe script first instead of immediately building every tracker.

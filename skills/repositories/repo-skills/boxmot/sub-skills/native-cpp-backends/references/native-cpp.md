# Native C++ Backends

## What BoxMOT exposes

BoxMOT ships native C++ tracker implementations for:

- `botsort`
- `bytetrack`
- `ocsort`
- `occluboost`
- `sfsort`

Supported backends cover both live tracking and cached benchmark replay for the trackers listed above.

## Backend selection

Use the tracker backend, not the replay executor, to choose the implementation:

```bash
boxmot track --tracker bytetrack --tracker-backend cpp --source video.mp4
boxmot eval --benchmark mot17 --split ablation --tracker botsort --tracker-backend cpp
```

`--tracking-backend cpp` remains as a compatibility alias for existing replay scripts.

## Build entry point

Use the CLI build command to compile the native libraries:

```bash
boxmot build
boxmot build --tracker bytetrack --tracker ocsort
boxmot build --force
```

The compiled libraries land under `build/native/<tracker>/`.

## Native live tracking

The Python wrappers still own source iteration, detector execution, and result rendering. The native backend only swaps the tracker implementation.

## Native replay

For `eval`, `tune`, and `research`, BoxMOT can run the replay stage through the C++ executable for the supported tracker.

## ReID behavior

- `botsort` and `occluboost` use native C++ ReID when configured for `cpp` backend runs.
- A `.pt` ReID checkpoint can be auto-exported to ONNX for native use.
- Native cached embeddings are stored in a `__cpp` cache bucket so they do not collide with Python-backend embeddings.

## C++ embedding

You can link the tracker core directly in your own C++ project:

```cmake
add_subdirectory("${BOXMOT_ROOT}/boxmot/native/cpp/trackers/bytetrack" "${CMAKE_BINARY_DIR}/boxmot_bytetrack")
target_link_libraries(my_app PRIVATE bytetrack_core)
```

Detection contract:

- AABB: `xyxy`, `conf`, `cls`, `det_ind`
- OBB: `is_obb = true`, `xywha`, `conf`, `cls`, `det_ind`

## Requirements

- C++17 compiler
- CMake 3.16+
- OpenCV 4.x
- Eigen3 3.3+

Use this page when the user is choosing a backend or linking the tracker into another C++ program.

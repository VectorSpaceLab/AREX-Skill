---
name: native-cpp-backends
description: "Use BoxMOT for native C++ tracker builds, backend selection, and
  C++ embedding workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Native C++ Backends

Use this sub-skill when the task is about `boxmot build`, `--tracker-backend cpp`, supported native tracker coverage, or embedding BoxMOT trackers from C++.

## Covers

- `boxmot build`
- `--tracker-backend cpp` and the compatibility alias `--tracking-backend cpp`
- native live tracking
- native benchmark replay
- C++ embedding of the tracker libraries
- native ReID handling for supported trackers
- build-toolchain and backend-selection debugging

## Does not cover

- Python tracker algorithm details
- ReID training/export workflows unless they affect native backend inputs
- benchmark metric interpretation beyond backend choice

## Read first

- [Native C++ backend guide](references/native-cpp.md)
- [Troubleshooting](references/troubleshooting.md)
- [Backend probe script](scripts/native_backend_probe.py)

## Good prompts for this route

- "How do I build the native trackers?"
- "Which trackers support `--tracker-backend cpp`?"
- "Why does my C++ backend fall back to Python?"
- "How do I link ByteTrack into my own C++ program?"
- "Does OBB work in the native replay path?"

## Typical workflow

1. Identify whether the user wants live tracking, benchmark replay, or standalone C++ embedding.
2. Check whether the tracker is in the supported native set.
3. Verify the build toolchain before suggesting a backend switch.
4. Decide whether the native ReID path is needed or whether the tracker is motion-only.
5. If the user only needs backend availability, run the bundled probe script instead of suggesting a build.

## Entry points

```bash
boxmot build
boxmot track --tracker bytetrack --tracker-backend cpp --source 0
boxmot eval --benchmark mot17 --split ablation --tracker botsort --tracker-backend cpp
```

For C++ embedding, use the tracker-specific library targets and the public detection contract described in the reference page.

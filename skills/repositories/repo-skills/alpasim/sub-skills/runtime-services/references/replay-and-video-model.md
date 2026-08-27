# Replay and video-model renderer

Read this for deterministic runtime regression checks or a stateful renderer
that returns frames in chunks.

## ASL replay boundary

An ASL file records size-delimited protobuf log entries for a rollout. The
replay reader loads entries, pairs requests with responses by service/method,
and exposes exchange summaries. It ignores known dynamic fields such as
session UUIDs and random seeds and compares floating-point values with small
absolute/relative tolerance. Rendered image bytes are correlated with logged
driver camera observations rather than assuming that a stateless render RPC
returned image bytes.

Replay services validate incoming requests against recorded exchanges and abort
with `INVALID_ARGUMENT` plus a diff when no matching request is found. Session
open/close state is tracked and a close for an unknown session is a `NOT_FOUND`
error. The recorded metadata supplies the replay service version identity and
available scene.

This facility is intended for refactoring/integration checks, principally with
one instance of each service. It does not model arbitrary concurrent clients,
new scenes, or a production service fleet. A mismatch should be investigated in
this order:

1. Confirm the same scene and resolved runtime settings.
2. Check whether a dynamic UUID/seed difference is expected or a structural
   request field changed.
3. Read the first unconsumed exchange and its generated diff.
4. Check timestamp/camera grouping and whether a multi-pose egomotion request
   was split correctly.
5. Compare service versions and only then loosen a fixture deliberately.

Use the evaluation route for reading, converting, or scoring ASL files; this
route owns replaying service behavior and request chronology.

## Video-model session lifecycle

Unlike sensorsim's frame-oriented renderer, the video-model client maintains a
remote session:

1. Read static HD-map parquet bytes and recorded first-frame JPEGs from the
   artifact-backed scene.
2. Parse recorded camera intrinsics/extrinsics, preserving FTheta polynomial
   direction and linear CDE terms.
3. Open a world-model session with map, camera specs, rig-to-camera poses,
   seed frames, and text prompts.
4. For each chunk, sample ego trajectory timestamps and dynamic actors, then
   request a block of frames.
5. Put returned RGB frames, and optional HD-map debug frames, into the runtime
   event timeline.
6. Close the session during rollout teardown.

The runtime's first chunk uses `first_chunk_frames`; subsequent requests use
`chunk_frames`. Frame timestamps come from the requested trajectory, not from an
unverified response trajectory. A response with more frames than requested is
an error because every frame needs a request timestamp.

`VideoModelConfig` guards positive `fps` and chunk lengths, restricts forwarding
mode to `all`/`subsample`, and requires `return_hdmap_frames` when forwarding
HD-map frames to the driver. The gRPC channel allows large chunk messages, but
message size is not a substitute for server capacity or GPU memory.

## Calibration and data alignment

The expected calibration is inside the scene artifact. Camera IDs are logical
names such as `camera_front_wide_120fov`; only cameras present in the recorded
calibration can be selected. The runtime may apply a resolution override, but
camera pose/intrinsics overrides invalidate the seed-frame/HD-map alignment and
are rejected for the video-model bootstrap.

A missing artifact, missing calibration parquet, missing frame directory, or
missing HD-map payload is a data failure. A malformed polynomial or unsupported
camera model is a calibration failure. A remote session-start timeout is a
renderer readiness/model/cache failure. Keep those categories distinct.

## Backend boundary

Mocked video-model tests can validate chunk size, timestamp propagation,
configuration guards, and event scheduling on CPU. Full integration needs a
compatible server/container, CUDA, model checkpoints, sufficient VRAM, valid
scene assets, and sometimes authenticated asset access. A successful import or
mock test must not be reported as full video-model recovery.

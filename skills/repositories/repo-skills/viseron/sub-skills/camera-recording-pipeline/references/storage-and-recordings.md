# Storage, NVR, Recordings, Snapshots, and Timelapse

Use this reference to design Viseron recorder/NVR behavior and retention rules. It deliberately separates recorder video, snapshots, and timelapse because they are different storage categories with independent cleanup behavior.

## NVR is the camera coordinator

Add an `nvr` entry for every camera identifier that should be active:

```yaml
ffmpeg:
  camera:
    front_door:
      host: camera-lan
      port: 554
      path: /Streaming/Channels/101/

nvr:
  front_door:
```

The NVR requires the camera domain and treats detector/post-processor domains as optional dependencies. It starts/stops the camera, listens for frame bytes, decides which scanners should receive frames, starts/stops the recorder for event/manual recordings, and publishes processed-frame/operation-state information.

Detector details are owned elsewhere, but their recorder impact is:

- No object or motion detector: the NVR can still start the camera; there are no detector frame scanners and no detector-triggered event recording.
- Object detector only: object scanning is enabled when configured, and objects with recording-trigger flags can start event recordings.
- Motion detector only: scanner-style motion can trigger recording when its motion detector config enables recording; event-driven motion detectors do not create frame scanners.
- Object plus motion: `scan_on_motion_only` pauses object scanning until motion; motion can keep a recording alive when detector filters require motion overlap or motion keepalive.
- Scanner FPS above camera output FPS is clamped to the camera output FPS and logged as a warning.

## Recorder options that affect retention and timing

Each camera has a `recorder` section inherited by FFmpeg and GStreamer camera configs.

| Option | Default | Effect |
|---|---:|---|
| `lookback` | `5` | Seconds to include before an event; segment cleanup respects this buffer. |
| `idle_timeout` | `10` | Seconds to keep recording after an event appears over. |
| `max_recording_time` | `300` | Hard maximum event/manual recording length. |
| `continuous_recording` | `true` | Enables 24/7 recording only when continuous retention is configured globally or per camera. |
| `create_event_clip` | `false` | Creates an MP4 event clip in addition to fragmented recording files. This consumes extra storage. |
| `thumbnail.save_to_disk` | `true` | Saves the latest recording thumbnail under the recorder thumbnail category. |
| `schedule.events` | unrestricted | Restricts event recordings by cron windows. |
| `schedule.continuous` | unrestricted | Restricts continuous retention windows; inactive continuous segments age out after lookback. |
| `schedule.timezone` | server timezone | IANA timezone for cron expressions. |

Manual recordings can be started through Viseron control surfaces and are not blocked by the event/continuous schedule. They stop when explicitly stopped or when their duration/max-recording-time limit is reached.

## Recording file model

Viseron stores short fragmented MP4 (`.m4s`) segments and serves recordings through generated HLS playlists in the web interface. Segments are not meant to be played as standalone media files. Download actions can concatenate a selected event or timespan into an `.mp4` file.

Event recordings, continuous recordings, and manual recordings share recorder segment storage. Manual recordings follow event retention rules. If `create_event_clip: true`, Viseron stores an additional MP4 event clip under the event-clips subcategory; retain enough space for both the fragments and the clip.

## Storage categories and subcategories

The storage component manages tiers for these categories:

| Category | Subcategories | Typical files |
|---|---|---|
| `recorder` | `segments`, `event_clips`, `thumbnails` | Fragmented video segments, optional MP4 event clips, recording thumbnails. |
| `snapshots` | `face_recognition`, `object_detector`, `license_plate_recognition`, `motion_detector` | JPEG snapshots from events or post-processors. |
| `timelapse` | `timelapse` | JPEG frames extracted from video fragments for timelapse use. |

With `path: /`, Viseron expects the conventional container paths for the category (`/segments`, `/event_clips`, `/thumbnails`, `/snapshots`, `/timelapse`). With a custom path, Viseron creates category/subcategory/camera subdirectories below that base path.

## Tier semantics

A tier is an ordered storage location. Viseron writes new files to the first tier, then moves or deletes files when `max_age` or `max_size` is reached.

Rules and cautions:

- The first tier must be a local disk or RAM disk. Do not make the first tier a network share or NTFS mount; Viseron may not detect files or gather metadata reliably. Later tiers can use slower/network storage, with `poll: true` when filesystem events are unreliable.
- `max_age` is calculated from the file creation time, not from when the file arrived in the current tier. Tier ages are not additive: a 1-day first tier and a 7-day second tier delete after 7 total days, not 8.
- `min_age` protects young files from size-based cleanup; `min_size` can keep a minimum amount of data even when age cleanup would otherwise move/delete it.
- Size retention is calculated per camera. Two cameras with `max_size: 10 GB` can use about 20 GB total for that rule.
- The same tier path cannot appear twice within one tier list, and later `max_age` values must be greater than previous `max_age` values for the same storage type.
- If the first recorder tier does not enable `events`, later tiers cannot enable event retention. The same applies to `continuous`.
- `move_on_shutdown: true` is important for RAM-disk first tiers so files are moved or deleted to the next tier on shutdown rather than lost.
- `drain: true` moves all files when a limit is reached, reducing repeated small writes, but event recordings can still require partial moves.
- Paths `/tmp` and Viseron's own temp directory are reserved tier paths.

## Global retention example

This keeps event/manual recordings for 14 days, keeps continuous recordings by size, and retains snapshots separately.

```yaml
storage:
  recorder:
    tiers:
      - path: /
        events:
          max_age:
            days: 14
        continuous:
          max_size:
            gb: 10
  snapshots:
    tiers:
      - path: /
        max_age:
          days: 7
```

## Per-camera recorder overrides

Per-camera `recorder.events` or `recorder.continuous` creates a one-tier recorder override for that camera. Per-camera `storage.recorder.tiers` replaces the global recorder tier list for that camera.

```yaml
ffmpeg:
  camera:
    front_door:
      host: camera-lan
      port: 554
      path: /Streaming/Channels/101/
      recorder:
        events:
          max_age:
            days: 30
        continuous:
          max_size:
            gb: 20
```

Use the full `storage.recorder.tiers` override when a camera needs more than one tier.

## Difficult case: keep event clips longer than continuous segments

Goal: retain event/manual recordings and optional event clips longer than continuous background segments, without deleting snapshots.

```yaml
storage:
  recorder:
    tiers:
      - path: /fast-local
        move_on_shutdown: true
        continuous:
          max_age:
            hours: 6
        events:
          max_age:
            days: 3
      - path: /archive-events
        events:
          max_age:
            days: 30
  snapshots:
    tiers:
      - path: /snapshots-local
        max_age:
          days: 14
    object_detector:
      tiers:
        - path: /snapshots-local
          max_age:
            days: 14
        - path: /snapshots-archive
          max_age:
            days: 45
```

Why this works:

- The first recorder tier enables both `continuous` and `events`, so event files can move to a later event tier while continuous-only files have no later continuous tier and are deleted after the first-tier continuous rule.
- Event clips and thumbnails are moved in step with event recordings. If `create_event_clip` is enabled, plan for duplicate storage in `event_clips`.
- Snapshots have their own `snapshots` category. They are not protected by `recorder.events`, so the snapshot tier must be configured explicitly.
- The second event `max_age` is greater than the first event `max_age`, satisfying tier validation.

## Snapshots

Snapshots are JPEGs from motion/object detection and post-processing domains. Snapshot creation conditions are configured under the detector/post-processor components, but snapshot retention belongs here.

- Default global snapshot retention is 7 days when using default storage settings.
- Override per snapshot domain under `storage.snapshots.<domain>.tiers`.
- Override per camera under the camera's `storage.snapshots` section when only one camera needs different snapshot retention.
- Stationary objects can create many snapshots; use detector `store_interval`/post-processor settings plus snapshot retention to control growth.

## Timelapse

Timelapse retention is optional. When configured, Viseron extracts frames from video fragments into the `timelapse` storage category. The extraction path uses FFmpeg internally and depends on available segment files; treat it as target-host behavior unless verified.

```yaml
storage:
  timelapse:
    tiers:
      - path: /timelapse-fast
        interval:
          minutes: 5
        max_age:
          days: 7
      - path: /timelapse-archive
        max_age:
          days: 30
```

If no timelapse tiers are configured, camera objects have no timelapse folder and no timelapse frames are extracted.

## Cleanup and database cautions

- Let Viseron run storage cleanup through tier rules, cleanup jobs, and web/API deletion flows. Avoid manually deleting files while Viseron is running unless you also understand the database rows that point to them.
- Database migrations run on startup when needed. Do not interrupt Viseron while it logs that a database upgrade is in progress.
- An external PostgreSQL database is selected by the target host's `POSTGRES_DATABASE_URL`. Treat DB connectivity and credentials as deployment requirements, not skill-verified behavior.
- The repository contains a database recreate helper that drops all tables and recreates the schema. It was intentionally not bundled because it is destructive and can erase recordings/events. Do not use database recreation as a retention cleanup tool.

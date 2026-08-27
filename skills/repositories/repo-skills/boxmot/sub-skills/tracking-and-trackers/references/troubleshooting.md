# Tracking Troubleshooting

## "Detections must have 7 columns" or similar

That means the tracker received the wrong geometry layout.

- AABB input must be `(x1, y1, x2, y2, conf, cls)`
- OBB input must be `(cx, cy, w, h, angle, conf, cls)`

If the detector emits the wrong layout, fix the detector or convert the tensor before calling the tracker.

## OBB input rejected by a tracker

Not every tracker supports OBB in every branch. Check the tracker's `supports_obb` flag and make sure you are using an OBB-capable tracker such as ByteTrack, BotSort, OcSort, OccluBoost, or SFSORT.

## Output column confusion

Remember the output layout changes with geometry:

- AABB output has 8 columns
- OBB output has 9 columns

If downstream code reads the wrong column index, use the named `TrackResults` accessors instead of raw positional indices.

## No track output

If the tracker returns empty outputs, check:

- confidence thresholds (`conf`, `track_thresh`, `det_thresh`, or `min_conf` depending on the tracker)
- class filtering / `per_class`
- whether the tracker was given `embeddings` when it requires appearance features
- whether the sequence has any detections after NMS

## Tracker state switching during a sequence

Do not switch a single tracker instance between AABB and OBB inputs mid-run. The tracker should be recreated or reset when the geometry changes.

## Native `--tracker-backend cpp` surprise failures

If the user only wants Python tracking, keep the backend at the default `python`. If they explicitly want C++ and the build fails, send them to the native backend sub-skill rather than debugging the shape path here.

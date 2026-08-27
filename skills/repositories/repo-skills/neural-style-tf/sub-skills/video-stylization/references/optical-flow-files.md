# Optical-flow Files

## When to read

Read this before using `--init_frame_type prev_warped`, adapting an optical-flow pipeline, or diagnosing missing `.flo` and `reliable_*.txt` files.

## Expected files

For adjacent frames `i` and `j = i + 1`, the source-compatible pipeline expects these files in `--video_input_dir`:

| File | Direction | Used by |
| --- | --- | --- |
| `forward_{i}_{j}.flo` | previous/current pair, previous to current | consistency checking and diagnostics |
| `backward_{j}_{i}.flo` | current to previous | `get_prev_warped_frame(frame)` for warping previous stylized output |
| `reliable_{i}_{j}.txt` | previous to current reliability | source reads alongside backward reliability but returns the forward one in inspected code |
| `reliable_{j}_{i}.txt` | current to previous reliability | consistency evidence for temporal loss generation |

The default `neural_style.py` format strings are:

```text
--backward_optical_flow_frmt backward_{}_{}.flo
--forward_optical_flow_frmt forward_{}_{}.flo
--content_weights_frmt reliable_{}_{}.txt
```

The source calls these templates with unpadded frame integers for flow/reliability files, while content frames are zero-padded before `--content_frame_frmt` is formatted.

## `.flo` reader expectations

The source `read_flow_file(...)` reads:

1. 4-byte header;
2. 32-bit integer width;
3. 32-bit integer height;
4. width × height pairs of 32-bit floats for x/y flow.

It does not validate the magic header or file length. A corrupt or mismatched `.flo` can therefore fail later with shape, remap, or read errors. Prefer validating file dimensions before a long render.

## Reliability text expectations

The source `read_weights_file(...)` expects a text file:

1. first line: width and height separated by a space;
2. following lines: numeric values for each row;
3. values below 255 become 0, and values at least 255 become 1;
4. the resulting 2D mask is stacked to 3 channels.

If dimensions do not match the current frame, temporal loss may fail or produce invalid weighting.

## Choosing an initialization mode

- `prev_warped`: best temporal continuity, but requires previous output frame plus backward flow and reliability files.
- `prev`: initializes from the previous stylized frame without warping; avoids flow files but can smear motion.
- `content`: initializes each frame from its content frame; lower temporal consistency but simpler.
- `random` or `style`: useful for experiments but usually flickers across frames.

If the user has no flow pipeline, route to `content` or `prev` rather than pretending `prev_warped` can work without `.flo` and reliability files.

## Binary and platform notes

The inspected repository includes Linux static optical-flow executables and a consistency checker. Generated skill files do not copy those platform-specific binaries. Treat them as evidence for the expected file formats and pipeline order, not as portable bundled runtime assets. On a new machine, use a compatible optical-flow generator that can produce the expected `.flo` and reliability files, or use a non-warped initialization mode.

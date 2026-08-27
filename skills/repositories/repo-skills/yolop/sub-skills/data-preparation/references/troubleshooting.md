# Data Preparation Troubleshooting

## Empty or zero-length dataset

Likely causes:

- `MASKROOT/<split>` has no `.png` files. `BddDataset` uses the drivable mask list as the database anchor.
- The wrong split name is configured (`TRAIN_SET`, `TEST_SET`).
- Data roots point at a parent directory one level too high or too low.

Recovery:

1. Run `scripts/check_data_layout.py` with the same roots and splits.
2. Confirm `MASKROOT/train` and `MASKROOT/val` contain PNG files.
3. Confirm matching images/labels/lanes exist for the sampled mask stems.

## `FileNotFoundError` or `Path.iterdir()` failure

Likely causes:

- One of `DATAROOT`, `LABELROOT`, `MASKROOT`, or `LANEROOT` does not exist.
- The config points to a leaf split directory while source expects a root containing the split directory.

Recovery:

- If the images are in `/data/bdd100k/images/100k/train`, set `DATAROOT` to `/data/bdd100k/images/100k`, not to the `train` directory.
- Repeat for labels, drivable masks, and lane masks.

## Detection JSON parses but no boxes appear

Likely causes:

- `single_cls = True` in `lib/dataset/bdd.py`, so only `car`, `bus`, `truck`, and `train` are retained.
- JSON objects lack `box2d`.
- The BDD schema differs from the expected `frames[0].objects` shape.

Recovery:

- Inspect one JSON and verify the schema fields named in `data-layout.md`.
- Decide deliberately before changing `single_cls`; changing it changes model class semantics and detection head expectations.

## Generated drivable masks are blank

Likely causes:

- The BDD JSONs do not contain categories starting with `area`.
- Polygons use unexpected `poly2d` point/codes.
- The helper was run with an incorrect image width/height.

Recovery:

- Check that at least one JSON contains an object category such as `area/drivable`.
- Run the generator on a single known JSON with `--limit 1` and inspect the output PNG.
- If the raw annotation coordinate frame is not 1280x720, pass `--image-width` and `--image-height`.

## Matplotlib backend or display errors

The mask generator should use a non-interactive backend, but headless environments can still expose display-related issues if another script imports pyplot first.

Recovery:

- Run the bundled generator as a standalone process.
- Set `MPLBACKEND=Agg` for mask generation.
- Avoid running GUI demo inference in the same headless process.

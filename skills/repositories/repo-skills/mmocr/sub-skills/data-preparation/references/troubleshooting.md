# MMOCR Data Preparation Troubleshooting

## Unsupported dataset or task

Symptoms:

- preflight reports dataset not found;
- a dataset has `textdet.py` but no `kie.py`;
- metadata lists different tasks from the task config files.

Actions:

1. Run `python scripts/mmocr_dataset_preflight.py --list` to see known official
   support.
2. If using a private dataset-zoo, pass `--dataset-zoo-path <dataset_zoo>` and
   check that `<dataset>/<task>.py` exists.
3. If `metafile.yml` exists, ensure `Data.Tasks` includes the requested task;
   the unified preparer rejects a task missing from metadata.
4. If the task is unavailable, choose a different supported task or create a
   private task config with matching obtainer/gatherer/parser/packer/dumper and
   config generator.

## Accidental network download or large write

Symptoms:

- conversion starts downloading archives;
- cache files are missing or MD5 checks fail;
- disk usage grows under cache/data directories;
- a conversion prompts about re-extracting an existing archive.

Actions:

1. Stop before conversion if the user has not approved network, storage, and
   license terms.
2. Use the preflight helper for read-only checks; it does not import MMOCR or
   download anything.
3. For official preparer semantics, remember that the obtainer downloads when a
   cache file is absent or fails integrity checks, extracts archives into
   `data_root`, moves mapped files, and deletes temporary folders listed in
   `delete`.
4. For restricted networks, stage required archives in the expected cache names
   first, then rerun only after confirming checksums and storage budget.

## Wrong split selection

Symptoms:

- requested `val` produces nothing;
- a split-specific annotation file is missing;
- a training handoff references `*_val` variables that were never generated.

Actions:

1. Valid split names are only `train`, `test`, and `val`.
2. Check whether the dataset-zoo task config defines `train_preparer`,
   `test_preparer`, and/or `val_preparer`. Missing split preparers are skipped.
3. Prepare only the splits the dataset actually supports.
4. If a validation split must be derived from training data, document the split
   policy before conversion; do not invent a `val` annotation filename after the
   fact.

## Generated config was not overwritten

Symptoms:

- annotations were regenerated but base dataset config still points to old
  files;
- console says a config was found and skipped;
- a local config edit disappeared after conversion.

Actions:

1. By default, config generation does not overwrite an existing base dataset
   config.
2. Use the overwrite option only with explicit approval, because it can replace
   local dataset edits.
3. If preserving edits, write a new dataset name or `dataset_postfix` rather
   than overwriting.
4. After conversion, record the generated variable names and route any model
   config changes to the training/evaluation sub-skill.

## LMDB mismatch in recognition data

Symptoms:

- `--lmdb` is used with detection, spotting, or KIE;
- `RecogLMDBDataset` cannot find `num-samples`;
- `LoadImageFromFile` fails on LMDB data;
- a JSON dataset config points to `.lmdb` or an LMDB config points to `.json`.

Actions:

1. LMDB is supported only for `textrecog`.
2. Verify LMDB directories contain `num-samples`, `image-000000001`, and
   `label-000000001` style keys.
3. Use `RecogLMDBDataset` with `ann_file='textrecog_<split>.lmdb'`.
4. Replace the first recognition loader with `LoadImageFromNDArray`, because
   the dataset returns image arrays from LMDB.
5. Keep JSON recognition configs on `OCRDataset`/`LoadImageFromFile`; do not
   mix storage formats.

## Missing images, `ann_file`, `data_root`, or `data_prefix`

Symptoms:

- dataset length is zero;
- images cannot be loaded;
- annotation JSON exists but all relative image paths are wrong;
- training fails before the first batch.

Actions:

1. Confirm `data_root/ann_file` exists.
2. Inspect a few `data_list[].img_path` values and resolve them relative to
   `data_root` plus any configured image prefix.
3. For generated JSON, paths are normally relative to `data_root`; avoid adding
   an extra prefix unless the config was designed for it.
4. For `PairGatherer`, check that image suffixes and regex replacement rules
   map image names to annotation names exactly.
5. For `MonoGatherer`, check that the one annotation filename lives under the
   configured annotation directory and that image names inside it match the
   image directory.

## Polygon, bbox, and text encoding issues

Symptoms:

- polygons are malformed or masks are empty;
- bboxes have reversed coordinates;
- ignored instances are trained as positives;
- non-ASCII text becomes mojibake;
- labels containing commas or spaces are truncated.

Actions:

1. Validate polygons as flat even-length coordinate lists with at least eight
   numbers.
2. Validate bboxes as `[x1, y1, x2, y2]` with `x2 >= x1` and `y2 >= y1`.
3. Keep ignore markers consistent with the parser (`###`, `#`, or label-based
   ignore depending on dataset).
4. Use an encoding that matches the raw annotation, often UTF-8 with BOM support
   for ICDAR-style text files.
5. Configure separators and formats so transcript fields may contain commas or
   spaces without being split incorrectly.
6. For detection datasets whose annotations were made on raw image pixels, use
   an image loader that ignores EXIF orientation in downstream pipelines.

## KIE label and class problems

Symptoms:

- class IDs do not match names;
- key/value edges are missing or inconsistent;
- WildReceipt assumptions are applied to a different receipt schema;
- KIE training sees only background/others labels.

Actions:

1. Confirm every annotation token has an 8-number `box`, a `text` string, and a
   numeric `label`.
2. Keep a class list or metainfo mapping beside the annotations and verify ID
   parity with the model config.
3. For WildReceipt-style closed set, label IDs pair key and value classes; open
   set conversion maps nodes into background/key/value/others and assigns edge
   groups.
4. For private KIE, write an explicit label and edge mapping. Do not rely on the
   built-in receipt class numbers unless names and semantics are identical.
5. If OCR boxes/text are available but semantic labels are absent, route the
   data as textspotting or detection+recognition instead of KIE.

## Headless dataset visualization

Symptoms:

- visualization hangs waiting for a window;
- no display server is available;
- output images are huge or pipeline mode is slow;
- task inference fails for a dataset-only config.

Actions:

1. Prefer JSON/path preflight before visualization.
2. In headless mode, use no-display/output-only options and write images to an
   approved output directory.
3. Limit sample count during checks.
4. Specify the task manually when automatic task inference cannot distinguish
   detection from recognition.
5. Use original-mode visualization for annotation geometry first; transformed
   or pipeline views debug preprocessing after the raw labels are trusted.

---
name: data-preparation
description: "Prepare, validate, and troubleshoot rPPG-Toolbox raw datasets,
  face-cropped NPY caches, labels, file lists, splits, and dataset-loader
  integrations."
disable-model-invocation: true
metadata: { disco-role: operating }
license: NOASSERTION
---

# Data preparation

Use this skill when a Researcher must turn a supported raw dataset into aligned,
face-cropped, resized, normalized, chunked cache clips, or must audit an existing
cache without access to the original checkout. This skill covers dataset discovery,
preprocessing configuration, cache/file-list contracts, and loader extension points.
It does not cover trainer/model internals or metric interpretation. Use the
`evaluation-and-visualization` sub-skill for metrics and the `supervised-models`
sub-skill for trainer configuration.

## Operating contract

- Keep raw data immutable. Treat preprocessing as an explicit, potentially expensive
  build step; use a separate `CACHED_PATH` and `FILE_LIST_PATH`.
- First validate the raw layout and a small representative video/label pair. Then
  choose subject-safe splits, face settings, transforms, chunk length, and output
  locations. Record the effective configuration alongside the run externally.
- For an existing cache, run `scripts/validate_preprocessed_data.py` in read-only
  mode before loading it. A normal NPY cache contains paired `*_input*.npy` and
  `*_label*.npy` files and a CSV whose required column is `input_files`.
- Do not assume a CSV path is portable: generated file lists contain the paths used
  at preprocessing time. Relocate/rewrite them deliberately, then revalidate.
- `DO_PREPROCESS: true` reads raw data and writes cache files; after a successful
  build, set it to false for training/evaluation. With preprocessing disabled,
  missing `CACHED_PATH` is an error; a missing file list may trigger retroactive
  reconstruction from raw identifiers and cached input names.

## Standard preprocessing plan

1. **Select the source and loader.** Match the layout in
   [references/data-formats.md](references/data-formats.md), verify frame and label
   sampling, and identify whether the split is by subjects or by files.
2. **Set paths and split.** Configure `DATA_PATH`, `CACHED_PATH`, `FILE_LIST_PATH`,
   `BEGIN`, `END`, and `DATA_FORMAT`. Use `BEGIN=0, END=1` for all data. For
   subject-aware loaders, fractional boundaries select whole sorted subjects, not
   arbitrary clips. Avoid leakage by keeping a subject in one split.
3. **Choose preprocessing.** Use `DATA_TYPE` values `Raw`, `DiffNormalized`, and/or
   `Standardized`; choose one `LABEL_TYPE` from `Raw`, `DiffNormalized`, or
   `Standardized`. `DO_CHUNK` with `CHUNK_LENGTH` keeps only complete chunks; the
   remainder is discarded. `DO_CHUNK: false` emits one variable-length clip.
4. **Crop and resize.** Configure `CROP_FACE.DO_CROP_FACE`, `BACKEND` (`HC` or
   `Y5F`), `USE_LARGE_FACE_BOX`, `LARGE_BOX_COEF`, and detection settings. Set
   `RESIZE.W/H`. Confirm the detector on representative frames before a full build.
5. **Align labels and build.** Dataset loaders resample BVP to frame length where
   needed, then `BaseLoader.preprocess` crops/resizes, transforms, normalizes labels,
   chunks, and saves. Check paired names, finite values, frame/label lengths, and
   file-list coverage before using the cache.

## Cache and loader contract

Standard `BaseLoader.save`/`save_multi_process` names outputs
`<source-id>_input<k>.npy` and `<source-id>_label<k>.npy`. An input NPY is normally
rank 4 `(D,H,W,C)` on disk: temporal depth, height, width, channels (NDHWC).
The matching label is normally rank 1 `(D,)`; `D` must equal the input temporal
length. `BaseLoader.__getitem__` casts both to float32. For `DATA_FORMAT=NDCHW`
it returns `(D,C,H,W)`; for `NCDHW`, `(C,D,H,W)`; for `NDHWC`, it leaves the
stored array unchanged. Do not confuse the on-disk NDHWC contract with the
post-loader tensor layout.

The loader returns `(data, label, filename, chunk_id)`. `filename` is derived from
the cache filename before the final `_inputN` suffix and `chunk_id` is the numeric
chunk suffix. `load_preprocessed_data` reads `input_files`, sorts paths, and derives
labels by replacing `input` with `label`; therefore use unambiguous cache names and
never mix unrelated input/label roots.

`BP4DPlusBigSmallLoader` is a deliberate exception: it writes a pickle input
containing two arrays (big and small streams), with a paired NPY label of shape
`(D,49)`, and supports `NDCHW`, `NCDHW`, and `NDHWC` for each stream. The supplied
validator audits the standard NPY contract, not pickle contents; audit BigSmall
streams with a loader-aware check and confirm fold membership separately.

## Face crop safety

`HC` uses OpenCV Haar Cascade on the first frame by default; `Y5F` uses the bundled
YOLO5Face implementation and checkpoint and can use CPU or one CUDA device. A
missed detection falls back to a full-frame box; multiple HC detections choose the
largest. Dynamic detection samples every `DYNAMIC_DETECTION_FREQUENCY` frames;
`USE_MEDIAN_FACE_BOX` can replace all sampled boxes with their median. Large-box
expansion can help motion videos but may include background and is clipped during
cropping. Resize uses OpenCV area interpolation.

The source implementation currently addresses the HC XML through a relative
repository dataset path, which is unsafe when the process runs outside the
repository root. A portable runtime must resolve the cascade from an
installed/package resource or an explicit user-supplied resource path, verify that
OpenCV loaded it, and pass an absolute resolved path; never ask a downstream agent
to depend on a source checkout or current working directory. Y5F likewise requires
its model YAML/checkpoint resources to be packaged or explicitly staged; no download
or credential step is part of this skill.

## Boundaries and safe operations

Safe operations are read-only layout/cache validation, deterministic CSV inspection,
small dry-run probes, and writes into an explicitly chosen cache directory. Treat
full video decoding, face detection, pseudo-label generation, and multiprocessing
as costly. `BaseLoader.multi_process_manager` can spawn up to eight workers by
default, each decoding and holding arrays; reduce concurrency for memory-limited
systems. Do not overwrite a known-good cache, mutate raw files, run training, fetch
datasets/checkpoints, or infer metrics here. Motion-augmented data must already be
prepared by the external MA-rPPG Video Toolbox; this repository only reads its NPY
frames when `DATA_AUG` contains `Motion`.

For detailed layouts, loader tails, formats, and caveats, read
[references/data-formats.md](references/data-formats.md). For an actionable build
sequence and custom split/fold guidance, read [references/workflows.md](references/workflows.md).
For failures, read [references/troubleshooting.md](references/troubleshooting.md).
Use `python scripts/validate_preprocessed_data.py --help` before auditing a cache.

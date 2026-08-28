# Data formats and preprocessing

## Merged raw dataset

```text
dataset/
  videos/
    video_001.mp4
  videos2caption.json
```

The manifest is a JSON list whose records contain a relative `path` and caption
field `cap`. Paths must resolve under the dataset's video root, captions must be
non-empty strings, and duplicate/missing paths should be rejected before
encoding.

## HF dataset

Use dataset type `hf` with a Hub ID or local dataset directory. The workflow
expects video and caption columns; inspect a sample before selecting a decoder.

## Precomputed records

Training consumes Parquet-like records with fields such as
`vae_latent_bytes`, `text_embedding_bytes`, and for I2V
`clip_feature_bytes`/`first_frame_latent_bytes`, plus serialized shapes, dtypes,
and sample identifiers. These fields are model/workload-dependent: do not add
I2V columns to a T2V-only pipeline without checking its schema.

## Safe command shape

Use the installed package's preprocessing entry point with explicit paths and a
small frame/resolution sample first. Typical options are `--workload-type t2v`
or `i2v`, `--preprocess.dataset-type merged`,
`--preprocess.dataset-path`, `--preprocess.dataset-output-dir`,
`--preprocess.num-frames`, `--preprocess.max-height`,
`--preprocess.max-width`, and `--preprocess.train-fps`. The exact full CLI can
be inspected with `python -m fastvideo.pipelines.preprocess.v1_preprocessing_new --help`.

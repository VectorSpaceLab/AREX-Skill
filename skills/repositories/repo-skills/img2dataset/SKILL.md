---
name: img2dataset
description: "Create, restart, audit, and scale img2dataset runs for turning URL
  tables into image datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# img2dataset

Use this skill when a user wants to turn a URL list or table into an image dataset with `img2dataset`, or needs to debug an existing download run.

## What this skill covers

- The public Python API `img2dataset.download(...)` and the `img2dataset` console command.
- Input table formats and output writer layouts.
- Image resizing, encoding, and bounding-box blurring.
- Distributed execution with multiprocessing, PySpark, and Ray.
- Restarting interrupted runs, hash verification, SSL policy, and X-Robots-Tag handling.
- Dataset-scale recipes and common troubleshooting.

## Start here

1. Confirm the package is installed and reachable:

   ```bash
   python -c "from importlib.metadata import version; from img2dataset import download; print(version('img2dataset')); print(download)"
   ```

2. Install the package in the environment you want to inspect. For a release install, use `python -m pip install img2dataset`; for a local checkout, use `python -m pip install -e .` from the checkout root.

3. Use the sub-skill that matches the user's request:
   - [core-download](sub-skills/core-download/SKILL.md) for CLI/API runs, retries, incremental recovery, hashes, SSL, and X-Robots-Tag policy.
   - [input-output-formats](sub-skills/input-output-formats/SKILL.md) for input schemas, output formats, metadata layouts, captions, hashes, and TFRecord prerequisites.
   - [image-processing](sub-skills/image-processing/SKILL.md) for resize modes, codecs, filters, and bbox blur.
   - [distributed-execution](sub-skills/distributed-execution/SKILL.md) for multiprocessing, PySpark, Ray, W&B, throughput, and cluster troubleshooting.

## Core import and CLI check

When you only need to confirm the package is alive, run one of these from a neutral working directory:

```bash
python -c "from img2dataset import download; print(download)"
img2dataset -- --help
```

If `img2dataset` is not on `PATH`, use the CLI help check described in `core-download`.

## Read before relying on this skill

- [Repository provenance](references/repo-provenance.md) if you need to confirm whether this skill matches the current checkout.
- [Dataset recipes](references/dataset-recipes.md) for common public dataset command patterns and scale notes.
- [Troubleshooting](references/troubleshooting.md) for install/import failures, backend dependencies, filesystem prefixes, and stale-skill checks.
- [Repo routing metadata](references/repo-routing-metadata.json) is consumed by the managed repo-skill router during import.

## Root helper

- [scripts/check_img2dataset_env.py](scripts/check_img2dataset_env.py) checks the installed package, signature, CLI help, and optional backend availability without depending on the original checkout.

## Route map

- Use **core-download** when the request is about starting, restarting, or recovering a run; deciding `incremental`, `overwrite`, or `extend`; or handling hashes, SSL, robots directives, and base metadata.
- Use **input-output-formats** when the request is about `--input_format`, `--output_format`, output layout, metadata schema, or TFRecord and parquet sidecars.
- Use **image-processing** when the request is about `Resizer`, `ResizeMode`, `skip_reencode`, `disable_all_reencoding`, interpolation, image size filters, or bbox blur.
- Use **distributed-execution** when the request is about `--distributor`, PySpark, Ray, W&B, process/thread tuning, `subjob_size`, or throughput bottlenecks.

## Notes for future agents

- Keep runtime guidance inside this skill tree; do not point back to the original repository checkout.
- Treat dataset-scale public recipes as reference material, not as default verification cases.
- If the current checkout has changed, compare it with `references/repo-provenance.md` before reusing the skill.

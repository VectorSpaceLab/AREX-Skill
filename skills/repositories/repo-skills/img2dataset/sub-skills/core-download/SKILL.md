---
name: core-download
description: "Build, validate, and troubleshoot img2dataset CLI/API download
  runs with safe core options, hashes, retries, SSL, robots handling, and
  incremental recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# core-download

Use this sub-skill when a user asks how to start, validate, restart, or debug an `img2dataset` run through the public Python API (`img2dataset.download`) or the `img2dataset` console command.

## Natural triggers

Read this sub-skill for prompts about:

- Building a small or production `download(...)` call or `img2dataset` command.
- Choosing safe core defaults for `thread_count`, `processes_count`, `timeout`, `retries`, `max_shard_retry`, `enable_wandb`, and `incremental_mode`.
- Restarting interrupted runs, reusing an existing output folder, or deciding between `incremental`, `overwrite`, and `extend`.
- Hash computation/verification, hash-mismatch metadata, captions, EXIF metadata, and core status/error validation.
- SSL certificate failures, `X-Robots-Tag` exclusions, `user_agent_token`, and opt-out directive policy.
- Checking that the package import and Fire CLI entry point are usable.

## First checks

1. Verify the public import in the user's active Python environment:

   ```bash
   python - <<'PY'
   import inspect
   import img2dataset
   from img2dataset import download
   print("img2dataset import ok")
   print(inspect.signature(download))
   PY
   ```

2. Verify the CLI help. The command uses Fire; for full function help prefer:

   ```bash
   img2dataset -- --help
   ```

   If the console script is not on `PATH`, try:

   ```bash
   python -m img2dataset.main -- --help
   ```

3. For a no-network smoke path, run the bundled tiny local HTTP demo from this sub-skill directory:

   ```bash
   python scripts/tiny_download_demo.py --dry-run
   python scripts/tiny_download_demo.py --output-folder tiny-output --output-format files
   ```

## Core workflow outline

1. Identify the URL-list input and format. Use the default text format only for one-URL-per-line files; route detailed CSV/TSV/JSON/Parquet schemas to `input-output-formats`.
2. Pick an output format and small safe defaults. For novice runs start with `processes_count=1`, modest `thread_count`, `enable_wandb=False`, `retries=1`, and `max_shard_retry=1`. Route output-format trade-offs to `input-output-formats` and distributed tuning to `distributed-execution`.
3. Decide metadata options: `caption_col` when captions exist, `extract_exif=True` unless EXIF extraction is too costly, `compute_hash` as `sha256` by default, and `verify_hash` only when the input table has trusted raw-image hashes.
4. Decide HTTP policy: keep default `X-Robots-Tag` opt-out directives unless the user has permission to override; use `ignore_ssl_certificate=True` only as a last resort for trusted sources.
5. Run the CLI/API call, then validate root metadata parquet files and `*_stats.json` files for `status`, `error_message`, success counts, failed downloads, failed resizes, and hash-mismatch patterns.
6. For interruptions, rerun the exact same command with the same URL list and `number_sample_per_shard` under `incremental` mode. Use `overwrite` only to delete and rebuild the output, and `extend` only to append new shard ids intentionally.

## References and bundled helper

- [API and CLI reference](references/api-reference.md) covers the verified public signature, CLI option groups, argument interactions, validation rules, metadata fields, and incremental semantics.
- [Quickstart](references/quickstart.md) gives self-contained CLI, Python, tiny-demo, and hash-verified Parquet-to-WebDataset recipes.
- [Troubleshooting](references/troubleshooting.md) maps core symptoms to likely causes and recovery steps.
- [tiny_download_demo.py](scripts/tiny_download_demo.py) creates a local image fixture and runs a tiny download without external network or W&B by default.

## Route to sibling sub-skills

- Use `input-output-formats` for input-format matrices, schema/column mapping, metadata schema details, writer layouts, shard naming details, `save_additional_columns` deep dives, and output-format audits.
- Use `image-processing` for resize modes, encoding quality/format, interpolation, `skip_reencode`, `disable_all_reencoding`, image filters, and bounding-box blur.
- Use `distributed-execution` for PySpark, Ray, multiprocessing performance tuning, W&B performance logging, DNS/filesystem throughput, cluster setup, and `subjob_size` tuning.
- Use the root dataset-recipes reference for dataset-scale public recipes; this sub-skill owns command construction mechanics, not large-dataset acquisition plans.

## Guardrails

- Do not require access to any original checkout, notebook, examples, or test fixture to answer a user. Use only this sub-skill, its references, and its bundled script.
- Do not suggest disabling `X-Robots-Tag` filtering or SSL verification without stating the policy/security trade-off.
- Do not use `overwrite` on an existing output folder unless the user explicitly wants recursive deletion.

# Core download troubleshooting

Use this matrix for install/import, CLI, downloader, hash, SSL, robots, and incremental-recovery failures. Route format-specific layouts to `input-output-formats`, image decode/resize errors to `image-processing`, and throughput/cluster problems to `distributed-execution`.

## Quick diagnosis commands

```bash
python - <<'PY'
import inspect
from img2dataset import download
print("import ok")
print(inspect.signature(download))
PY

img2dataset -- --help
```

Inspect run metadata:

```bash
python - <<'PY'
from pathlib import Path
import json
import pandas as pd

out = Path("images")  # change to the user's output folder
parquets = sorted(out.glob("*.parquet"))
stats = sorted(out.glob("*_stats.json"))
print("metadata parquet count:", len(parquets))
print("stats json count:", len(stats))
if parquets:
    df = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
    print(df["status"].value_counts(dropna=False))
    print(df[df["status"] != "success"][["url", "status", "error_message"]].head(50).to_string(index=False))
if stats:
    for p in stats[:3]:
        s = json.loads(p.read_text())
        print(p.name, {k: s.get(k) for k in ["count", "successes", "failed_to_download", "failed_to_resize", "status_dict"]})
PY
```

## Troubleshooting matrix

| Symptom | Likely cause | Concrete recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'img2dataset'` | Package is not installed in the active Python environment. | Install the package in the environment that will run the command, then rerun the import check. |
| `ModuleNotFoundError: No module named 'fire'` or another runtime dependency | Partial install or missing runtime requirements. | Reinstall the package with dependencies, for example `pip install --upgrade img2dataset`, or repair the environment's dependency installation. Then run `img2dataset -- --help`. |
| `img2dataset: command not found` | Console entry point is not on `PATH` or package was installed into another environment. | Use `python -m img2dataset.main -- --help` to verify the module, activate the correct environment, or reinstall so console scripts are visible. |
| `img2dataset --help` is confusing or does not show all function flags | Fire exposes function help after a separator. | Use `img2dataset -- --help`; then pass `URL_LIST` positionally or with `--url_list=...`. |
| `ValueError: Unsupported hash to compute` | `compute_hash` is not `None`, `md5`, `sha256`, or `sha512`. | Use one of the supported values. Prefer Python API for `compute_hash=None` if CLI literal parsing is uncertain. |
| `ValueError: verify_hash and compute_hash must be the same` | `verify_hash=[column, type]` uses a hash type that does not match `compute_hash`. | Match them exactly, e.g. `--compute_hash=sha256 --verify_hash='["sha256_expected", "sha256"]'`. |
| `ValueError: Invalid hash type ...` from reader setup | The `verify_hash` type is not `md5`, `sha256`, or `sha512`. | Correct the second `verify_hash` element and ensure the first element names the input column containing that hash. |
| Metadata rows have `status=failed_to_download` and `error_message=hash mismatch` | The downloaded raw bytes do not match the trusted input hash. Common causes are wrong hash column, wrong algorithm, stale hashes, or source images changed. | Confirm `verify_hash` points to the expected input column and the second element equals `compute_hash`. Spot-check a URL manually. If the data source legitimately changed, either accept dropping mismatches or rerun without `verify_hash` after a policy decision. |
| `ValueError` says reserved columns cannot be used in `save_additional_columns` | User tried to save a column name reserved by img2dataset metadata. | Rename input metadata columns before calling img2dataset. Do not pass: `key`, `caption`, `url`, `width`, `height`, `original_width`, `original_height`, `status`, `error_message`, `exif`, `md5`, `sha256`, or `sha512`. |
| Many rows show `Use of image disallowed by X-Robots-Tag directive` | Source responses include an opt-out directive such as `noai`, `noimageai`, `noindex`, or `noimageindex`. | Default behavior is to respect these directives. If the source requires crawler identification, set `--user_agent_token=...`. Only when the user has explicit permission to ignore opt-out directives, pass `--disallowed_header_directives='[]'` and document the decision. |
| `user_agent_token` did not bypass X-Robots filtering | The header may be general (`X-Robots-Tag: noai`) rather than scoped to a different user-agent token. General directives apply regardless of token. | Keep the drop, obtain permission/data from another source, or explicitly disable `disallowed_header_directives` only when allowed. |
| HTTPS errors mention `certificate verify failed`, self-signed certificate, or expired certificate | The server's certificate chain cannot be verified by the active environment. | Prefer fixing CA certificates or using a source with a valid certificate. As a last resort for trusted sources, use `--ignore_ssl_certificate=True` / `ignore_ssl_certificate=True`, then inspect metadata for unexpected failures. |
| Downloads remain flaky with timeouts or connection resets | Transient network/server failures, too much concurrency, or too short timeout. | Reduce `thread_count`, increase `timeout`, set modest `retries` such as `1` or `2`, and rerun with `incremental`. Escalate performance diagnosis to `distributed-execution` if throughput is the core problem. |
| Output folder exists and a rerun does nothing for some shards | Default `incremental` skipped shard ids that already have root JSON stats files. | If recovering, this is expected. If you changed the URL list/order/shard size and need a fresh output, choose a new output folder or explicitly use `incremental_mode="overwrite"` after confirming recursive deletion is intended. |
| Interrupted run left partial output and `_tmp` artifacts | Process stopped before cleanup or before every shard wrote stats. | Rerun the exact same command with `incremental_mode="incremental"`, same URL list, same `number_sample_per_shard`, and same output settings. img2dataset will skip completed shards and rebuild shards without completion markers. |
| `extend` created duplicate-looking data | `extend` starts new shard ids after existing root JSON ids; it does not deduplicate rows from the same input. | Use `extend` only for intentional append workflows. For recovery, use `incremental`. For a clean rebuild, use a new output folder or `overwrite` after explicit deletion approval. |
| Root metadata parquet exists but many images are missing | Samples with failed download, failed resize, robots exclusion, or hash mismatch still get metadata rows but may not have image payloads. | Count `status`, inspect `error_message`, and route image decode/resize failures to `image-processing`; route writer-layout expectations to `input-output-formats`. |
| Stats JSON shows failed shards after retries | Some shard-level calls failed even after `max_shard_retry`. | Rerun the same command in `incremental` mode after fixing the underlying issue. Increase `max_shard_retry` modestly only after inspecting error patterns. |

## SSL / X-Robots / retry decision flow

1. Inspect metadata `error_message` and stats `status_dict`; do not guess from missing files alone.
2. If errors are timeouts, resets, DNS, or temporary server failures: lower concurrency or increase `timeout`/`retries`, then rerun with `incremental`.
3. If errors are SSL certificate failures: fix certificates first. Use `ignore_ssl_certificate=True` only for trusted sources and document the security trade-off.
4. If errors are X-Robots exclusions: respect default drops unless there is explicit permission. `user_agent_token` identifies the crawler; it is not a general bypass for source-wide opt-out directives.
5. If policy permits overriding X-Robots filtering, pass an empty directive list: CLI `--disallowed_header_directives='[]'`, Python `disallowed_header_directives=[]`.
6. After any change, rerun the same output folder under `incremental` and re-check status counts.

## Hash verification recovery pattern

Use this pattern when a user reports hash mismatch drops:

1. Confirm the input file format and hash column name.
2. Confirm the expected hash algorithm: `md5`, `sha256`, or `sha512`.
3. Ensure `compute_hash` and `verify_hash[1]` are identical.
4. Run a tiny sample and inspect metadata:

   ```bash
   img2dataset \
     --url_list=urls_with_hashes.parquet \
     --input_format=parquet \
     --url_col=url \
     --output_folder=hash-check \
     --output_format=files \
     --number_sample_per_shard=10 \
     --compute_hash=sha256 \
     --verify_hash='["sha256_expected", "sha256"]' \
     --thread_count=4 \
     --processes_count=1 \
     --enable_wandb=False
   ```

5. If mismatches persist, the source bytes likely differ from the recorded hashes. Decide whether dropping mismatches is desired.

## Incremental recovery checklist

Before rerunning an interrupted command, verify:

- Same `url_list` path/content and row ordering.
- Same `input_format`, `url_col`, `caption_col`, and `verify_hash` settings.
- Same `number_sample_per_shard`; changing it changes shard boundaries.
- Same output format and image options unless you intentionally want a fresh rebuild.
- `incremental_mode="incremental"`, not `extend`.
- `overwrite` is used only after the user agrees to recursive deletion.

Then rerun the original command. Inspect root `*_stats.json` and metadata parquet files for remaining failures.

# Core download API and CLI reference

This reference summarizes public `img2dataset` entry points and core argument behavior verified from the installed package signature, CLI help, README guidance, and source behavior.

## Public entry points

### Python API

```python
from img2dataset import download

download(url_list="urls.txt", output_folder="images")
```

Verified public signature:

```text
download(
    url_list: str,
    image_size: int = 256,
    output_folder: str = "images",
    processes_count: int = 1,
    resize_mode: str = "border",
    resize_only_if_bigger: bool = False,
    upscale_interpolation: str = "lanczos",
    downscale_interpolation: str = "area",
    encode_quality: int = 95,
    encode_format: str = "jpg",
    skip_reencode: bool = False,
    output_format: str = "files",
    input_format: str = "txt",
    url_col: str = "url",
    caption_col: Optional[str] = None,
    bbox_col: Optional[str] = None,
    thread_count: int = 256,
    number_sample_per_shard: int = 10000,
    extract_exif: bool = True,
    save_additional_columns: Optional[List[str]] = None,
    timeout: int = 10,
    enable_wandb: bool = False,
    wandb_project: str = "img2dataset",
    oom_shard_count: int = 5,
    compute_hash: Optional[str] = "sha256",
    verify_hash: Optional[List[str]] = None,
    distributor: str = "multiprocessing",
    subjob_size: int = 1000,
    retries: int = 0,
    disable_all_reencoding: bool = False,
    min_image_size: int = 0,
    max_image_area: float = inf,
    max_aspect_ratio: float = inf,
    incremental_mode: str = "incremental",
    max_shard_retry: int = 1,
    user_agent_token: Optional[str] = None,
    disallowed_header_directives: Optional[List[str]] = None,
    ignore_ssl_certificate: bool = False,
)
```

### Console command

The installed console command is `img2dataset`. It exposes the same parameters through Fire. Full function help is available with:

```bash
img2dataset -- --help
```

Fire also allows the required positional argument as either `URL_LIST` or the named flag `--url_list=...`:

```bash
img2dataset --url_list=urls.txt --output_folder=images --thread_count=8 --image_size=256
# equivalent style:
img2dataset urls.txt --output_folder=images --thread_count=8 --image_size=256
```

For list-valued CLI arguments, quote JSON/Python-list syntax so the shell passes one value:

```bash
img2dataset --url_list=urls.parquet \
  --input_format=parquet \
  --verify_hash='["sha256_expected", "sha256"]'
```

## CLI option groups owned by this sub-skill

| Group | Main options | Notes |
| --- | --- | --- |
| Run construction | `url_list`, `output_folder`, `input_format`, `output_format`, `number_sample_per_shard`, `oom_shard_count` | This sub-skill covers the minimal run shape. Route detailed schemas and writer layouts to `input-output-formats`. |
| Local concurrency | `processes_count`, `thread_count`, `timeout`, `retries`, `max_shard_retry` | `retries` retries individual image downloads; `max_shard_retry` retries failed shards after the shard pass. Route performance tuning to `distributed-execution`. |
| Metadata | `caption_col`, `extract_exif`, `save_additional_columns`, `compute_hash`, `verify_hash` | Captions and EXIF are core run options; route full metadata schema and additional-column design to `input-output-formats`. |
| HTTP policy | `user_agent_token`, `disallowed_header_directives`, `ignore_ssl_certificate` | Keep default opt-out and certificate verification unless the user's policy permits a narrower exception. |
| Restart behavior | `incremental_mode` | One of `incremental`, `overwrite`, or `extend`. Details below. |
| Routed elsewhere | `resize_mode`, `encode_quality`, `encode_format`, `skip_reencode`, `disable_all_reencoding`, filters, `bbox_col`, `distributor`, `subjob_size`, W&B performance use | Use `image-processing` or `distributed-execution`. |

## Argument validation and interactions

### Hash computation and verification

- `compute_hash` must be one of `None`, `md5`, `sha256`, or `sha512`.
- Default `compute_hash="sha256"` computes a raw downloaded image hash and writes a metadata column named `sha256`.
- `verify_hash` must be a two-element list: `[input_hash_column, hash_type]`.
- When `verify_hash` is provided, its `hash_type` must exactly match `compute_hash`; otherwise `download(...)` raises a `ValueError` similar to `verify_hash and compute_hash must be the same`.
- The hash used for verification is computed from the raw downloaded bytes before resize/re-encode. A mismatch causes that sample to be dropped from image output, with metadata `status="failed_to_download"` and `error_message="hash mismatch"`.
- For CLI hash verification, quote the list:

  ```bash
  --compute_hash=sha256 --verify_hash='["sha256_expected", "sha256"]'
  ```

- If you need `compute_hash=None`, the Python API is the least ambiguous path. CLI users should test the exact Fire parsing on a tiny run before applying it to a large dataset.

### Additional columns and reserved names

`save_additional_columns` cannot include metadata columns reserved by img2dataset. The validator rejects these names:

```text
key, caption, url, width, height, original_width, original_height,
status, error_message, exif, md5, sha256, sha512
```

Use distinct input column names for user metadata. If you also use `bbox_col`, img2dataset appends that column to `save_additional_columns` so the downloader can access it; route bbox-specific behavior to `image-processing`.

### Captions and EXIF

- Set `caption_col` for table formats with a caption column. Captions are saved in output samples and represented in metadata as `caption`.
- `extract_exif=True` adds an `exif` metadata column containing a JSON string when EXIF extraction succeeds, or `None` when unavailable/failing.
- For tiny or high-throughput runs where EXIF is not needed, set `extract_exif=False` to reduce work.

## Downloader HTTP behavior

### User-Agent and user-agent token

The downloader sends a browser-like `User-Agent`. If `user_agent_token` is set, it is stripped/lowercased internally and appended as an identifying compatible token. Use this to identify your crawler when a source requires it.

### X-Robots-Tag filtering

When `disallowed_header_directives` is omitted, `download(...)` defaults to:

```python
["noai", "noimageai", "noindex", "noimageindex"]
```

If an HTTP response contains an `X-Robots-Tag` directive in that set, the sample is excluded and metadata records:

```text
status = failed_to_download
error_message = Use of image disallowed by X-Robots-Tag directive
```

Directive matching is lowercased. Headers without a user-agent prefix apply generally. Headers with a prefix, such as `somebot: noindex`, apply only when that prefix matches the configured `user_agent_token`.

To disable this filtering only when the user's policy and permissions allow it:

```bash
--disallowed_header_directives='[]'
```

In the Python API, pass `disallowed_header_directives=[]`. Internally an empty list becomes `None`, which disables the check.

### Retries and timeouts

- `timeout` is the per-image URL open timeout in seconds.
- `retries=N` means up to `N + 1` attempts for an individual image URL.
- If all attempts fail, the last error string is written to metadata `error_message` and the sample is marked `failed_to_download`.
- `max_shard_retry` retries failed shards after the main shard pass, not individual images inside a successful shard.

### SSL certificate handling

By default, SSL certificates are verified. With `ignore_ssl_certificate=True`, the downloader disables hostname checking and sets the SSL context to not verify certificates. This can allow invalid/self-signed HTTPS sources, but it weakens security and should be used only for trusted sources when fixing the certificate chain is not practical.

## Incremental modes

| Mode | Behavior | Use when | Avoid when |
| --- | --- | --- | --- |
| `incremental` (default) | Existing output folder is kept. Done shard ids are inferred from root `*.json` files such as shard stats files, and those shards are skipped. | Recovering an interrupted run with the same URL list and same `number_sample_per_shard`. | You changed input ordering, shard size, or output settings that make old shards incompatible. |
| `overwrite` | Recursively deletes the output folder and starts from zero. | You explicitly want a fresh rebuild. | Any output should be preserved. |
| `extend` | Finds the highest existing root JSON shard id and starts new output shard ids after it. It does not deduplicate existing input rows. | Appending intentionally under new shard ids. | Restarting the exact same interrupted URL list; it can duplicate data with new shard ids. |

For reliable recovery, keep `url_list`, input order, `input_format`, `number_sample_per_shard`, hash settings, and output format consistent between the original and resumed command.

## Core output validation signals

Every successful non-`dummy` shard writes a root metadata parquet file such as `00000.parquet`. Runs also write root shard stats JSON files such as `00000_stats.json`.

Core metadata fields commonly inspected here:

| Field | Meaning |
| --- | --- |
| `url` | Resolved source URL from the input row. |
| `caption` | Present when `caption_col` is set for supported input formats. |
| `key` | Zero-padded sample key; first digits identify shard, last digits identify sample position within shard. |
| `status` | `success`, `failed_to_download`, or `failed_to_resize`. |
| `error_message` | Downloader/resizer error string; `hash mismatch` and `Use of image disallowed by X-Robots-Tag directive` are important core cases. |
| `width`, `height` | Output image dimensions when resize/encode succeeds. |
| `original_width`, `original_height` | Dimensions before resizing when image decode succeeds. |
| `exif` | JSON string or null when `extract_exif=True`. |
| `md5`, `sha256`, `sha512` | Present when that `compute_hash` value is enabled. |

Minimal validation snippet:

```bash
python - <<'PY'
from pathlib import Path
import json
import pandas as pd

out = Path("images")
parquets = sorted(out.glob("*.parquet"))
stats = sorted(out.glob("*_stats.json"))
print("metadata parquet files:", [p.name for p in parquets])
print("stats json files:", [p.name for p in stats])
if parquets:
    df = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
    print(df["status"].value_counts(dropna=False))
    failures = df[df["status"] != "success"][["url", "status", "error_message"]]
    print(failures.head(20).to_string(index=False))
if stats:
    first = json.loads(stats[0].read_text())
    print("first shard stats keys:", sorted(first))
    print("first shard status_dict:", first.get("status_dict"))
PY
```

For full input/output format layouts, writer-specific files, and additional metadata columns, route to `input-output-formats`.

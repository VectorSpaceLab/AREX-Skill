# Core download quickstart

These recipes are self-contained and use only the public `img2dataset` package. They do not require any original repository examples, notebooks, or test fixtures.

## 0. Verify import and CLI help

```bash
python - <<'PY'
import inspect
from img2dataset import download
print("img2dataset.download import ok")
print(inspect.signature(download))
PY

img2dataset -- --help
```

If `img2dataset` is not on `PATH`, try `python -m img2dataset.main -- --help` or reinstall the package in the active environment.

## 1. No-network tiny demo with a local HTTP image

From this sub-skill directory:

```bash
python scripts/tiny_download_demo.py --help
python scripts/tiny_download_demo.py --dry-run
python scripts/tiny_download_demo.py --output-folder tiny-output --output-format files
```

The helper creates a tiny local HTTP-served image fixture, writes a temporary one-URL-per-line list, calls `img2dataset.download`, disables W&B, avoids external network, and prints validation hints. Try alternate output formats:

```bash
python scripts/tiny_download_demo.py --output-folder tiny-webdataset --output-format webdataset
python scripts/tiny_download_demo.py --output-folder tiny-parquet --output-format parquet
python scripts/tiny_download_demo.py --output-folder tiny-dummy --output-format dummy
```

`dummy` is useful for checking downloader flow without saving images; it still writes shard stats JSON.

## 2. CLI quickstart with your URL list

Create a text file containing one image URL per line:

```bash
cat > urls.txt <<'EOF'
https://your-domain.example/image-001.jpg
https://your-domain.example/image-002.jpg
https://your-domain.example/image-003.jpg
EOF
```

Run a small, restartable local download:

```bash
img2dataset \
  --url_list=urls.txt \
  --output_folder=images-files \
  --input_format=txt \
  --output_format=files \
  --image_size=256 \
  --thread_count=8 \
  --processes_count=1 \
  --number_sample_per_shard=1000 \
  --timeout=10 \
  --retries=1 \
  --max_shard_retry=1 \
  --incremental_mode=incremental \
  --enable_wandb=False
```

Validate core status metadata:

```bash
python - <<'PY'
from pathlib import Path
import json
import pandas as pd

out = Path("images-files")
parquets = sorted(out.glob("*.parquet"))
stats = sorted(out.glob("*_stats.json"))
print("parquet metadata:", [p.name for p in parquets])
print("stats files:", [p.name for p in stats])
if parquets:
    df = pd.concat([pd.read_parquet(p) for p in parquets], ignore_index=True)
    print(df["status"].value_counts(dropna=False))
    print(df[["url", "status", "error_message"]].head().to_string(index=False))
if stats:
    print(json.loads(stats[0].read_text()).get("status_dict"))
PY
```

Expected `files` layout for successful rows:

```text
images-files/
  00000.parquet
  00000_stats.json
  00000/
    000000000.jpg
    000000000.json
    ...
```

For detailed output-format layouts, use `input-output-formats`.

## 3. Python API quickstart

```python
from img2dataset import download

download(
    url_list="urls.txt",
    output_folder="images-api",
    input_format="txt",
    output_format="files",
    image_size=256,
    processes_count=1,
    thread_count=8,
    number_sample_per_shard=1000,
    timeout=10,
    retries=1,
    max_shard_retry=1,
    incremental_mode="incremental",
    enable_wandb=False,
)
```

Re-run the same call after an interruption. Keep the same URL list, ordering, `number_sample_per_shard`, and output settings so `incremental` can skip completed shards and finish the rest.

## 4. Captions with CSV or Parquet inputs

Use table inputs when you need captions or extra columns. This sub-skill shows the core pattern; route detailed schemas to `input-output-formats`.

CSV example:

```csv
url,caption
https://your-domain.example/cat.jpg,a cat
https://your-domain.example/dog.jpg,a dog
```

CLI:

```bash
img2dataset \
  --url_list=captioned.csv \
  --input_format=csv \
  --url_col=url \
  --caption_col=caption \
  --output_folder=captioned-files \
  --output_format=files \
  --thread_count=8 \
  --processes_count=1 \
  --enable_wandb=False
```

Python:

```python
from img2dataset import download

download(
    url_list="captioned.csv",
    input_format="csv",
    url_col="url",
    caption_col="caption",
    output_folder="captioned-files",
    output_format="files",
    processes_count=1,
    thread_count=8,
    enable_wandb=False,
)
```

## 5. Hash-verified Parquet to restartable WebDataset

Use this pattern when the input table has captions plus trusted raw-image hashes, and you want a restartable WebDataset output.

Example Parquet columns:

| Column | Meaning |
| --- | --- |
| `url` | Image URL. |
| `caption` | Optional caption. |
| `sha256_expected` | Expected SHA-256 of the raw downloaded image bytes. |

Python:

```python
from img2dataset import download

download(
    url_list="urls_with_hashes.parquet",
    input_format="parquet",
    url_col="url",
    caption_col="caption",
    output_folder="dataset-wds",
    output_format="webdataset",
    image_size=256,
    processes_count=1,
    thread_count=16,
    number_sample_per_shard=10000,
    compute_hash="sha256",
    verify_hash=["sha256_expected", "sha256"],
    retries=1,
    max_shard_retry=1,
    incremental_mode="incremental",
    enable_wandb=False,
)
```

CLI equivalent:

```bash
img2dataset \
  --url_list=urls_with_hashes.parquet \
  --input_format=parquet \
  --url_col=url \
  --caption_col=caption \
  --output_folder=dataset-wds \
  --output_format=webdataset \
  --image_size=256 \
  --thread_count=16 \
  --processes_count=1 \
  --number_sample_per_shard=10000 \
  --compute_hash=sha256 \
  --verify_hash='["sha256_expected", "sha256"]' \
  --retries=1 \
  --max_shard_retry=1 \
  --incremental_mode=incremental \
  --enable_wandb=False
```

Validation:

```bash
python - <<'PY'
from pathlib import Path
import pandas as pd

out = Path("dataset-wds")
print("tar shards:", [p.name for p in sorted(out.glob("*.tar"))[:5]])
meta = sorted(out.glob("*.parquet"))
print("metadata shards:", [p.name for p in meta[:5]])
if meta:
    df = pd.concat([pd.read_parquet(p) for p in meta], ignore_index=True)
    print(df["status"].value_counts(dropna=False))
    print("hash mismatches:", (df["error_message"] == "hash mismatch").sum())
PY
```

Recovery after interruption: rerun the same command. Do not switch to `extend` for the same input; `extend` starts new shard ids and can duplicate already processed rows. Use `overwrite` only when you intentionally want to delete and rebuild `dataset-wds`.

## 6. SSL, robots, and retry decision flow

1. Start conservative:

   ```bash
   --timeout=10 --retries=1 --max_shard_retry=1
   ```

2. If errors are transient network timeouts or connection resets, increase `--retries` first, then consider larger `--timeout`.
3. If metadata shows `Use of image disallowed by X-Robots-Tag directive`, keep the default exclusion unless the user has permission to override source opt-out headers.
4. If a site requires crawler identification, set a clear token:

   ```bash
   --user_agent_token=my-research-crawler
   ```

5. Only when policy allows ignoring opt-out headers, disable directive filtering explicitly:

   ```bash
   --disallowed_header_directives='[]'
   ```

6. If HTTPS fails with certificate errors, prefer fixing the trust store or source certificate. Use this only for trusted sources as a last resort:

   ```bash
   --ignore_ssl_certificate=True
   ```

7. Re-validate metadata after any policy change, especially `status`, `error_message`, and stats `status_dict`.

## 7. Safe defaults checklist

- `enable_wandb=False` unless the user explicitly wants W&B logging.
- `incremental_mode="incremental"` for recovery, not `overwrite`.
- `retries=1` or `2` for mild network flakiness; avoid very high retries until you inspect errors.
- `compute_hash="sha256"` for audit metadata; use `verify_hash` only with trusted input hash columns.
- Keep default `disallowed_header_directives` and SSL verification unless there is an explicit permission/security decision.
- Move image transform choices to `image-processing`, output layout choices to `input-output-formats`, and high-throughput tuning to `distributed-execution`.

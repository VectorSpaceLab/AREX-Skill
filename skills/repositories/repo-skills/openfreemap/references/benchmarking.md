# Benchmarking

## Purpose

Read this when the task is about replaying OpenFreeMap nginx traffic, generating path lists from logs, or sanity-checking localhost throughput.

## Safe workflow

1. Capture or synthesize a small nginx access JSONL sample.
2. Convert the sample to a path list with `scripts/nginx_to_path_list.py`.
3. Replay the list against a local nginx instance with `wrk` and `scripts/wrk_custom_list.lua`.

## Why localhost only

The benchmark measures server throughput, not internet speed. Run it against localhost or a local VM endpoint, not across the public internet.

## Helper scripts

### `scripts/nginx_to_path_list.py`

Converts a tiny access log sample into a list of PBF paths that `wrk` can replay.

Expected inputs:

- JSONL access log rows
- status `200`
- method `GET`
- URIs containing `tiles/` and ending in `.pbf`

### `scripts/wrk_custom_list.lua`

Replays the generated path list with `wrk`.

Environment variables used by the helper:

| Variable | Meaning |
| --- | --- |
| `OFM_PATH_LIST` | Path to the newline-delimited replay list. Defaults to `path_list_500k.txt`. |
| `OFM_URL_BASE` | URL path prefix that gets prepended to each replay line. Defaults to `/planet/fake_version/`. |
| `OFM_HOST_HEADER` | Host header sent with each request. Defaults to `ofm`. |


## Example flow

```bash
python scripts/nginx_to_path_list.py --input access.jsonl --output path_list_500k.txt
wrk -c10 -t4 -d60s -s scripts/wrk_custom_list.lua http://localhost
```

Useful `wrk` parameters from the repo docs:

- `-c10` for a modest concurrent connection count
- `-t4` for a multicore local benchmark
- `-d60s` for a one-minute run

## Interpreting results

The historical benchmark notes show that localhost throughput can be dramatically higher than over-the-network throughput. Use those numbers as rough sanity context, not as hard targets.

## Troubleshooting

- `wrk` missing: install it on the benchmark host or skip the benchmark.
- Empty replay list: the access sample likely had no matching 200 GET PBF requests.
- The results look slow over the network: rerun on localhost or a loopback-backed VM.
- The replay path list uses the wrong prefix: regenerate it or override the base path in the Lua helper.

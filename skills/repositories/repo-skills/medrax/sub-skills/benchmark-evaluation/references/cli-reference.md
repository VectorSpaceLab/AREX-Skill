# CLI reference

The benchmark runner's reference entry point is `quickstart.py`. Run
`python quickstart.py --help` in the environment that contains the runner
before spending a request; the following flags are the supported quickstart
surface.

| Flag | Default | Meaning |
|---|---:|---|
| `--model MODEL` | `chatgpt-4o-latest` | Request model identifier. Pass the exact model name accepted by the provider. |
| `--temperature FLOAT` | `0.2` | Sampling temperature recorded in each log entry. |
| `--log-prefix PREFIX` | model name | Prefix for the timestamped JSONL log filename. Choose a writable, non-secret location/prefix. |
| `--max-cases INTEGER` | all | Process at most the first `INTEGER` cases. Use `1` for a smoke run. |
| `--use-urls` | off | Resolve `image_source_urls` through HTTP before sending the multimodal request. Requires explicit network authorization. |

A conservative invocation is:

```bash
python quickstart.py --model "$MODEL" --temperature 0.2 \
  --log-prefix benchmark-smoke --max-cases 1
```

For a URL smoke run, add `--use-urls`. Do not combine URL mode with an
unbounded case count. `--max-cases` is a prefix limit, not a shuffle or
stratified sample. Negative values are not a valid bounded plan; validate the
runner's behavior and stop rather than relying on accidental slicing.

## Environment

- `OPENAI_API_KEY` must be present for the reference quickstart. Treat it as a
  secret and never print it.
- `OPENAI_BASE_URL` is optional and is forwarded as the client's compatible API
  base URL when present. It is useful for a local gateway or another provider.
- `OPENAI_MODEL` is documented as a compatible-provider convention, but the
  reference quickstart selects the CLI `--model` value. Use
  `--model "${OPENAI_MODEL:-chatgpt-4o-latest}"` if the environment variable is
  your source of truth.
- A custom endpoint and key do not prove that the selected model accepts image
  inputs. Perform a one-case smoke run and inspect the response before scaling.

The runner obtains the benchmark JSONL from its configured dataset location,
then initializes the client. A missing key therefore fails before useful
inference; a malformed case or unavailable image can fail later. Run the local
manifest validator first whenever a local manifest is available.

## Exit and output expectations

A normal run prints progress and a summary, and verifies that the timestamped
log exists and is non-empty. A graceful interrupt leaves a partial log; retain
its processed/skipped counts and mark the run interrupted. A persistent API
exception may be re-raised after retries, so a non-zero exit does not imply
that every case failed. Never delete a partial log to make a run appear
complete.

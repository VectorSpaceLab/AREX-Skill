# Troubleshooting and recovery

Use only safe local checks first. Do not turn a diagnosis into a real download,
installation, or API call without approval.

## Viral retrieval

### NCBI datasets CLI, API, or cache

- The optimized SARS-CoV-2/Alphainfluenza path looks for a working `datasets`
  executable in `PATH` first and otherwise uses gget's bundled binary. It
  checks `datasets --version` and caches the detected path. Run
  `command -v datasets` and `datasets --version` manually as a read-only check;
  if absent/broken, use the normal API path with the internal `_skip_cache=True`
  option only when you understand that it is an internal escape hatch.
- A cached package failure is designed to fall back to normal API retrieval.
  If both fail, inspect `command_summary.txt`, retain any partial metadata, and
  retry later or narrow the query. Do not repeatedly rerun a broad query against
  a failing service.
- API timeouts, 429/5xx responses, connection resets, and failed pagination or
  sequence batches are recorded in the summary. Respect NCBI rate limits;
  `NCBI_API_KEY` raises E-utilities throughput from the unauthenticated limit
  but does not guarantee service availability. Passing `api_key=` takes
  precedence over the environment variable and must be kept secret.
- Large responses may use chunking/streaming, but disk, memory, bandwidth, and
  NCBI server limits still apply. `download_all_accessions=True` can mean the
  entire virus taxonomy and may take hours; never use it as an exploratory
  default.

### Date and filter validity

- Use `YYYY-MM-DD` for `min_collection_date`, `max_collection_date`,
  `min_release_date`, and `max_release_date`. The implementation accepts
  partial date forms in comparisons, but a malformed date can reject records or
  fail validation. Confirm min <= max; equal bounds are valid.
- Valid `nuc_completeness` values are `complete` and `partial`, and valid
  `source_database` values are `genbank` and `refseq`. A `complete` request is
  often server/cache filtered; sequence length and ambiguity are separate
  checks.
- `host` and `env_source` cannot be combined. `env_source` is a GenBank-based
  environmental-source filter and excludes named-host logic. GenBank-dependent
  filters automatically turn on detailed GenBank retrieval, which adds API
  calls and files.
- A zero-result summary is not necessarily an API failure. Check the filter
  breakdown and relax one constraint at a time, starting with dates, host,
  location, or completeness. Confirm the taxon/accession spelling and whether
  an accession query needs `is_accession=True`.

### Large downloads and temporary files

- Always provide a dedicated `outfolder` and confirm free space before a large
  query. Results include FASTA, CSV, JSONL, and possibly full GenBank XML/CSV;
  temporary downloads can require additional space.
- Leave `keep_temp=False` for routine runs. Set it only when debugging and
  ensure the directory is private because it can contain raw metadata and
  partial files. Do not manually delete a partial metadata file until the
  recovery decision is complete.
- If a run fails after metadata retrieval, use the reported
  `*_partial_metadata_api_failure.jsonl` as `baseline_metadata` on a new run.
  With `merge_results=True`, inspect the new merged CSV; with `False`, preserve
  and compare the new-only output. A baseline skips matching accessions; it is
  not a general checkpoint for a changed filter query.
- For a completed run, count FASTA headers, non-empty JSONL rows, and CSV data
  rows. If counts differ, inspect the summary and GenBank fallback path before
  treating the dataset as valid.

## Mutation generation

### Sequence-ID mismatch

1. Print/inspect FASTA headers and table IDs without changing either file.
2. Normalize each FASTA title as gget does: first whitespace-delimited token,
   then remove the dot and version suffix. Remove spaces/dots from table IDs
   only if that is the intended identifier, not as an uncontrolled repair.
3. Run `scripts/validate_mutation_inputs.py --fasta ... --mutations ...`.
   Correct the table or FASTA in a new file, then rerun `gget.mutate` with a new
   `out`; never overwrite the source FASTA/table during recovery.
4. If no IDs join, expect `ValueError`; if some join, expect unmatched rows to
   be dropped with a warning. Record the dropped rows for audit.

### Coordinates, bases, and ambiguous input

- `c.35G>A` is one-based and checks that position 35 is `G` in the matching
  sequence. A mismatch increments the incorrect-wild-type counter and drops
  the row; it does not silently substitute the requested base.
- `c.35del`, range deletion, insertion, delins, duplication, and inversion have
  different coordinate boundaries. Use the tiny fixtures or a hand-calculated
  short sequence to verify a new annotation. Positions beyond sequence length,
  uncertain `?`, ambiguous parentheses, intronic `+/-`, and `*` regions are
  rejected/count-reported rather than guessed.
- `N` is accepted as an input character. Use `max_ambiguous` to exclude mutant
  fragments with too many Ns; do not call an N a validated reference base.
  Non-nucleotide characters produce a warning and especially compromise
  inversion correctness.
- If `translate=True` produces `X`, check the requested frame and boundaries,
  `store_full_sequences=True`, and whether the codon is incomplete or
  ambiguous. Translation is an annotation output, not a sequence correction.

### Output and update safety

- `out=None` returns strings (or an updated DataFrame when `update_df=True`);
  `out=...` writes FASTA. Since identical mutants may be merged by default,
  set `merge_identical=False` when row-level cardinality matters.
- Updated mutation tables can be very large. Set an explicit new
  `update_df_out`, keep the original table, and confirm the output schema and
  row count. Full sequences and translation increase size substantially.

## Setup and GPT

### Setup side effects

- `gget.setup` is not a dry-run. Check `sys.version`, OS, `uv`/pip/curl/git,
  importability, disk, and permission first. Use a dedicated environment and
  snapshot its package state if reproducibility matters.
- If an install fails, do not blindly repeat: capture the package error,
  verify Python compatibility, and inspect whether a partial package or ELM
  file set was left behind. For ELM, a custom `out` is not the package's live
  data location; use the default package location only after approving that
  mutation. AlphaFold setup may clone repositories and download multi-gigabyte
  model parameters and is unsupported on Windows in this implementation.

### OpenAI package/API-key/version mismatch

- `gget.gpt` requires the legacy `openai.ChatCompletion.create` API and setup
  pins `openai<=0.28.1`. If the import works but `ChatCompletion` is absent,
  check `python -c "import openai; print(openai.__version__)"` and use the
  dedicated compatibility environment rather than downgrading a shared one.
- If the key is missing or rejected, stop before retrying. The wrapper receives
  `api_key` as an argument and does not read `OPENAI_API_KEY` itself. Do not
  print or save the key. HTTP/auth/rate-limit/model errors are service-side;
  validate the model name, account access, billing limit, and prompt size
  outside the wrapper before another paid request.
- A mocked `openai.ChatCompletion.create` is the safe test path. The native
  test asserts the request fields and a returned text with a trailing newline;
  a live call is not required to verify integration.

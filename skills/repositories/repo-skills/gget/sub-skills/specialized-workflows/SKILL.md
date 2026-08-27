---
name: specialized-workflows
description: "Operate gget's viral dataset, mutation-generation, optional setup,
  and legacy GPT workflows with explicit filters, file contracts, validation,
  and side-effect boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Specialized workflows

Use this skill for four gget entry points:

- `gget.virus`: retrieve and filter viral sequence datasets from NCBI Virus.
- `gget.mutate`: apply standard nucleotide mutation annotations to FASTA or
  in-memory nucleotide sequences.
- `gget.setup`: install/download optional dependencies or ELM data.
- `gget.gpt`: call the legacy OpenAI ChatCompletion wrapper.

Read the matching reference before a non-trivial run:
[virus workflow](references/virus-workflow.md), [mutation contract](references/mutation-contract.md),
[setup and GPT](references/setup-gpt.md), and
[troubleshooting](references/troubleshooting.md). For a safe preflight of a
FASTA/table pair, use [validate_mutation_inputs.py](scripts/validate_mutation_inputs.py).
It reads inputs and prints JSON; it never mutates them, downloads data, installs
packages, or calls an API.

## Route first

- Route general Ensembl/NCBI sequence retrieval, translation, alignment, BLAST,
  or related sequence operations to `sequence-tools`.
- Route cancer mutation database lookup or cancer structure interpretation to
  `disease-structure`; use `mutate` only to transform sequences from an
  already-selected mutation table.
- Keep `virus` for viral dataset retrieval/filtering, not arbitrary taxonomy
  or generic FASTA manipulation.

## Choose the workflow

1. **Viral retrieval.** Start with a taxon name, taxon ID, accession, a
   space-separated accession list, or a one-accession-per-line text file. Set
   `is_accession=True` for accession forms. For SARS-CoV-2 or Alphainfluenza,
   use the explicit optimized flag for accession queries.
2. **Mutation generation.** Start with nucleotide FASTA (or a string/list) and
   a mutation string, list, CSV/TSV, or DataFrame. Establish the sequence-ID
   join before invoking the transform.
3. **Optional setup.** Treat `setup` as an installation/download operation,
   not a harmless probe. Inspect the target environment and obtain approval
   before running it.
4. **Legacy GPT.** Treat `gpt` as a credentialed, billable, unmaintained
   compatibility wrapper. Do not use it without an explicit API key and
   confirmation of the old OpenAI client contract.

## Viral run recipe

- Select narrow filters before downloading. `virus` validates inputs, obtains
  server-side metadata (or uses cached metadata), applies local metadata
  filters, performs GenBank-dependent filtering when needed, downloads only
  surviving accessions, then applies sequence-dependent filters.
- Use `outfolder` explicitly. Expect FASTA plus metadata CSV/JSONL and
  `command_summary.txt`; GenBank mode adds detailed CSV and full XML/CSV.
- For incremental work, pass a baseline CSV/JSONL/JSON/text accession file.
  With `merge_results=True`, inspect the merged CSV; with `False`, inspect the
  new-only CSV and retained baseline reference. Never overwrite the source
  baseline as a recovery shortcut.
- Confirm output counts agree across FASTA, final metadata JSONL, and CSV.
  Read the summary's counts for API records, metadata survivors, GenBank
  survivors, final sequences, filter exclusions, and failed operations.

## Mutation run recipe

- Ensure every mutation-table `seq_ID` matches the FASTA identifier after gget's
  normalization: first token only, with a dot/version suffix removed. A missing
  join is an input error, not permission to guess.
- Use HGVS-like nucleotide annotations such as `c.35G>A`, ranges with
  `del`/`ins`/`delins`, `dup`, or `inv`; verify the wild-type base for a
  substitution. Use `k` to bound retained flanks (default 30).
- Return a list when `out=None` and `update_df=False`; write mutant FASTA when
  `out` is supplied. Output headers are `>[seq_ID]:[mut_ID]` in the current
  implementation (the older docs show an underscore; follow the live output).
- Request `update_df=True` for mutation annotations and sequences in a CSV/TSV
  output. Full-sequence and translation columns require
  `store_full_sequences=True`; translation uses the requested nucleotide frame
  and emits `X` for unknown/incomplete codons. Keep the original FASTA/table;
  write to a new output path.

## Setup and GPT boundaries

- Supported setup module names are `alphafold`, `cellxgene`, `elm`, `gpt`, and
  `cbio`. It may install with `uv` or pip, download ELM files with curl, clone
  and patch AlphaFold dependencies, and download large model parameters.
- For ELM, omit `out` if `gget.elm` must find the downloaded files; a custom
  `out` is an independent copy and is not used by the module. For AlphaFold,
  expect platform/dependency/model-size constraints and prefer a dedicated
  environment.
- `gpt` uses `api_key` directly, sets `openai.api_key`, calls
  `openai.ChatCompletion.create`, returns text with a trailing newline, and
  optionally writes the text to `out`. The wrapper targets `openai<=0.28.1`;
  newer clients commonly lack this endpoint. Never place keys in files or
  command history, and do not send sensitive data in prompts.

## Validate and recover

- Before network or credentialed work, run the mutation preflight and inspect
  its JSON errors. For virus runs, validate date ranges, mutually exclusive
  `host`/`env_source`, storage, and intended output location first.
- Do not run real downloads, setup, or GPT calls in a dry-run. Use mocked API
  responses or tiny local fixtures for tests. On a viral API failure, preserve
  the partial JSONL and resume with it as `baseline_metadata`; on a mutation
  mismatch, fix IDs or the table and rerun to a new FASTA; on setup/GPT errors,
  inspect package/version and environment state before reinstalling.
- Stop and report when a service is unavailable, a credential is absent, the
  requested dataset is too large, or a required dependency would alter the
  environment without approval. See [troubleshooting](references/troubleshooting.md)
  for concrete recovery paths.

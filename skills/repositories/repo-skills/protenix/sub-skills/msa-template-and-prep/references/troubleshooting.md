# MSA, Template, and Prep Troubleshooting

## Safety Classification

Treat these actions as expensive or side-effecting until the user confirms local resources and permission:

- `protenix msa` in `protenix` mode when it may call an MSA service or local MMseqs database.
- `protenix msa` in `colabfold` mode when it may use ColabFold/MMseqs services or databases.
- `protenix mt` because it may run MSA search, HMMER, and database lookup/download.
- `protenix prep` because it may run protein MSA, template search, and RNA MSA search.
- ColabFold/MMseqs local database setup or search.
- Training MSA steps that read raw mmCIF trees, large `.m8` files, UniRef databases, or many `.a3m` files.
- Database download/generation flows; they can download large datasets and require external tools.

Use the bundled layout checker first when files already exist.

## Command Name Mismatch

If a documented long name or internal function name fails, use the registered CLI commands:

- Use `protenix msa` for protein MSA generation.
- Use `protenix mt` for protein MSA plus template search.
- Use `protenix prep` for protein MSA plus template plus RNA MSA search.

The internal functions are named `msa`, `msatemplate`, and `inputprep`, but the installed CLI registers only `msa`, `mt`, and `prep` for these workflows.

## Stale JSON Paths

Symptoms:

- `pairedMsaPath`, `unpairedMsaPath`, `templatesPath`, or RNA `unpairedMsaPath` points to a file that no longer exists.
- Protenix logs that a path does not exist and will re-search MSA.
- Prediction fails later because a path was moved after preprocessing.

Response:

1. Run the checker on the JSON:
   `python sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py input.json --expect-template --expect-rna`.
2. If files were moved, update the JSON path fields rather than rerunning search.
3. If files are genuinely missing, choose the smallest regeneration command: `msa` for protein MSA, `mt` for templates, or `prep` for RNA MSA too.
4. If the user wants a forced fresh search, remove stale path fields from a copy of the JSON before running preprocessing.

## Forced Fresh Search

Protenix intentionally skips stages with valid existing paths. To force regeneration:

- Remove `pairedMsaPath` and `unpairedMsaPath` from protein chains before `protenix msa` or `protenix mt`.
- Remove `templatesPath` before `protenix mt` if template search should rerun.
- Remove RNA `unpairedMsaPath` before `protenix prep` if RNA MSA search should rerun.
- Use a fresh output directory when comparing old and new outputs.

Do not delete the user's existing files unless explicitly asked; edit a copy of the JSON instead.

## Missing HMMER or Kalign Binaries

Symptoms:

- `hmmsearch binary path should not be None`.
- `hmmbuild binary path should not be None`.
- `nhmmer binary path should not be None`.
- `hmmalign binary path should not be None`.
- An explicit binary path is supplied but does not exist.
- Prediction or template-feature parsing reports missing `kalign`.

Fixes:

- Install or activate an environment/container that includes the needed binaries.
- For template search, provide `--hmmsearch_binary_path` and `--hmmbuild_binary_path` if binaries are not on `PATH`.
- For RNA search, provide `--nhmmer_binary_path`, `--hmmalign_binary_path`, and `--hmmbuild_rna_binary_path` or the shared `--hmmbuild_binary_path` as appropriate.
- For prediction with templates, route to `../../cli-and-inference/SKILL.md` for `--kalign_binary_path` planning.
- If the user cannot install HMMER, avoid `protenix mt` and `protenix prep`; use precomputed `templatesPath` and RNA `unpairedMsaPath` files instead.

## Missing Search Databases

Symptoms:

- Template search tries to download `pdb_seqres_2022_09_28.fasta`.
- RNA MSA search tries to download NT-RNA, Rfam, or RNAcentral databases.
- Search is slow or fails due to network policy or disk space.

Fixes:

- Use a search database directory containing:
  - `pdb_seqres_2022_09_28.fasta`
  - `nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta`
  - `rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta`
  - `rnacentral_active_seq_id_90_cov_80_linclust.fasta`
- Provide explicit paths with `--seqres_database_path`, `--ntrna_database_path`, `--rfam_database_path`, and `--rna_central_database_path`.
- Validate file presence with the checker before running expensive commands.
- If downloads are not allowed, do not rely on Protenix defaults that auto-download missing databases.

## MSA Header Taxonomy Issues

Likely cause: `pairing.a3m` headers cannot be parsed into species identifiers.

Checks:

- Inspect `pairing.a3m` headers after `>query`.
- Good paired headers often look like `UniRef100_<hit>_<taxonomy-id>/` or UniProt `sp|...` / `tr|...` headers with species/taxonomy cues.
- Risky headers are generic hit ids with no taxid, query-only files, or raw ColabFold names that cannot be mapped to species.

Fixes:

- Use Protenix post-processing in `protenix` mode when possible because it can create split `pairing.a3m` and `non_pairing.a3m` files.
- For local ColabFold workflows, ensure a post-processing step adds pseudo taxonomy IDs before splitting.
- Do not point `pairedMsaPath` directly at raw ColabFold output unless it has already been transformed into Protenix-compatible paired layout.
- If no taxonomy is recoverable, expect `pairing.a3m` to be query-only and rely on `non_pairing.a3m`; warn that multimer pairing quality may degrade.

## Missing Pairing, Non-Pairing, or Template Files

Symptoms:

- MSA directory contains only one of `pairing.a3m` or `non_pairing.a3m`.
- `templatesPath` points to `hmmsearch.a3m`, but the file is absent.
- Template search cannot find usable MSA input.

Checks:

- Run the checker on the MSA directory.
- For protein MSA-only inference, at least one useful protein MSA can be enough, but missing paired data affects multimers and missing unpaired data affects evolutionary depth.
- For template search, `pairing.a3m` and/or `non_pairing.a3m` must exist before HMMER can build/search a profile.

Fixes:

- If only template output is missing and MSA files exist, run template search after confirming HMMER and seqres database.
- If both MSA files are missing, rerun protein MSA search or supply precomputed files.
- If paths point to the wrong directory, fix JSON fields rather than moving files blindly.

## Dummy or Thin MSAs

Protenix may create dummy files to keep a workflow moving when MSA search cannot produce depth:

```text
>query
<original-sequence>
```

Respond by:

- Warning that MSA depth is effectively one sequence.
- Checking whether MMseqs/ColabFold search actually produced raw `.a3m` files.
- Checking for taxonomy metadata when paired MSA was expected.
- Recommending rerun only after search service, database, and network permissions are confirmed.

## RNA Database Selection

Symptoms:

- The JSON includes `rnaSequence`, but no RNA `unpairedMsaPath` exists.
- `prep` fails during RNA search.
- The user has released RNA MSA data but does not know which file to use.

Response:

- Prefer existing released RNA MSA data when it covers the sequence: look up `rna_msa/rna_sequence_to_pdb_chains.json`, choose the first mapped PDB entity id, and validate `rna_msa/msas/<entity>/<entity>_all.a3m`.
- If no released mapping exists, use custom RNA A3M if supplied and validate it with the checker.
- If search is necessary, require `nhmmer`, `hmmalign`, `hmmbuild`, and the three RNA database FASTAs.
- Use `--nhmmer_n_cpu` to bound CPU use when running RNA search.

## ColabFold Mode Limitations

Common limitations:

- Requires external ColabFold/MMseqs installation and databases.
- Raw combined A3M may not be split per Protenix chain.
- Raw headers may not carry taxonomy data needed for paired MSA species grouping.
- Outputs can be large, especially with environmental database hits.

Mitigation:

- Validate the generated split directory before prediction.
- Use query-only `pairing.a3m` only as a deliberate fallback, not as evidence of real pairing.
- Keep ColabFold setup and database commands reference-only unless the user confirms permission and resources.

## Huge Outputs and Network Requirements

Symptoms:

- Search directories grow unexpectedly large.
- Commands hang while downloading databases or querying services.
- Disk quota or network policy errors occur.

Response:

- Stop and clarify storage/network permission before continuing.
- Prefer validating/reusing existing paths over rerunning searches.
- Use a fresh, user-approved output directory for expensive reruns.
- Avoid bulk training MSA generation unless the user explicitly asked for dataset-scale preprocessing.

## Output Suffix Confusion

Common confusion:

- `protenix msa` with JSON can return a sibling `*-update-msa.json`.
- `protenix mt` and `protenix prep` can return `*-final-updated.json` when template or RNA paths were added.
- If MSA search created `*-update-msa.json` first, the final stage replaces `-update-msa` with `-final-updated`.
- If nothing changed, Protenix returns the original or intermediate JSON unchanged.

When a user asks which JSON to predict from, use the returned path from the command or API. If multiple files exist, prefer `*-final-updated.json` over `*-update-msa.json`, and prefer `*-update-msa.json` over the original only when it contains new path fields.

## Template Parser Errors

Template parser and prefilter errors usually mean `templatesPath` exists but its contents or referenced template structures are unusable.

Error classes to recognize:

- Parsing and chain errors: malformed mmCIF, no chains, no atom data, multiple chains where one was expected.
- Atom mask errors: template atom positions are all masked or unavailable.
- Alignment errors: sequence not in template, query-to-template alignment failed, or distance checks failed.
- Prefilter/date errors: hit is too recent, too short, duplicate/subsequence-like, or has too little alignment coverage.

Response:

1. Validate that `templatesPath` exists and is readable.
2. Confirm `hmmsearch.a3m` came from the same MSA directory as the chain's `pairedMsaPath`/`unpairedMsaPath`.
3. Confirm the template database and structure files match the intended release/date policy.
4. If template quality is not required, reroute prediction planning to run without templates instead of adding a bogus `templatesPath`.

## Training MSA Layout Fails

Symptoms:

- Training loader cannot map a sequence to an MSA directory.
- `pairing.a3m` and `non_pairing.a3m` are present but under raw `.a3m` file names instead of integer directories.
- Pairing is poor because UniRef hits do not contain taxonomy IDs.

Checks:

- `common/seq_to_pdb_index.json` exists and maps exact sequence strings to integer ids.
- Each integer id has `mmcif_msa_template/<id>/pairing.a3m` and `non_pairing.a3m`.
- `hmmsearch.a3m` exists when template features are expected.
- Pairing headers contain taxonomy-like identifiers.

Fixes:

- Regenerate the mapping from unique protein sequences if sequence strings changed.
- Add taxids before splitting raw A3M files.
- Split UniRef100 hits to `pairing.a3m` and other hits to `non_pairing.a3m`.
- Route full dataset bioassembly/index preparation to `../../training-and-data-pipeline/SKILL.md` after MSA layout is fixed.

## Import or First-Run Model Errors During Prep

Some Protenix imports may initialize optional compiled kernels before reaching MSA logic. If a prep command fails before search starts with CUDA, compiler, or optional-extension errors:

- Confirm the environment has the required compiler/CUDA support for the selected Protenix install.
- Try a safer model/runtime configuration only if the task is actually prediction-related.
- Route CUDA/kernel troubleshooting to the root skill or advanced model configuration guidance rather than changing MSA layout guidance.

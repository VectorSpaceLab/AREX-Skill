# Sequence-tools troubleshooting

Use the smallest safe diagnosis first. Preserve the original input and output directory, record the exact gget version/tool arguments, and do not silently change molecule type, database, assembly, or query/reference orientation.

## Input and FASTA failures

**`FileNotFoundError` or an unsupported file-format `ValueError`**

- Confirm the path is relative to the current shell/Python working directory and is readable.
- BLAST and BLAT recognize `.fa` and `.txt` paths; AlphaFold recognizes `.fa` and `.txt`; MUSCLE/DIAMOND use a string containing a dot as a path-like input. Avoid relying on a nonstandard extension.
- A literal sequence containing `.` can be mistaken for a file path by the wrappers. Put it in a valid FASTA file or remove annotation characters before passing it.

**`Expected FASTA to start with a '>' character`**

- The first nonempty line must be a header beginning with `>`; the shared parser does not accept a bare sequence file for a path.
- Put sequence text after the header, and use one or more sequence lines before the next header. Do not place two headers consecutively.
- Check that the sequence is not an empty line, a comment, or a copied alignment with spaces/formatting. For BLAST/BLAT, remember that only the first complete record is submitted.

**Unexpected empty sequence or missing record**

- Confirm every header is paired with at least one sequence line. A malformed or empty FASTA is not a valid no-hit experiment.
- Inspect record count and lengths with a small local parser before retrying a remote tool. The bundled package does not trim multiple FASTA records into a batch for BLAST/BLAT.

## Type mismatch and ambiguous alphabets

**Default says the input is not nucleotide or amino acid**

- Remove whitespace, digits, stop symbols, gap characters, and FASTA headers from a literal sequence.
- For BLAST, choose an explicit `program` and `database`; for BLAT, choose an explicit `seqtype`. Valid BLAST programs are `blastn`, `blastp`, `blastx`, `tblastn`, `tblastx`; valid BLAT types are `DNA`, `protein`, `translated%20RNA`, `translated%20DNA`.
- A valid protein made only from `A/T/G/C/N` is inherently ambiguous to gget's default detector and will be treated as nucleotide. Set `program="blastp"` and a protein database, or `seqtype="protein"`, instead of accepting the default.
- `translated=True` in DIAMOND means nucleotide query → amino-acid reference (`blastx`). It does not mean protein query → nucleotide reference.
- ELM accepts amino-acid input but warns on invalid amino-acid characters; a UniProt accession must use `uniprot=True`. Do not treat an accession as a raw protein string.
- AlphaFold expects protein sequences and applies strict length validation (16–3,400 each; 2,500 monomer maximum; 3,400 total).

## BLAST and BLAT remote failures

**Slow, throttled, or failed BLAST**

- BLAST is a queued NCBI web request. The implementation waits before polling; `WAITING` is normal, while `FAILED`/`UNKNOWN` or a missing significant-similarity table returns `None` after logging.
- Respect the service rules: at least 10 seconds between submissions, no more frequent than once per minute for a given RID, and schedule batches over 50 searches during the service's recommended off-hours. Do not parallelize retries.
- Lower `limit`, use an appropriate database, and increase `expect` only when biologically justified. A short sequence may have no significant hit.
- If an explicit program was supplied with `database="default"`, add a compatible database; the wrapper rejects that combination before contacting NCBI. Verify `program` and `database` case-insensitively against the supported lists.
- Keep remote results with the request settings. A DataFrame with zero rows or `None` is not evidence that the sequence was invalid without checking the logged service message.

**BLAT returns `None`, wrong genome, or no rows**

- A sequence shorter than the UCSC service's useful minimum (commonly about 20 characters) may produce no match. Use a longer query when possible.
- Input over 8,000 characters is silently reduced to the first 8,000 with an informational log. Split or choose a region deliberately instead of assuming full-length alignment.
- Check the `genome` column. `human`, `mouse`, and `zebrafinch` map to `hg38`, `mm39`, and `taeGut2`; an unrecognized assembly can be served as UCSC's default genome with a warning.
- UCSC transient HTTP 429/5xx, network errors, and HTML throttle pages are retried four times with exponential backoff. After the final failure, wait and reduce request frequency rather than changing sequence type.
- A type mismatch can return no hits or misleadingly poor matches. Use `DNA` for DNA and `protein` for amino acid input; use the translated choices only when the query/reference biology calls for them.

## MUSCLE local binary and output failures

**MUSCLE is missing, cannot execute, or permission is denied**

- The wrapper selects a platform-specific packaged executable and attempts to grant execute permission. This generated skill does not ship or repair that binary.
- Check the executable path supplied by the package/environment, run its version/help command safely, and verify the file is executable. On Unix, a dynamic-linker error is different from a sequence error; inspect stderr.
- If the packaged binary is absent, gget attempts to compile MUSCLE on Linux/macOS. Compilation needs `git`, `make`, a C/C++ compiler, and `sed`; Windows compilation is explicitly unsupported by `compile_muscle`.
- Do not run a network clone/compile automatically in a restricted or offline environment. Install a compatible executable or get explicit approval for the compiler workflow.

**Alignment output is missing or empty**

- Pass an explicit `out="...afa"`; `out=None` prints a colored alignment and deletes the temporary file.
- Ensure the parent directory is writable and the process completed without a nonzero subprocess status. Validate that the `.afa` contains every expected header and equal-length aligned sequences.
- Choose `super5=True` for a large input when PPP is too slow or memory hungry. It is a different algorithmic mode, not a repair for malformed input.

## DIAMOND binary, ordering, and database lifecycle

**`DIAMOND version check failed`, loader error, or permission error**

- gget invokes the binary three times: `version`, `makedb`, then `blastp`/`blastx`. Diagnose the first failing command and preserve stderr.
- Verify the explicit `diamond_binary` path (or the package-selected binary), execute a harmless `diamond version`, and check execute permission and architecture/shared-library compatibility. Do not confuse a missing binary with an empty alignment result.
- `threads` is passed to both database creation and alignment; reduce it while diagnosing resource pressure.

**The CLI treats a reference as a query or the result columns are reversed**

- The CLI grammar is `gget diamond QUERY [QUERY ...] -ref REFERENCE [REFERENCE ...]`. Put the query positional arguments first and use the required `-ref` option. An unoptioned sequence before `-ref` is another query by design.
- Prefer Python named arguments: `gget.diamond(query=query_fasta, reference=reference_fasta)`. Interpret `query_accession` as the searched input and `subject_accession` as the target/reference match.
- Do not “fix” a reversed-looking result by swapping biological labels after the run; rerun with explicit arguments and compare the accessions/lengths.

**Database creation or reuse is confusing**

- `diamond_db` is a basename passed to `makedb`; DIAMOND writes its database artifact (normally with `.dmnd`). If omitted without `out`, the artifact is temporary and deleted. If `out` is set and `diamond_db` is omitted, the basename is placed in that folder. An explicit `diamond_db` is intended to preserve the created database.
- The wrapper does not implement a true “reuse existing database” mode: it runs `makedb` on each call. Do not assume a preexisting basename skips creation.
- In the inspected implementation, `makedb` receives `db_path`, but the later alignment command passes `reference_file` to `--db`. If alignment reports an invalid database even though `makedb` succeeded, this source-level path mismatch is the first wrapper behavior to record. Verify the installed gget version and DIAMOND stderr before deleting files or manually renaming a `.dmnd`.
- Keep query/reference FASTA files separate from database artifacts. A reference FASTA is input to `makedb`; it is not itself the `.dmnd` database.

## ELM setup and data problems

**ELM says database files are missing**

- Run `gget setup elm` or `gget.setup("elm")` once with network access, `curl`, and write permission to gget's data location. Setup downloads four files and checks for known server-error text.
- A custom `setup(..., out="raw-elm")` directory is for a separate raw copy. `gget.elm` checks its default installed data directory; it will not discover the custom copy automatically.
- Do not distribute or use the downloaded ELM data commercially unless the applicable ELM license permits it.

**ELM returns no orthologs or regex matches**

- Empty `ortholog_df`/`regex_df` is valid. Check the input alphabet, accession spelling, database update date, and DIAMOND binary first.
- For UniProt input, set `uniprot=True` exactly. If the accession is not in local ELM instances, gget may fetch its sequence from UniProt; this requires a functioning network and exact accession matching.
- `expand=True` only changes descriptive regex output; it does not make a sequence more likely to match. Adjust DIAMOND sensitivity only when the biological objective supports the extra compute.
- The ELM workflow uses a local DIAMOND reference, so all DIAMOND binary/database lifecycle diagnostics above also apply.

## PDB retrieval and format fallback

**PDB resource is invalid or identifier is missing**

- Use one of the documented resource names exactly. `assembly` requires an assembly identifier; entity resources require an entity ID; `*_instance` resources require a chain ID.
- If the server returns no record, verify the PDB ID and identifier separately. The wrapper logs a resource-specific error and returns `None`.

**A `pdb` request returns mmCIF or saves `.cif`**

- This is intentional: gget tries legacy PDB downloads from available endpoints and falls back to RCSB PDBx/mmCIF when legacy PDB is unavailable, especially for large structures.
- Request `resource="mmcif"` explicitly to silence the fallback warning and make the expected format clear. Check the returned text prefix and the actual saved extension before handing it to downstream software.
- If a downstream parser only accepts legacy PDB, choose a known small legacy entry or use a parser that supports mmCIF; do not rename `.cif` to `.pdb`.

## AlphaFold prerequisites, memory, and network

**Import/setup failure**

- gget checks for `simtk.openmm`, an importable AlphaFold package, `pdbfixer`, model parameter files, and the bundled Jackhmmer executable. `relax=True` adds an OpenMM requirement.
- On Windows, gget documents setup/prediction as unsupported. The setup path installs large third-party components and downloads model parameters; run it only in an isolated, compatible environment with explicit approval.
- `plot=True` imports `py3Dmol`, IPython widgets, matplotlib, and related plotting support. For a headless or minimal environment, use `plot=False` and install only what the selected runtime requires.

**Out-of-memory, disk exhaustion, or a stuck MSA search**

- Check per-chain and total lengths before running: minimum 16, maximum 3,400 per sequence, 2,500 monomer maximum, 3,400 total. The implementation warns above 3,000 because runtime and accuracy are not fully validated.
- MSA searches stream several large remote databases and can use about 2 GB of temporary Jackhmmer disk space. Set `jackhmmer_savedir` to a writable filesystem with enough capacity; check free space and cleanup after an interrupted run.
- Multiple chains invoke multimer processing and can be substantially slower; duplicate chains may share MSA work, but distinct chains add searches. Lower `multimer_recycles` while diagnosing and avoid launching multiple predictions concurrently.
- A failed network fetch for the MSA database is not repaired by increasing model recycles. Check DNS/proxy/firewall and storage access, then retry once the external service is available.

**Prediction completed but files are absent**

- Set an explicit writable `out` directory and check `selected_prediction.pdb` plus `predicted_aligned_error.json`. With `out=None`, work is placed in the temporary Jackhmmer directory and cleanup removes temporary FASTA files.
- `relax=False` intentionally skips AMBER relaxation; this is not a missing prediction. A plot is optional and can fail independently of the saved PDB/PAE files.
- Treat the output as theoretical modeling with pLDDT/PAE confidence annotations, not as an experimental structure or a substitute for a current maintained prediction service.

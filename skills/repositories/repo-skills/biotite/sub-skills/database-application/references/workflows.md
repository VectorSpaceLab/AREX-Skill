# Database and Application Workflows

These recipes describe how to plan and implement Biotite database and wrapper tasks. Treat network services and local external binaries as opt-in side effects: if a task only asks for a plan, code sketch, or diagnosis, do not contact services or run analyses.

## Plan an RCSB fetch and parse handoff

1. Decide whether the user already has a PDB ID or needs an RCSB search.
2. For simple text search use `rcsb.BasicQuery(term)`; for metadata constraints use `rcsb.FieldQuery(field, operator=value)`; combine with `&`/`|` and negate field queries with `~`.
3. Use `rcsb.count(query, ...)` before broad downloads when only cardinality is needed.
4. Use `rcsb.search(query, return_type="entry", content_types=("experimental",))` for experimental entries; include `content_types=("computational",)` when AlphaFold/ModelArchive IDs are acceptable.
5. Fetch with `rcsb.fetch(ids, format, target_path, overwrite=False)`, preferring `"bcif"` or `"cif"` for modern structure workflows and `"fasta"` for entry sequences.
6. Hand downloaded or file-like content to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md) for `CIFFile`, `BinaryCIFFile`, `PDBFile`, or FASTA parsing.
7. Route in-memory structure measurements to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md) and sequence work to [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md).

Use `target_path=None` only when the next parser accepts file-like objects and you know whether the content is text (`pdb`, `cif`, `fasta`) or binary (`bcif`). Use a real target directory when extension-based dispatch or caching matters.

## Search and fetch AlphaFold DB models

1. If RCSB search returned computational IDs, split IDs by prefix: `AF_` or `AF-...-F1` belongs to AlphaFold DB; `MA_` identifies ModelArchive entries, which Biotite's AFDB fetch helper does not support.
2. For direct AlphaFold DB work, use UniProt accessions or AlphaFold IDs with `afdb.fetch(ids, "cif"|"bcif"|"pdb"|"fasta", target_path=...)`.
3. Parse structure formats through [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md).
4. Preserve the model-vs-experimental distinction in downstream analysis notes, because predicted confidence and experimental resolution are not equivalent metadata.

## Plan an Entrez search/fetch workflow

1. Identify the Entrez database, e.g. `"protein"`, `"nuccore"`, or another NCBI E-utilities database name.
2. Build query terms with `entrez.SimpleQuery(term, field=None)`; combine with `&` for AND, `|` for OR, and `^` for NOT.
3. Keep fields service-valid, e.g. `"Organism"`, `"Gene Name"`, `"Sequence Length"`, `"Properties"`, `"Journal"`, `"Volume"`, and similar NCBI field names.
4. Call `entrez.search(query, db_name, number=N)` to obtain UIDs; the default result limit is small.
5. For separate files, call `entrez.fetch(uids, target_path, suffix, db_name, ret_type, ret_mode="text")`.
6. For multi-record FASTA/GenBank parsing, call `entrez.fetch_single_file(uids, file_name, db_name, ret_type)`.
7. Route FASTA, GenBank/GenPept, and annotation parsing to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md).

If a task will issue many Entrez requests, ask whether the user has an NCBI API key and set it with `entrez.set_api_key(key)` in the calling process; do not embed keys in scripts or skill content.

## Plan a UniProt query/fetch workflow

1. Build queries with `uniprot.SimpleQuery(field, term)`, for example `accession`, `reviewed`, `organism_name`, `keyword`, `gene`, or `xref` fields.
2. Combine UniProt queries with `&`, `|`, and `^`.
3. Call `uniprot.search(query, number=500)` to collect IDs.
4. Fetch records with `uniprot.fetch(ids, "fasta"|"gff"|"txt"|"xml"|"rdf"|"tab", target_path=...)`.
5. The fetch helper infers UniProtKB, UniRef, or UniParc from ID shape; do not prepend endpoint names manually.
6. Parse sequence/file content through [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md) before downstream analysis.

## Plan a PubChem compound workflow

1. Select a query class: `NameQuery`, `SmilesQuery`, `InchiQuery`, `InchiKeyQuery`, `FormulaQuery`, `SuperstructureQuery`, `SubstructureQuery`, `SimilarityQuery`, or `IdentityQuery`.
2. Use integer CIDs after search; Biotite intentionally rejects string CIDs in `pubchem.fetch()`.
3. For molecule files, fetch `"sdf"` by default or `"png"`/`"json"`/other formats when explicitly needed.
4. For structural formula coordinates, pass `as_structural_formula=True`; otherwise PubChem attempts 3D conformer records.
5. Use `fetch_property(cids, property_name)` for metadata filters such as charge, isotope counts, or names.
6. Respect `ThrottleStatus`: lower `throttle_threshold`, request fewer CIDs, or pause/skip when PubChem is busy.
7. Route fetched `sdf`/`mol` content to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md), and in-memory molecule analysis to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md).

PubChem query objects are not boolean-combinable in Biotite; combine results in Python after separate queries when necessary.

## Use BLASTWebApp safely

1. Confirm that a web BLAST service may be contacted; BLAST can take time and server usage rules matter.
2. Choose `program`: `"blastn"` for nucleotide-nucleotide, `"blastp"` for protein-protein, `"blastx"`, `"tblastn"`, or `"tblastx"` for translated searches.
3. Build the query as a Biotite `Sequence`, a raw sequence string, or a FASTA path.
4. Instantiate `blast.BlastWebApp(program, query, database="nr", obey_rules=True, mail=...)`.
5. While the app is in `CREATED` state, set options such as `set_entrez_query()`, `set_max_results()`, `set_max_expect_value()`, gap penalties, word size, or scoring settings.
6. Call `start()`, then `join(timeout=...)`; result getters are valid only after `JOINED`.
7. Use `get_alignments()` for `BlastAlignment` objects with score, E-value, query/hit intervals, hit ID, and hit definition.
8. Use hit IDs with Entrez fetch planning when complete hit sequences are needed.

Avoid setting `obey_rules=False` unless the user explicitly accepts responsibility for a private server or controlled test context.

## Run multiple sequence alignment wrappers

1. Use local Biotite alignment APIs in [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md) if no external MSA binary is available or allowed.
2. Check binary availability with `scripts/check_optional_applications.py` before choosing a wrapper.
3. Prepare at least two compatible Biotite `Sequence` objects; all inputs need compatible alphabets.
4. Choose wrapper:
   - `ClustalOmegaApp` for common nucleotide/protein MSA with guide tree/distance options but no custom matrices.
   - `MafftApp` when custom nucleotide/protein matrices or custom sequence mapping are useful.
   - `MuscleApp` only for MUSCLE 3; it validates version and supports some custom matrix/gap options.
   - `Muscle5App` for MUSCLE 5+; it validates version and has different options, such as Super5 and thread/iteration settings.
5. Set wrapper-specific options before `start()`.
6. Call `start()` and `join(timeout=...)`, then read `get_alignment()`, `get_alignment_order()`, and available guide-tree/distance outputs.
7. Route alignment interpretation, scoring, profiles, and phylogeny to [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md).

Do not treat `muscle` on `PATH` as both MUSCLE 3 and MUSCLE 5: Biotite has separate wrappers with incompatible version expectations.

## Use DSSP through mkdssp

1. If an approximate Biotite-only secondary-structure annotation is acceptable, route to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md) instead of requiring `mkdssp`.
2. If DSSP is required, ensure `mkdssp` is available and allowed to run.
3. Prepare a protein-only `AtomArray`; `DsspApp` rejects non-amino-acid atoms.
4. Instantiate `dssp.DsspApp(atom_array, bin_path="mkdssp")` or call `DsspApp.annotate_sse(atom_array)`.
5. The wrapper writes temporary CIF/DSSP files and adapts CLI arguments for older/newer DSSP versions.
6. After `join()`, call `get_sse()` for residue-level DSSP symbols.
7. Route downstream residue filtering or structural summaries to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md).

## Plan SRA read retrieval

1. Confirm network/cache use and external `sra-tools` availability; SRA tasks can be large.
2. Use `FastqDumpApp` for reads plus quality scores or `FastaDumpApp` for FASTA output.
3. Decide `output_path_prefix`; if omitted, wrapper-managed temporary files are used and read into memory after completion.
4. Instantiate with explicit binary paths only when the user provides them; otherwise rely on `prefetch` and `fasterq-dump` on `PATH`.
5. Call `start()` and `join(timeout=...)`.
6. After `JOINED`, use `get_file_paths()`, `get_sequences()`, `get_fastq()`, or `get_sequences_and_scores()`.
7. Route FASTQ/FASTA parser details and quality-score handling to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md).

For broad sequencing workflows, first estimate data volume and prefer user-provided local files when available.

## Use Tantan repeat masking

1. Confirm that `tantan` is installed or run the diagnostic helper.
2. Prepare either one `NucleotideSequence`/`ProteinSequence` or a list of sequences all of the same type.
3. If a custom `SubstitutionMatrix` is provided, ensure it is symmetric and matches the common alphabet.
4. Instantiate `TantanApp(sequence_or_sequences, matrix=None)` or call `TantanApp.mask_repeats(...)`.
5. Use the boolean mask(s) to ignore repeat regions in sequence comparisons; route downstream sequence analysis to [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md).

## Use AutoDock Vina through VinaApp

1. Confirm `vina` availability and that docking is allowed; docking is an external compute workflow, not a harmless import check.
2. Prepare ligand and receptor `AtomArray` objects with associated `BondList`; partial charges via a `charge` annotation are recommended.
3. Choose search-box `center` and `size` arrays in coordinate units matching the structures.
4. Use `flexible` only for amino-acid side chains that can be separated safely; cyclic residues or missing `CA`/`CB` atoms can fail.
5. Instantiate `VinaApp(ligand, receptor, center, size, flexible=None)`.
6. Set seed, CPU count, exhaustiveness, model count, and energy range before `start()`.
7. After `join()`, use `get_energies()`, `get_ligand_coord()`, `get_ligand_models()`, and flexible-residue outputs.
8. Route structure preparation and docking-result analysis to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md); route PDBQT file-format details to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md).

## Use ViennaRNA wrappers

1. Confirm the needed binary: `RNAfold`, `RNAalifold`, or `RNAplot`.
2. For one RNA sequence, use `RNAfoldApp(NucleotideSequence(...), temperature=37)`.
3. For aligned RNA sequences, use `RNAalifoldApp(alignment, temperature=37)`.
4. Add constraints with `set_constraints()` while the app is in `CREATED` state; be careful with alignment gap positions for RNAalifold.
5. For 2D layout coordinates, use `RNAplotApp(dot_bracket=...)` or `RNAplotApp(base_pairs=..., length=...)`.
6. After `join()`, retrieve dot-bracket strings, free energy, covariance energy, base pairs, or coordinates as appropriate.
7. Route base-pair interpretation and sequence/alignment preparation to [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md) or [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md) depending on the data model.

## Safe diagnostic-first workflow

1. Run `python sub-skills/database-application/scripts/check_optional_applications.py` from the Biotite skill root.
2. Read the `status` for each executable:
   - `found` means the executable is on `PATH`.
   - `found-version-probe-failed` means the executable exists, but the safe version/help probe did not return cleanly.
   - `missing` means the wrapper will likely fail if the task depends on that binary.
3. Use wrapper import statuses to distinguish a missing Biotite installation from missing external tools.
4. Report missing dependencies as actionable prerequisites or choose a no-external alternative rather than failing mid-analysis.
5. Do not substitute this diagnostic for actual network authorization, service health, or full workflow validation.

# Database and Application Troubleshooting

Use this guide when Biotite database clients or `biotite.application` wrappers fail. Separate service/network problems, external-binary problems, Biotite object-preparation problems, and parser/analysis handoff problems before retrying.

## First triage

1. Identify whether the failing call contacts a network service, launches a local executable, or only imports/prepares Biotite objects.
2. If optional executables are involved, run `scripts/check_optional_applications.py` before constructing expensive inputs.
3. Confirm the wrapper's lifecycle: all option setters must run before `start()`, and result getters generally require `join()` to complete successfully.
4. Confirm IDs, fields, return types, file formats, and target-path decisions before retrying network calls.
5. Route parser errors to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md) and in-memory sequence/structure errors to sibling analysis sub-skills.

## Network and service failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `biotite.database.RequestError`, HTTP error text, malformed response, or empty/invalid downloaded file | Service unavailable, invalid ID/query, throttling, or transient malformed database response | Retry later only after validating IDs and query fields; prefer `count()` before broad search/fetch; cache to `target_path` to avoid repeated downloads. |
| RCSB `fetch()` fails for a PDB ID or format | Invalid ID, unsupported format, malformed service response, gzip with `"fasta"`, or computational-model mismatch | Validate ID; choose `"cif"`/`"bcif"`; do not use gzip for FASTA; use `afdb.fetch()` for AlphaFold IDs rather than `rcsb.fetch()` when appropriate. |
| RCSB search returns no IDs | Query too restrictive, wrong field/operator, default experimental-only content | Test `BasicQuery`; use `count()`; include `content_types=("computational",)` only when predicted models are acceptable. |
| RCSB grouping omits expected IDs | Grouping can omit entries that cannot be grouped | Use ungrouped search for complete ID lists or `return_groups=True` when groups are explicitly needed. |
| Entrez `SimpleQuery` raises `ValueError` | Unknown field or illegal term characters | Use valid NCBI fields; remove quotes/brackets/boolean keywords from raw terms; combine query objects with `&`, `|`, `^` instead. |
| Entrez fetch/search rate failures | NCBI request limit, missing API key, too many records | Ask whether the user has an NCBI API key and call `entrez.set_api_key()` in the current process; reduce `number`; batch requests; cache files. |
| Entrez returns unexpected format | Invalid `db_name`/`ret_type`/`ret_mode` combination | Verify the E-utilities database and retrieval type; for FASTA/GenBank workflows, use `ret_mode="text"` and route parsing to file IO. |
| UniProt query raises `ValueError` | Invalid UniProt field or illegal query term | Use valid field names such as `accession`, `reviewed`, `organism_name`, `gene`, `keyword`, or `xref`; avoid embedded boolean words in terms. |
| UniProt fetch hits wrong endpoint | ID shape implies UniProtKB, UniRef, or UniParc automatically | Provide the canonical ID and let Biotite infer the endpoint; do not prefix endpoint names manually. |
| PubChem calls are slow, blocked, or intermittently fail | Dynamic request throttling or busy PubChem service | Use fewer CIDs, keep `throttle_threshold` enabled or lower it, request `return_throttle_status=True`, and wait/skip if `ThrottleStatus` indicates high count/time/service load. |
| PubChem `fetch()` raises `TypeError` for CID | CID passed as string | Convert CIDs to integers before fetching. |
| AlphaFold DB fetch fails for `MA_...` ID | ModelArchive IDs are not supported by `afdb.fetch()` | Skip, route to another source if available, or report unsupported ModelArchive fetch. |

## BLAST web wrapper issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `RuleViolationError` or "Too frequent BLAST requests" | NCBI contact/request delay rules | Keep `obey_rules=True`; wait before polling/submitting; avoid parallel BLAST submissions unless using an approved private service. |
| `ValueError` for invalid BLAST program | Program not one of Biotite's accepted values | Use `blastn`, `blastp`, `blastx`, `tblastn`, or `tblastx`; `megablast` is not accepted by this wrapper. |
| `ValueError` for unsuitable symbol | Query sequence alphabet does not fit the program | Use nucleotide symbols for `blastn`/translated nucleotide modes and protein symbols for `blastp`/protein modes; clean ambiguous/invalid letters first. |
| "URI is too large" | Query sequence or request parameters too long for GET request | Use a shorter sequence/window or a different BLAST setup; do not repeatedly resubmit unchanged oversized requests. |
| Server status `UNKNOWN` | Invalid server-side input values or expired RID | Revalidate database, program, query, and options; submit a fresh app if needed. |
| Empty hit list | No homologs under current settings or too strict E-value/result limit | Relax `set_max_expect_value()`, increase `set_max_results()`, change database, or report no hits as a valid outcome. |

## External executable availability

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError`, command not found, or nonzero `SubprocessError` mentioning a binary | Required external program is missing or not on `PATH` | Run `scripts/check_optional_applications.py`; ask the user to install the tool or pass an explicit `bin_path`; use a local Biotite alternative when available. |
| Version probe fails in diagnostic | Binary exists but does not support the safe version/help option or exits nonzero | Treat executable as present but unverified; run the actual wrapper only with user approval and a timeout. |
| Wrapper starts but `join(timeout=...)` raises timeout | External analysis is slow, stuck, or waiting on remote resources | Catch timeout, report the app was cancelled, reduce inputs/options, or increase timeout with user approval. |
| `get_command()` unavailable | Called before `start()` or on a wrapper that is not `LocalApp` | Start the app first for `LocalApp` wrappers; use wrapper-specific diagnostics otherwise. |

The bundled diagnostic only checks imports and executable discovery/version-help probes. It does not run BLAST, SRA downloads, alignments, DSSP, docking, Tantan masking, or ViennaRNA analyses.

## Application lifecycle mistakes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AppStateError` from an option setter | Setter called after `start()` | Construct a new app, set every option while the state is `CREATED`, then start. |
| `AppStateError` from a result getter | Getter called before successful `join()` | Call `start()` then `join(timeout=...)`; only read results after `JOINED`. |
| `AppStateError` after failed evaluation | Wrapper moved to `CANCELLED` due to parse or subprocess failure | Inspect the underlying exception and stderr; create a fresh app after correcting inputs/dependencies. |
| Reusing one app for multiple runs fails | Biotite app objects are single-lifecycle objects | Create a new wrapper instance per run. |
| Output/temp file disappears | Wrapper-managed temp files are cleaned after `join()`/object destruction | Use explicit output paths or copy required outputs before cleanup if a workflow needs persisted files. |

## MSA wrapper failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: At least two sequences are required` | MSA wrapper received fewer than two sequences | Validate sequence collection before constructing the app. |
| `ValueError: Alphabets of the sequences are not equal` | Mixed incompatible sequence alphabets | Convert/clean sequences in [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md) before MSA. |
| Custom matrix rejected | Matrix is not symmetric or wrapper does not support custom matrices | Use `MafftApp` or `MuscleApp` for supported custom protein matrices; avoid custom matrices with Clustal Omega or MUSCLE 5. |
| `VersionError` from `MuscleApp` | `muscle` on `PATH` is not MUSCLE 3 | Use `Muscle5App` for MUSCLE 5+ or install/point to MUSCLE 3. |
| `VersionError` from `Muscle5App` | `muscle` on `PATH` is older than version 5 | Use `MuscleApp` for MUSCLE 3 or install/point to MUSCLE 5+. |
| Guide tree unavailable | Tool did not emit a guide tree or method requires specific mode | Check wrapper-specific guide-tree support; for Clustal Omega distance matrix output, call `full_matrix_calculation()` before start. |

## DSSP issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `BadStructureError: The input structure must contain only amino acids` | AtomArray contains hetero atoms, water, nucleic acids, ligands, or nonprotein residues | Filter protein atoms in [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md) before constructing `DsspApp`. |
| `mkdssp` missing or exits nonzero | DSSP not installed, wrong binary name, incompatible input, or CLI/version mismatch | Check executable availability; pass explicit `bin_path`; ensure a protein-only AtomArray; use Biotite local secondary-structure tools if DSSP is optional. |
| SSE length unexpected | Input residues changed by filtering, missing residues, or DSSP skipped records | Compare residue starts before/after filtering and document missing residues. |

## SRA issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `prefetch` or `fasterq-dump` missing | `sra-tools` is not installed or not on `PATH` | Install `sra-tools` or pass explicit binary paths; do not run the wrapper when only a diagnostic is requested. |
| SRA workflow is too slow/large | Run accession has large reads or slow remote/cache access | Ask the user for a smaller accession, local FASTQ files, or an explicit output/cache plan. |
| Unexpected read-file names | Single-read vs paired/multi-read output suffixes differ | Use `get_file_paths()` after `join()` instead of guessing suffixes. |
| Quality scores wrong | FASTQ offset mismatch | Set `offset` explicitly (`"Sanger"`, `"Solexa"`, `"Illumina-1.3"`, `"Illumina-1.5"`, `"Illumina-1.8"`) and route FASTQ details to file IO. |

## Tantan, Vina, and ViennaRNA issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Tantan rejects sequence list | Mixed nucleotide/protein sequences or invalid sequence type | Split by type or convert sequences before masking. |
| Tantan custom matrix rejected | Matrix not symmetric or alphabet incompatible | Use a symmetric matrix whose alphabet extends the common sequence alphabet. |
| Vina rejects ligand/receptor | Missing `BondList` or unsuitable flexible residues | Build/read structures with bonds; avoid flexible glycine/cyclic side-chain cases that cannot be separated; route preparation to structure/file IO sub-skills. |
| Vina coordinates contain `NaN` | Vina removed nonpolar hydrogens or flexible residues omitted atoms | Treat `NaN` as expected missing output coordinates and keep original atom mapping. |
| RNAfold/RNAalifold no pairs or odd constraints | Constraint positions conflict or RNAalifold constraints point to gaps | Rebuild constraints with sequence/alignment positions checked; for RNAalifold avoid constraints on consensus gap positions. |
| RNAplot cleanup/output problems | `RNAplot` writes an `rna.ss` file in the execution directory | Run in a controlled working directory if needed and let the wrapper clean up after `join()`. |

## Output path and file-like pitfalls

- Many fetch helpers return a single object for a single ID and a list for iterables. Normalize with `isinstance(ids, str)` or wrap single results when writing generic code.
- `target_path=None` means a file-like object, not a filesystem path. Parser choice must respect text vs binary content.
- `overwrite=False` can silently reuse cached files. Set `overwrite=True` only when refreshing stale downloads is intentional.
- `gzip=True` changes RCSB filenames and is unsupported for RCSB FASTA.
- Fetch helpers may create target directories. Keep paths under user-approved working directories and avoid source-repo fixture dependencies in generated workflows.

## When to skip rather than retry

Skip and explain clearly when:

- The user did not authorize network or external-binary execution.
- A service is unavailable or throttled and a retry would be wasteful.
- Required executables are missing and no Biotite-only fallback exists.
- The task can be completed as a plan or code recipe without live service calls.
- A native Biotite parser/analysis sibling sub-skill owns the next step and remote data is already available locally.

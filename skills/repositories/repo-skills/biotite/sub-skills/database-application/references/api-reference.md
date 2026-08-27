# Database and Application API Reference

Use this reference to choose the right Biotite database client or external-application wrapper. Network services and external binaries are optional operational surfaces; check permissions and availability before running them.

## Database clients

| Task | API | Main inputs | Returns and handoff |
| --- | --- | --- | --- |
| Fetch RCSB PDB files | `biotite.database.rcsb.fetch(pdb_ids, format, target_path=None, overwrite=False, verbose=False, gzip=False)` | PDB IDs or iterables; formats `"pdb"`, `"pdbx"`, `"cif"`, `"mmcif"`, `"bcif"`, `"fasta"` | Path(s) if `target_path` is set; `StringIO` or `BytesIO` otherwise. Parse local/fetched structures in [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md). |
| Search RCSB PDB | `rcsb.search(query, return_type="entry", range=None, sort_by=None, group_by=None, return_groups=False, content_types=("experimental",))`; `rcsb.count(...)` | `BasicQuery`, `FieldQuery`, `SequenceQuery`, `StructureQuery`, `MotifQuery`; optional `Sorting`/`Grouping` | Entry IDs, return-type IDs, grouped IDs, or counts. Include `content_types=("computational",)` for computational-model searches. |
| Fetch AlphaFold DB models | `biotite.database.afdb.fetch(ids, format, target_path=None, overwrite=False, verbose=False)` | UniProt IDs, AlphaFold IDs such as `AF-P12345-F1`, or RCSB computational IDs such as `AF_AFP12345F1`; formats match RCSB except no gzip option | Path(s) or file-like objects. Parse `cif`/`bcif` as structure files in [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md). |
| Fetch Entrez records | `biotite.database.entrez.fetch(uids, target_path, suffix, db_name, ret_type, ret_mode="text", overwrite=False, verbose=False)` | UID(s), database name such as `"protein"`/`"nuccore"`, ret type such as `"fasta"`/`"gb"` | Separate path(s) or file-like objects. Parse FASTA/GenBank in [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md). |
| Fetch Entrez multi-record file | `entrez.fetch_single_file(uids, file_name, db_name, ret_type, ret_mode="text", overwrite=False)` | Iterable UIDs and target file name or `None` | Single path or `StringIO`; useful for one FASTA/GenBank parser pass. |
| Search Entrez | `entrez.search(query, db_name, number=20)` | `SimpleQuery(term, field=None)` combined with `&`, `|`, `^`; optional `entrez.set_api_key(key)` | UID list. Fields are service-defined; invalid field names are rejected client-side. |
| Fetch UniProt | `biotite.database.uniprot.fetch(ids, format, target_path=None, overwrite=False, verbose=False)` | UniProtKB, UniRef, or UniParc IDs; formats `"fasta"`, `"gff"`, `"txt"`, `"xml"`, `"rdf"`, `"tab"` | Path(s) or `StringIO`; database endpoint is inferred from ID shape. |
| Search UniProt | `uniprot.search(query, number=500)` | `SimpleQuery(field, term)` combined with `&`, `|`, `^` | UniProt ID list. Field names follow UniProt query fields and are validated by Biotite. |
| Fetch PubChem structures | `biotite.database.pubchem.fetch(cids, format="sdf", target_path=None, as_structural_formula=False, overwrite=False, verbose=False, throttle_threshold=0.5, return_throttle_status=False)` | Integer CID(s); formats `"sdf"`, `"asnt"`, `"asnb"`, `"xml"`, `"json"`, `"jsonp"`, `"png"` | Path(s) or file-like objects, optionally plus `ThrottleStatus`. Parse SDF/MOL in [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md). |
| Fetch PubChem properties | `pubchem.fetch_property(cids, name, throttle_threshold=0.5, return_throttle_status=False)` | Integer CID(s) and PubChem property name | String(s), optionally plus `ThrottleStatus`. |
| Search PubChem | `pubchem.search(query, throttle_threshold=0.5, return_throttle_status=False)` | `NameQuery`, `SmilesQuery`, `InchiQuery`, `InchiKeyQuery`, `FormulaQuery`, `SuperstructureQuery`, `SubstructureQuery`, `SimilarityQuery`, `IdentityQuery` | CID list, optionally plus `ThrottleStatus`. PubChem queries are not combined with boolean operators. |

## RCSB query helpers

| Helper | Use for | Notes |
| --- | --- | --- |
| `rcsb.BasicQuery(term)` | Simple text search over RCSB fields | Wraps the term as a phrase. |
| `rcsb.FieldQuery(field, ..., exact_match=..., contains_words=..., contains_phrase=..., greater=..., less=..., greater_or_equal=..., less_or_equal=..., equals=..., range=..., range_closed=..., is_in=...)` | Field-specific metadata filters | Only one operator keyword is allowed. Use `~query` to negate. |
| `rcsb.SequenceQuery(sequence, scope, min_identity=..., max_identity=...)` | Sequence similarity searches | `scope` is `"protein"`, `"dna"`, or `"rna"`. |
| `rcsb.StructureQuery(entry_id, chain=None, assembly=None, min_similarity=..., max_similarity=...)` | Structure similarity searches | Requires a reference entry and optional chain/assembly. |
| `rcsb.MotifQuery(motif, pattern_type, scope)` | Motif searches | Use return type `"polymer_entity"` when motif hits should be entity-level. |
| `rcsb.Sorting(field, descending=True)` | Ordered search results | Pass as `sort_by`. |
| `rcsb.DepositGrouping`, `IdentityGrouping`, `UniprotGrouping` | Redundancy grouping | Pass as `group_by`; `return_groups=True` returns group mappings. |

## Application lifecycle and base classes

| API | Use | State rule |
| --- | --- | --- |
| `biotite.application.Application` | Abstract lifecycle base | Starts in `CREATED`, then `RUNNING`, `FINISHED`, `JOINED`, or `CANCELLED`. |
| `app.start()` | Launch web/local application | Only valid in `CREATED`. Set wrapper options first. |
| `app.join(timeout=None)` | Wait, evaluate results, and clean up | Result getters usually require `JOINED`. Use a timeout for long local binaries. |
| `app.cancel()` | Stop a running/finished app and clean up | Leaves no accessible results. |
| `app.get_app_state()` | Inspect lifecycle state | For web apps, polling can contact the server. |
| `biotite.application.LocalApp` | Base for local command wrappers | Can expose `get_command()`, `get_stdout()`, `get_stderr()`, and exit-code errors after start/join. |
| `biotite.application.WebApp` | Base for web wrappers | Can raise `RuleViolationError` when server rules would be violated. |
| `AppStateError`, `TimeoutError`, `VersionError` | Common lifecycle/version exceptions | Treat these as configuration or call-order problems before retrying work. |

## External application wrappers

| Wrapper | Required external service/binary | Primary inputs | Important results/options |
| --- | --- | --- | --- |
| `biotite.application.blast.BlastWebApp(program, query, database="nr", app_url=..., obey_rules=True, mail=...)` | Reachable BLAST web service, usually NCBI | `program` in `"blastn"`, `"blastp"`, `"blastx"`, `"tblastn"`, `"tblastx"`; sequence, query string, or FASTA path | Set options in `CREATED`: `set_entrez_query()`, `set_max_results()`, `set_max_expect_value()`, `set_gap_penalty()`, `set_word_size()`, nucleotide/protein scoring options. After `join()`: `get_alignments()`, `get_xml_response()`. |
| `biotite.application.clustalo.ClustalOmegaApp(sequences, bin_path="clustalo", matrix=None)` | `clustalo` | At least two compatible `Sequence` objects | `align()`, `get_alignment()`, `get_alignment_order()`, `get_guide_tree()`, optional distance matrix/tree methods. Does not support custom matrices. |
| `biotite.application.mafft.MafftApp(sequences, bin_path="mafft", matrix=None)` | `mafft` | At least two compatible `Sequence` objects | Supports nucleotide/protein and custom matrices; after `join()` use `get_alignment()`, `get_alignment_order()`, `get_guide_tree()`. |
| `biotite.application.muscle.MuscleApp(sequences, bin_path="muscle", matrix=None)` | MUSCLE version 3 | At least two compatible `Sequence` objects | Validates major version 3; supports protein custom matrices; `set_gap_penalty()`; `get_guide_tree(iteration="kmer"|"identity")`; `align()`. |
| `biotite.application.muscle.Muscle5App(sequences, bin_path="muscle")` | MUSCLE version 5 or newer | At least two compatible `Sequence` objects | Validates major version >=5; `set_iterations()`, `set_thread_number()`, `use_super5()`, `align()`. No custom matrix support. |
| `biotite.application.dssp.DsspApp(atom_array, bin_path="mkdssp")` | `mkdssp` | Protein-only `AtomArray` | Adds required placeholder annotations internally; after `join()` use `get_sse()` or static `annotate_sse()`. Local structural analysis alternatives belong to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md). |
| `biotite.application.sra.FastqDumpApp(uid, output_path_prefix=None, prefetch_path="prefetch", fasterq_dump_path="fasterq-dump", offset="Sanger")` | `prefetch` and `fasterq-dump`; network/cache access | SRA UID | After `join()`: `get_file_paths()`, `get_fastq()`, `get_sequences()`, `get_sequences_and_scores()`. Static `fetch()` returns sequences. |
| `biotite.application.sra.FastaDumpApp(uid, output_path_prefix=None, prefetch_path="prefetch", fasterq_dump_path="fasterq-dump")` | `prefetch` and `fasterq-dump`; network/cache access | SRA UID | Runs `fasterq-dump --fasta`; after `join()` use `get_fasta()` or `get_sequences()`. |
| `biotite.application.tantan.TantanApp(sequence, matrix=None, bin_path="tantan")` | `tantan` | One or more nucleotide/protein sequences of one type | After `join()` use `get_mask()`; static `mask_repeats()` returns boolean repeat masks. |
| `biotite.application.autodock.VinaApp(ligand, receptor, center, size, flexible=None, bin_path="vina")` | `vina` | Ligand/receptor `AtomArray` objects with `BondList`; search box center/size | Set `seed`, `cpu`, `exhaustiveness`, max models, and energy range before `start()`. After `join()`: `get_energies()`, `get_ligand_models()`, `get_ligand_coord()`, flexible-residue outputs. |
| `biotite.application.viennarna.RNAfoldApp(sequence, temperature=37, bin_path="RNAfold")` | `RNAfold` | `NucleotideSequence` | Optional constraints before `start()`. After `join()`: `get_free_energy()`, `get_dot_bracket()`, `get_base_pairs()`. |
| `biotite.application.viennarna.RNAalifoldApp(alignment, temperature=37, bin_path="RNAalifold")` | `RNAalifold` | RNA `Alignment` | Optional constraints before `start()`. After `join()`: free/covariance energy, consensus string, dot-bracket, base pairs. |
| `biotite.application.viennarna.RNAplotApp(dot_bracket=None, base_pairs=None, length=None, layout_type=RNAplotApp.Layout.NAVIEW, bin_path="RNAplot")` | `RNAplot` | Dot-bracket or base-pair array plus length | After `join()` use `get_coordinates()`; static `compute_coordinates()` is a convenience wrapper. |

## Parser and analysis handoffs

- FASTA/FASTQ/GenBank/GFF/Clustal/PDB/PDBx/BinaryCIF/SDF parsing belongs to [../file-io-formats/SKILL.md](../../file-io-formats/SKILL.md).
- Sequence interpretation, local alignments, annotation slicing, phylogeny, and profile work belong to [../sequence-analysis/SKILL.md](../../sequence-analysis/SKILL.md).
- AtomArray filtering, structural measurements, contacts, secondary structure alternatives, and docking-result analysis belong to [../structure-analysis/SKILL.md](../../structure-analysis/SKILL.md).
- Optional PyMOL/RDKit/OpenMM conversions and visualization belong to [../interfaces-visualization/SKILL.md](../../interfaces-visualization/SKILL.md).

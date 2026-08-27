# Input Data API Reference

This reference distills the AlphaFold 2.3.2 parser, pipeline, multimer, template, and notebook input APIs relevant to validating data before expensive searches or inference.

## Parser APIs

| API | Signature | Safe use | Important behavior |
| --- | --- | --- | --- |
| `alphafold.data.parsers.parse_fasta` | `parse_fasta(fasta_string: str) -> Tuple[Sequence[str], Sequence[str]]` | Parse FASTA text into sequence strings and descriptions. | Skips blank lines, removes the leading `>` from descriptions, concatenates sequence lines, and does not validate residues, lengths, duplicate descriptions, or missing biological metadata. |
| `alphafold.data.parsers.parse_stockholm` | `parse_stockholm(stockholm_string: str) -> Msa` | Parse JackHMMER/HMMER Stockholm alignment text. | First sequence is treated as the query; columns where the query has gaps are removed; deletion counts are measured relative to query residues. |
| `alphafold.data.parsers.parse_a3m` | `parse_a3m(a3m_string: str) -> Msa` | Parse HHblits/HHsearch A3M text. | Lowercase residues represent insertions and contribute to the deletion matrix; aligned sequences returned by `Msa.sequences` have lowercase insertions removed. |
| `alphafold.data.parsers.convert_stockholm_to_a3m` | `convert_stockholm_to_a3m(stockholm_format: str, max_sequences: Optional[int] = None, remove_first_row_gaps: bool = True) -> str` | Convert Stockholm MSA text for tools expecting A3M. | Preserves sequence order up to `max_sequences`; can drop columns where the first/query row has gaps; emits FASTA-like A3M with descriptions when Stockholm `#=GS ... DE` rows exist. |
| `alphafold.data.parsers.truncate_stockholm_msa` | `truncate_stockholm_msa(stockholm_msa_path: str, max_sequences: int) -> str` | Safely trim very large Stockholm files before parsing. | Reads sequence names first, then keeps only alignment, description, reference annotation, start, blank, and end lines for selected names. |
| `alphafold.data.parsers.deduplicate_stockholm_msa` | `deduplicate_stockholm_msa(stockholm_msa: str) -> str` | Remove duplicate Stockholm rows before template search. | Duplicates are detected after ignoring query-relative insertions. |
| `alphafold.data.parsers.remove_empty_columns_from_stockholm_msa` | `remove_empty_columns_from_stockholm_msa(stockholm_msa: str) -> str` | Clean Stockholm columns before template search. | Removes columns where every alignment row has a dash. |

`Msa` objects expose `sequences`, `deletion_matrix`, `descriptions`, `len(msa)`, and `truncate(max_seqs)`. The constructor raises when the three fields have different lengths.

## Feature-Building APIs

| API | Signature | Notes |
| --- | --- | --- |
| `make_sequence_features` | `make_sequence_features(sequence: str, description: str, num_res: int) -> MutableMapping[str, np.ndarray]` | Builds `aatype`, `between_segment_residues`, `domain_name`, `residue_index`, `seq_length`, and `sequence`. Unknown residues are mapped through the `X` path, so strict validation should happen before calling it. |
| `make_msa_features` | `make_msa_features(msas: Sequence[Msa]) -> MutableMapping[str, np.ndarray]` | Requires at least one non-empty MSA. Deduplicates identical sequences across MSAs, converts residues through the HHblits alphabet, and emits `msa`, `deletion_matrix_int`, `num_alignments`, and `msa_species_identifiers`. |
| `run_msa_tool` | `run_msa_tool(msa_runner, input_fasta_path: str, msa_out_path: str, msa_format: str, use_precomputed_msas: bool, max_sto_sequences: Optional[int] = None) -> Mapping[str, Any]` | Calls the runner unless `use_precomputed_msas` is true and the expected output exists. For Stockholm plus `max_sto_sequences`, precomputed files are truncated before returning. |

## Monomer Data Pipeline

`alphafold.data.pipeline.DataPipeline.__init__` requires keyword-only paths and objects:

- `jackhmmer_binary_path`, `hhblits_binary_path`
- `uniref90_database_path`, `mgnify_database_path`
- `bfd_database_path`, `uniref30_database_path`, `small_bfd_database_path`
- `template_searcher`, `template_featurizer`
- `use_small_bfd`, `mgnify_max_hits=501`, `uniref_max_hits=10000`, `use_precomputed_msas=False`, `msa_tools_n_cpu=8`

`DataPipeline.process(input_fasta_path: str, msa_output_dir: str)` reads a FASTA file and raises if it contains more than one sequence. It writes or reads MSA/template search intermediates in `msa_output_dir`:

- `uniref90_hits.sto` from JackHMMER against UniRef90.
- `mgnify_hits.sto` from JackHMMER against MGnify.
- `pdb_hits.<format>` from HHsearch or HMMsearch template search.
- `small_bfd_hits.sto` when `use_small_bfd=True`, otherwise `bfd_uniref_hits.a3m` from HHblits against BFD and UniRef30.

The monomer pipeline is not a lightweight validator: construction and processing assume external binaries and database files are present.

## Multimer Data Pipeline

`alphafold.data.pipeline_multimer.DataPipeline.__init__(monomer_data_pipeline, *, jackhmmer_binary_path, uniprot_database_path, max_uniprot_hits=50000, use_precomputed_msas=False, jackhmmer_n_cpu=8)` wraps a monomer pipeline and adds UniProt all-sequence MSA search for pairing.

`DataPipeline.process(input_fasta_path: str, msa_output_dir: str)`:

- Parses all FASTA records and maps them to PDB chain IDs in order: `A-Z`, `a-z`, `0-9`.
- Rejects more than 62 chains, the PDB-format maximum.
- Writes `chain_id_map.json` in the MSA output directory.
- Runs monomer processing once per unique sequence and deep-copies features for repeated identical chains.
- Treats one unique sequence as monomer/homomer and skips all-sequence UniProt pairing features.
- For heteromers, adds `uniprot_hits.sto` all-sequence MSA features used by MSA pairing.
- Adds assembly features so repeated chains share an `entity_id` but receive distinct `sym_id` and `asym_id` values; output chain keys look like `A_1`, `A_2`, or `B_1` after grouping by unique sequence.

## Template APIs

Template search has two layers: a searcher that produces hits and a featurizer that converts valid hits plus mmCIF files into template feature arrays.

| Use case | Searcher | Featurizer | Input expectations |
| --- | --- | --- | --- |
| Monomer/PDB70 | HHsearch | `HhsearchHitFeaturizer` | Search typically consumes A3M; template hit names start with `PDBID_chain`. |
| Multimer/PDB SeqRes | HMMsearch | `HmmsearchHitFeaturizer` | Search uses HMMER-style inputs and PDB SeqRes for multimer templates. |

`TemplateHitFeaturizer.__init__(mmcif_dir, max_template_date, max_hits, kalign_binary_path, release_dates_path, obsolete_pdbs_path, strict_error_check=False)` requires:

- A template mmCIF directory containing `.cif` files.
- `max_template_date` in `YYYY-MM-DD` format.
- A Kalign binary path for realignment when template sequences differ.
- Optional release-date and obsolete-PDB mapping files.

Template prefiltering rejects hits that are after `max_template_date`, align to too little of the query, are near-duplicate exact subsequences of the query, or are shorter than 10 residues. Template parsing can fail when mmCIF files have no chains, missing atom data, all-zero atom masks, unexpected multiple chains, or query/template realignment issues.

## External Binary Assumptions

The input pipeline assumes external tools are installed and executable, but this sub-skill should not run them by default:

- JackHMMER for UniRef90, MGnify, small BFD, UniProt, and all-sequence multimer MSA searches.
- HHblits for full-database BFD plus UniRef30 A3M searches.
- HHsearch for monomer template hits against PDB70.
- HMMsearch and HMMbuild for multimer template hits against PDB SeqRes.
- Kalign for template/query realignment during template featurization.

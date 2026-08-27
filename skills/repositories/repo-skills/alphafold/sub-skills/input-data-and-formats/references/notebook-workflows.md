# Notebook Workflows

AlphaFold notebook helpers are useful for lightweight validation patterns, but notebook execution itself may assume network access, plotting, model setup, and long-running searches. Distill the helper behavior instead of running the notebook during routine skill use.

## Sequence Cleaning and Validation

`clean_and_validate_single_sequence(input_sequence, min_length, max_length)` performs notebook-style sequence validation:

1. Removes spaces, tabs, and newlines.
2. Uppercases the sequence.
3. Requires every character to be one of the 20 standard amino acids.
4. Raises if the cleaned sequence is shorter than `min_length`.
5. Raises if the cleaned sequence is longer than `max_length`.
6. Returns the cleaned sequence.

`clean_and_validate_input_sequences(input_sequences, min_sequence_length, max_sequence_length)` applies that logic to a sequence list, skips blank entries, and raises when no non-blank sequence remains.

The bundled [`../scripts/validate_fasta.py`](../scripts/validate_fasta.py) adapts this behavior for FASTA files without importing notebook plotting dependencies.

## Chunked MSA Merging

`merge_chunked_msa(results, max_hits=None)` combines multiple JackHMMER chunks:

- Each chunk is expected to contain Stockholm text under `sto` and table output under `tbl`.
- The query hit is kept from the first chunk only.
- Non-query hits are sorted by E-value parsed from table output.
- The result is an `Msa` object and can be truncated with `max_hits`.

Use this as a reasoning aid when a notebook workflow split a database into chunks. Do not infer that chunked MSA outputs are interchangeable with full pipeline outputs unless the sequence and database partitioning match.

## MSA Info Display

`show_msa_info(single_chain_msas, sequence_index)` deduplicates sequences while preserving order, prints the number of unique sequences, and plots per-residue non-gap counts. It is visualization-only and should not be used as an automated pass/fail validator.

## Placeholder Templates

`empty_placeholder_template_features(num_templates, num_res)` returns correctly shaped zero arrays for template feature names:

- `template_aatype`
- `template_all_atom_masks`
- `template_all_atom_positions`
- `template_domain_names`
- `template_sequence`
- `template_sum_probs`

This is useful when adapting notebook logic that intentionally runs without real templates. Full data-pipeline template featurization still requires template search hits, mmCIF files, a max template date, and Kalign.

## Cell Execution Order

`check_cell_execution_order(cells_ran, cell_number)` raises if earlier notebook cells were skipped. If a user reports notebook errors that look unrelated to data formats, first check whether cells ran in order and whether the runtime restarted.

## Notebook Validation Pitfalls

- Notebook validation rejects `X` even though some lower-level AlphaFold feature code can map unknown residues to `X`; prefer strict notebook validation for user-provided raw inputs.
- Notebook min/max length limits are caller supplied and may differ from full AlphaFold hardware limits.
- Plotting and MSA visualization helpers may import GUI/plotting packages and should not be used in headless validation scripts.
- Notebook workflows may use reduced examples or placeholder templates; do not generalize those shortcuts to production runs without checking data-pipeline requirements.

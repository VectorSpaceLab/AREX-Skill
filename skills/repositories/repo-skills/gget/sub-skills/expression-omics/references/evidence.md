# Evidence map

This sub-skill was drafted from the visible repository evidence supplied for
this generation task. Names below are source artifact names, not required
runtime files; the operating guidance above is self-contained and does not
ask a future agent to open them.

## Implementation evidence

- `gget_archs4.py`: validates `which` and `species`, resolves Ensembl IDs,
  uppercases symbols, calls correlation/tissue endpoints, drops the self-hit
  and optional `color` column, sorts tissue rows, and implements DataFrame/
  JSON/save behavior.
- `gget_bgee.py`: enforces one ID for orthologs, performs Bgee species
  lookups, rejects mixed-species expression lists, flattens ortholog and
  expression response fields, converts expression scores to float, and
  implements DataFrame/JSON behavior.
- `gget_cellxgene.py`: defines the five-species allowlist, listifies scalar
  filters, constructs observation predicates, chooses `feature_name` versus
  `feature_id`, separates AnnData and metadata-only branches, handles the
  optional import, and writes h5ad/CSV outputs.
- `gget_8cube.py`: validates list/tuple gene inputs, strips whitespace while
  preserving Ensembl versions, sends repeated query parameters, parses CSV,
  returns DataFrame/JSON, and names default save files.
- The live API signature report supplies the current public signatures and
  return annotations for `archs4`, `bgee`, `cellxgene`, `specificity`,
  `psi_block`, and `gene_expression`.

## Documentation evidence

- `archs4.md`: symbol/Ensembl mode, human/mouse tissue selection, correlation
  versus atlas semantics, CLI/Python output conventions, and legacy endpoint
  caveat.
- `bgee.md`: Ensembl examples, ortholog versus expression mode, multi-ID
  expression examples, broader Bgee species note, and output conventions.
- `cellxgene.md`: supported species, case-sensitive symbols, Census versions,
  optional setup, metadata filters, `meta_only`, output paths, and examples.
- `8cube.md`: specificity, ψ-block, and expression commands; required
  partition arguments; accepted symbol/Ensembl forms; JSON/DataFrame/CSV
  conventions; and documented partition examples.

## Native test and fixture evidence

- `test_archs4.py` and its fixture cover default correlation, JSON plus
  Ensembl input, tissue mode, mouse selection, missing IDs, and invalid
  `which`/species. A network-free regression confirms a tissue CSV without
  `color` is accepted and sorted by median.
- `test_bgee.py` and its fixture cover orthologs, single and multi-ID
  expression, invalid IDs, and invalid type.
- `test_cellxgene.py` and its fixture cover AnnData, metadata-only output,
  non-human-primate Census LTS selection, the five-species allowlist, and
  network-free invalid-species validation. Integration tests skip when the
  optional package is unavailable.
- `test_8cube.py` and its fixture cover JSON responses for specificity,
  ψ-block with `Across_tissues`/`Sex:Strain`, and expression with
  `Kidney`/`Sex:Celltype`; implementation validation supplies the scalar-input
  `ValueError` contract.

## Deliberate evidence limits

- No network-heavy query, credentialed service, or large Census read was run
  while drafting. Remote response contents and schemas remain versioned
  uncertainties.
- No source script was copied or adapted: these modules are direct network
  wrappers, and a local script would create unsafe duplicate behavior.
- The exact complete 8cube partition enumeration is not present in the visible
  evidence; examples are labeled as examples and callers are told to verify
  current service names.
- Bgee's public response shape and CELLxGENE Census availability can change;
  recovery guidance requires preserving errors/raw output before schema
  adaptation.

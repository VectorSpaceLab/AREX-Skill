# Input Data Troubleshooting

## FASTA and Sequence Errors

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Non-amino-acid letters reported | Input contains `B`, `J`, `O`, `U`, `X`, `Z`, nucleotide letters, punctuation, gaps, or hidden characters. | Clean whitespace, uppercase, and validate against `ACDEFGHIKLMNPQRSTVWY`; ask the user how ambiguous residues should be resolved rather than silently mapping them. |
| No input sequence | FASTA file is empty, contains only comments/headers without sequence, or notebook input fields are blank. | Require at least one non-empty sequence record. |
| Too short or too long | Notebook/helper min/max limits or practical memory limits are exceeded. | Recheck the requested min/max constraints; for long proteins, explain that full AlphaFold resource limits depend on GPU/system memory. |
| Monomer pipeline rejects FASTA | More than one FASTA record was provided to the monomer data pipeline. | Use one record for monomer mode or route to multimer command planning. |
| Duplicate FASTA descriptions | Multiple records share a header, making chain debugging and output interpretation ambiguous. | Rename descriptions; the bundled validator reports duplicates as warnings by default. |

## Multimer Chain Errors

| Symptom | Likely cause | Action |
| --- | --- | --- |
| More than 62 chains | PDB-format chain ID limit is exceeded. | Split the biological question or use downstream formats/tools that can represent larger assemblies; AlphaFold PDB output and multimer chain mapping cannot handle it directly. |
| Homomer/heteromer confusion | Repeated chains were represented as separate FASTA records but interpreted as separate proteins, or unique chains were collapsed mentally. | Count both total chains and unique cleaned sequences. Repeated identical records are homomer copies; multiple unique sequences are heteromer entities. |
| Pairing features missing | Target is monomer/homomer or UniProt all-sequence search was not available. | For heteromers, ensure multimer mode has UniProt database and JackHMMER available; for homomers, absence of pairing features is expected. |
| MSA reuse gives suspicious results | Sequence, chain order, target mode, database snapshot, or output directory changed. | Disable MSA reuse or regenerate MSAs; AlphaFold does not validate reuse compatibility. |

## MSA and Format Errors

| Symptom | Likely cause | Action |
| --- | --- | --- |
| A3M deletion matrix length mismatch | Lowercase insertions or query gaps were misunderstood. | Remember lowercase A3M residues are insertions and are removed from aligned sequences while contributing deletion counts. |
| Stockholm conversion changes columns | Query-gap columns are removed by default during Stockholm-to-A3M conversion. | Use `remove_first_row_gaps=False` only when a downstream consumer explicitly expects original query-gap columns. |
| Empty MSA error | `make_msa_features` received no MSA objects or an MSA with zero sequences. | Confirm search output exists and parse it before feature construction; include the query row. |
| Unknown residue in MSA feature construction | Alignment contains symbols outside the HHblits amino-acid alphabet. | Inspect and sanitize the alignment source; do not proceed with feature creation until residues are understood. |

## External Binary and Database Errors

| Symptom | Likely cause | Action |
| --- | --- | --- |
| JackHMMER/HHblits/HHsearch/HMMsearch not found | Binary path is missing, not executable, or not installed in the runtime. | Route setup to `docker-and-data-setup` or ask the user to provide valid binary paths; do not fake MSA/template outputs. |
| HMMbuild missing in multimer template search | Multimer HMMsearch path requires HMMER tooling beyond JackHMMER. | Verify HMMER installation and binary flags before running multimer template search. |
| Kalign failure during templates | Kalign path is missing or template/query realignment failed. | Verify Kalign availability and inspect template sequence compatibility. |
| Database path error | Required UniRef90, MGnify, BFD/UniRef30/small BFD, UniProt, PDB70, PDB SeqRes, or mmCIF paths are absent. | Route database layout and downloads to `docker-and-data-setup`; keep this sub-skill focused on format/API reasoning. |

## Template Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `max_template_date` rejected | Date is missing or not `YYYY-MM-DD`. | Provide an ISO date and explain its role in avoiding templates released after a benchmark cutoff. |
| Template skipped after cutoff | Hit release date is later than `max_template_date`. | Use an appropriate cutoff for historical benchmarks; do not override unless scientifically justified. |
| Duplicate or near-query template rejected | Template is an exact subsequence covering most of the query. | Treat as leakage/duplicate protection rather than a parser bug. |
| Template too short or low alignment ratio | Hit has fewer than 10 residues or aligns to too little of the query. | Prefer better template hits or continue with fewer/no templates if supported by the workflow. |
| mmCIF parsing quirks | File has no chains, sequence mismatch, missing atoms, all-zero masks, or multiple ambiguous chains. | Inspect the specific mmCIF and obsolete-ID mapping; consider strict versus non-strict template error handling. |

## Quick Checks

- Run `python sub-skills/input-data-and-formats/scripts/validate_fasta.py target.fasta --mode auto` for sequence, chain-count, duplicate-description, and homomer/heteromer classification.
- For parser-only reasoning, use tiny in-memory FASTA, A3M, or Stockholm examples rather than launching searches.
- For full `DataPipeline.process`, assume expensive external tools and databases are required unless a user explicitly provides a safe local test fixture.

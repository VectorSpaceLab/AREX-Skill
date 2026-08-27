# Troubleshooting and boundaries

Use the module-specific references for full signatures: [Enrichr](enrichr.md),
[cBioPortal](cbio.md), [COSMIC](cosmic.md), [Open Targets](opentargets.md), and
[G2P](g2p.md). This page is the recovery decision tree.

## First triage

1. **Identify the failure class:** validation error, missing optional
   dependency, network/HTTP failure, empty upstream result, local file/cache
   failure, or permission/license/account boundary.
2. **Re-run a small known case with progress enabled.** Preserve the exact
   identifier, species, resource/library, filters, versions, and output path.
3. **Inspect type and shape.** A DataFrame with zero rows, a `None`, and a
   `False`/`True` plot return have different meanings; check the log and output
   artifact before concluding anything biological.
4. **Stop at permission or credential boundaries.** Do not bypass licensing,
   submit guessed passwords, or use portal-only overlays as if they were public
   API fields.

## Enrichr

| Symptom | Likely cause | Recovery |
|---|---|---|
| Shortcut rejected for fly/yeast/worm/fish | Shortcuts are human/mouse-only | Use an exact species library name from that species' current Enrichr catalog |
| No results or HTTP error for Ensembl IDs | `ensembl=True` was omitted, or an ID cannot resolve | Strip/check ID versions, validate with `gget.info`, then retry with `ensembl=True` |
| Background behaves like symbols | `ensembl_bkg=True` was omitted | Convert the background with the separate flag; retain the experimental universe |
| Background rejected | Non-human/mouse species | Use no background or a service-supported design; do not force the default list |
| KEGG image missing | Non-KEGG database, absent `pykegg`, or nonexistent rank | Use a resolved KEGG library, install the optional package, and check `rank` values |
| Top-N differs between runs | Upstream library/data changed | Save exact input, resolved library, retrieval date, and the returned first N rows |

Ensembl conversion uses gget's `info` lookup and removes version suffixes before
lookup. Unknown IDs are skipped. A `None`/empty conversion is an input failure,
not evidence that the genes have no enrichment.

## cBioPortal

| Symptom | Likely cause | Recovery |
|---|---|---|
| `cbio_search` returns `[]` immediately | `bravado` is not installed | Run `gget.setup("cbio")` or install the documented dependency, then retry |
| Search misses a mixed cohort | Mixed cancer types are intentionally excluded | Search/select a specific non-mixed cohort or use the cBioPortal UI |
| Study download returns `False` | Invalid ID, Git LFS/network failure, or malformed pointer | Inspect the study cache, remove only incomplete files, retry with confirmation |
| Plot fails while loading | Required `mutations.txt` or `clinical_sample.txt` is absent/malformed | Redownload a valid study; optional CNA/SV absence only limits those variations |
| `cna_nonbinary` assertion | Wrong stratification or filter | Use `stratification="sample"` and `filter=("study_id", selected_study)` |
| `Consequence` assertion | Consequence is sample-level | Use `stratification="sample"` |
| Empty heatmap | Gene not present, wrong merge namespace, or filter removed all rows | Try symbols with `merge_type="Symbol"`, remove the filter, inspect cache headers |
| Output not where expected | Filename is relative to `figure_dir` | Check `<figure_dir>/<figure_filename>` or the default `Heatmap_*.png` |
| Too many x-axis columns | Renderer caps/omits labels | Split studies, aggregate by tissue/cancer type, and record truncation |

cBio caches `mutations`, `clinical_sample`, and optional `cna`/`sv` files under
the caller's `data_dir`; do not confuse that cache with a validated analysis
snapshot. Keep study IDs and cache provenance with the PNG.

## COSMIC

| Symptom | Likely cause | Recovery |
|---|---|---|
| `FileNotFoundError` for query | No local TSV or wrong path | Supply the extracted TSV, or obtain the permitted archive first |
| No match | COSMIC query is exact, not substring | Use the exact gene, mutation, accession, sample, or COSMIC ID and the correct project |
| Wrong schema/no columns | Project inferred incorrectly | Inspect headers; pass `cosmic_project="cancer"`, `"census"`, etc. explicitly |
| Full download asks for account | Licensed database | Stop and obtain an account/permission; use `cancer_example` for a small public case |
| Authentication/HTTP failure | Invalid account, version, curl/network, or license issue | Do not retry guessed credentials; verify account and version through COSMIC |
| GRCh confusion | CMC is documented for GRCh37; archive assembly differs | Match `grch_version` and mutation coordinates to the analysis assembly |
| Huge or partial TSV | Multi-GB archive or interrupted extraction | Verify disk/extraction, remove incomplete output only, and use a small licensed subset for development |
| Unexpected output path | `out` is a directory | Look for `gget_cosmic_<project>_<searchterm>.csv/json` below that directory |

COSMIC commercial licensing and access rules are external constraints. A
`gget_mutate`-formatted export is routed to specialized-workflows; this skill
does not transform or interpret mutations.

## Open Targets

| Symptom | Likely cause | Recovery |
|---|---|---|
| Invalid resource | Resource spelling not in the seven-value set | Use `diseases`, `drugs`, `tractability`, `pharmacogenetics`, `expression`, `depmap`, or `interactions` |
| Filter key error | Key is not an exact returned flattened column | Query once unfiltered; copy names including dots and filter one at a time |
| No disease rows | Target/resource/endpoint has no rows or an upstream issue | Validate the Ensembl ID and retry a bounded disease query; preserve the log |
| Expression columns look unfamiliar | Current API is `baselineExpression`, not old tissue z-scores | Use `median/min/q1/q3/max`, biosample, datasource, and datatype fields |
| Expression appears incomplete | API page max is 3000 rows | Filter by `datasourceId`/`datatypeId` and set a deliberate `limit`; record truncation |
| Drug/interaction nested values vary | Singleton collapse and API schema | Inspect `df.iloc[0].to_dict()` before type-specific code |
| Filter logic surprises | Python dict filters are exact AND | Apply a boolean mask after retrieval for OR logic, or use the CLI's documented OR option |
| File missing | Python function has no `save`/`out` parameter | Call `df.to_csv`/`to_json` explicitly after validating it |

Open Targets disease IDs are EFO-mapped and can be MONDO, HP, Orphanet, or
EFO traits. Do not rename every row to a disease or treat the aggregate score
as a per-source score.

## G2P

| Symptom | Likely cause | Recovery |
|---|---|---|
| Missing gene and UniProt error | At least one identifier is required | Pass the gene or explicit accession, preferably both |
| Gene-only result seems wrong | Approximate canonical human reviewed lookup | Inspect candidate warning and pass the intended accession explicitly |
| Alignment validation error | Gene resolution cannot select an isoform, or `isoform` is absent | Pass canonical `uniprot_id="P01130-1"` and alternative `isoform="P01130-2"` |
| `residues` validation error | String/bool/unsupported iterable or map resource | Use int/list/range/set with features/alignment only |
| `None` after HTTP 200 | G2P returned JSON failure/unknown pair | Check gene/accession pairing and retry `map` with an explicit pair |
| Repeated 5xx/timeouts | Portal/network transient failure | Allow built-in 1/2/4-second retries, then stop and preserve diagnostics |
| Expected ClinVar/gnomAD/HGMD columns absent | Portal web overlays are not public G2P API fields | Use the portal directly and record the boundary |
| Raw structure expected | G2P map is only an identifier map | Route PDB retrieval/AlphaFold/sequence work to sequence-tools |

G2P always adds the canonical pair to returned rows and saves it in `df.attrs`.
Treat a pair mismatch as a hard identity problem, not as a missing annotation.

## Explicit routing exclusions

- **sequence-tools:** raw PDB/mmCIF retrieval, AlphaFold predictions, sequence
  retrieval, and downstream structure handling. G2P `PDB Ids List` is only a
  pointer for that handoff.
- **specialized-workflows:** mutation transformation, application of COSMIC
  mutation strings to sequences, and validation of `gget_mutate` outputs.
- **portal/UI workflows:** COSMIC account/licensing operations and G2P's
  portal-only clinical variant overlays. These cannot be reproduced by the
  public wrappers covered here.

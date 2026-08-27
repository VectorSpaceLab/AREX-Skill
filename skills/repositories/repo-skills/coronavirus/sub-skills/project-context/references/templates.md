# Project-context note templates

These are self-contained field guides for Markdown notes. They restate the repository conventions in `potential-targets/` and `publications/` without requiring the original checkout, templates, PDFs, or network access.

## Evidence-status vocabulary

Attach one status to every non-trivial scientific statement:

- **Source-backed:** directly supported by the supplied article, repository note, dataset metadata, or other named source. Include a citation, link, page/figure, or repository path when available.
- **Reported observation:** a source reports an observation, but this note does not independently verify it. Keep the source and the observation distinct.
- **Project hypothesis:** a proposed mechanism, target rationale, or experiment to investigate. Use tentative language such as `may`, `could`, or `we propose`; do not write it as an established effect.
- **Preparation observation:** a local file or preparation step records what was done to an input. This is not proof of biological or therapeutic efficacy.
- **Unresolved / not verified:** evidence is missing, ambiguous, or not checked. Say what would resolve it.

Do not use an evidence label to imply clinical efficacy, safety, approval, or generalizability. Those claims require their own cited evidence and scope.

## Potential-target note

Use this outline for a file under `potential-targets/`. Keep the headings discoverable and preserve the original concepts: rationale, existing drugs, hypotheses, and preparation notes.

```markdown
# [Target name]

- **Aliases / exact names:** [names as supplied; do not silently normalize]
- **Virus lineage:** [SARS-CoV / SARS-CoV-2 / both / unknown]
- **Note status:** [draft / reviewed / unresolved]

## Rationale

- **Statement:** [Why this target is relevant to the viral life cycle, only as supported by a named source.]
- **Evidence status:** [Source-backed / Reported observation / Project hypothesis / Unresolved]
- **Source:** [citation, DOI/preprint, URL, or repository evidence; `not supplied` if absent]
- **Scope and limits:** [what this does and does not establish]

## Existing Drugs

The table is an inventory of reported compounds or drugs, not an efficacy claim. Use `not verified` rather than filling gaps from memory.

| Drug or compound | Target location / interaction as reported | What the source says | Evidence status | Source |
|---|---|---|---|---|
| [name] | [site, residue, domain, or `not specified`] | [neutral, source-faithful note] | [status] | [citation/link] |

- **Interpretation limit:** [Separate an in-vitro, structural, computational, animal, or clinical report from the project's hypothesis.]
- **Unresolved:** [missing target location, lineage, assay, or source details]

## Hypotheses

Label each proposed mechanism as a hypothesis. Do not state or imply that a compound works, treats disease, or is safe unless the supplied source explicitly supports that narrowly scoped statement.

1. **Hypothesis:** [If the target interaction changed, the following function might change: ...]
   - **Basis:** [source-backed observation or structural premise]
   - **Evidence status:** Project hypothesis
   - **Test or limitation:** [what structure/simulation/assay would be needed]

## Preparation notes

- **Intended structure or assembly:** [apo, complex, oligomer, domain, or unknown]
- **Source structure ID and exact name:** [PDB/other ID; `not supplied` if absent]
- **Lineage of source:** [SARS-CoV / SARS-CoV-2 / unknown]
- **Chains, residues, ligands, and ranges:** [as supplied]
- **Experimental provenance:** [method/resolution if supplied; otherwise `not verified`]
- **Local prepared-system label/path:** [label only; do not claim it exists without evidence]
- **Transformations:** [extraction, truncation, alignment, homology modeling, protonation, capping, ligand edits]
- **Evidence status:** [Preparation observation / Source-backed / Unresolved]
- **Cross-check:** [structure name and ID agree / mismatch reported / not checked]
- **System-preparation handoff:** [link to the sibling system-preparation workflow when simulation or serialized outputs are requested]
- **Structure-curation handoff:** [link when chains, residues, PDB, FASTA, SDF, or ligand edits are requested]

## Open questions and provenance gaps

- [Question, missing source, unresolved lineage, or structure mismatch]
```

### Target-note rules

- Preserve the distinction between **rationale** and **hypothesis**. A rationale can summarize why a source considers a target relevant; a hypothesis proposes what the project might test.
- For existing drugs, record what a source reports and the setting (for example, structural, in-vitro, computational, animal, or clinical) only when supplied. Do not infer efficacy from target presence.
- Never omit preparation notes because the structure is not yet available. Use `not supplied` and state the next handoff.
- A structure reference is incomplete until its identifier, exact source name, lineage, and transformations are either recorded or explicitly marked unresolved.

## Publication note

Use this outline for a `README.md` inside an article folder. It follows the repository's annotated-bibliography convention.

```markdown
# [Article title]

## Citation

[Full citation exactly as supplied]

- **DOI:** [verified DOI / `not supplied` / `not verified`]
- **Preprint status:** [preprint / peer-reviewed / both versions / unknown]
- **Source used for this note:** [article, README, URL, or other supplied material]
- **Citation status:** [Source-backed / Unresolved]

## Summary of Article

- [Brief, source-faithful takeaway]
- [Brief, source-faithful takeaway]
- [Optional third takeaway]

- **Summary evidence status:** [Source-backed / Reported observation / Unresolved]
- **Scope and limits:** [what the supplied material supports; identify missing abstract/full text]

## Additional Notes

- **Observation or quotation:** [note]
  - **Evidence status:** [status]
  - **Source locator:** [page, figure, section, URL, or `not supplied`]
- **Structure references:** [IDs and exact names as supplied, or `none stated`]
- **Project relevance:** [careful connection to a target or prepared system; label as a project hypothesis if interpretive]
- **Unresolved questions:** [missing DOI, lineage, structure mapping, or other gap]
```

### Publication-note rules

- A title or URL alone is not proof of DOI, peer-review status, or article content. Preserve the uncertainty.
- Keep a brief summary separate from additional reading notes. Do not invent empty summary bullets; use `not available in supplied material`.
- If an article discusses a structure, record the article's claim separately from the local prepared system. Link to system-preparation only for preparation/equilibration questions.
- PDF copies may support later review but are never required by this runtime route. Network retrieval is optional external work, not an implicit step.

## Structure-name cross-check record

When a target or publication note refers to a structure, add a small record like this:

```markdown
### Structure provenance check

| Field | Note |
|---|---|
| Identifier | [e.g. supplied PDB ID] |
| Exact source name | [verbatim name] |
| Lineage | [SARS-CoV / SARS-CoV-2 / unknown] |
| Local system label | [if any] |
| Transformations | [or `none supplied`] |
| Match result | [match / mismatch / not checked] |
| Evidence | [citation or repository note] |
| Next route | [system-preparation / structure-curation / unresolved] |
```

A SARS-CoV source used for a SARS-CoV-2 homology model must remain visibly a source/template relationship. Do not rewrite the source ID as though it were an experimental SARS-CoV-2 structure.

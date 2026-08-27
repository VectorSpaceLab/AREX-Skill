# Project-context troubleshooting

This route produces and reviews Markdown context notes. It does not install packages, import Python modules, read PDFs, retrieve papers, edit coordinates, or run simulations.

## Install/import request

**Symptom:** A user asks to install a package, import OpenMM, or verify a runtime while drafting a target/publication note.

**Action:** Keep this sub-skill Markdown-only. Record the requested dependency or unresolved environment fact as a note if it affects provenance, but do not claim installation or import success. Route molecular-system preparation and runtime checks to the sibling `system-preparation` skill. Route PDB/FASTA/SDF and chain/residue/ligand operations to `structure-curation`.

A note can contain a handoff such as:

```markdown
- **Runtime status:** not checked in project-context; route to `system-preparation` before simulation.
```

## Unsupported medical or drug claim

**Symptom:** A draft says a drug is effective, treats COVID-19, is safe, or should be used because a target note or article mentions the compound.

**Action:** Remove the unsupported conclusion. Rewrite the statement to identify exactly what the supplied source reports and where it was observed. Add an evidence status and citation. Put any proposed mechanism under `Hypotheses` and use tentative language. If the source does not support even the reported observation, mark it `not verified` rather than repairing it from memory.

Do not treat a target table, binding location, docking result, molecular-dynamics observation, or in-vitro report as interchangeable with clinical efficacy.

## Missing DOI or preprint status

**Symptom:** The article folder has only a title, URL, incomplete citation, or PDF filename.

**Action:** Preserve the citation exactly as supplied, set `DOI` to `not supplied` or `not verified`, and set `Preprint status` to `unknown` unless the supplied material explicitly establishes it. Do not synthesize a DOI from a title or follow a network link as an implicit runtime step. Add the missing field to `Unresolved questions`.

## Evidence and hypothesis fields are confused

**Symptom:** A rationale, source observation, preparation action, and proposed mechanism are written in one paragraph, or a hypothesis is phrased as fact.

**Action:** Split the content:

1. Put a source's claim or observed result in `Rationale` or `Additional Notes` with a citation and `Source-backed` or `Reported observation` status.
2. Put the proposed intervention or mechanism in `Hypotheses` with `Project hypothesis` status.
3. Put local file transformations in `Preparation notes` with `Preparation observation` status.
4. If the distinction cannot be resolved, use `Unresolved` and state what evidence is missing.

Do not use a heading named `Evidence` as a substitute for a citation; status and source are separate fields.

## Mismatched structure ID, name, or lineage

**Symptom:** The PDB/structure ID does not match the stated molecule, the note conflates SARS-CoV with SARS-CoV-2, or a modeled/truncated structure is presented as the experimental source.

**Action:** Stop the provenance claim. Preserve both the supplied identifier and name, describe the mismatch, and mark `Match result: mismatch` or `not checked`. Distinguish source structure, template, local model, and prepared system. Route coordinate, chain, residue, alignment, or ligand correction to `structure-curation`. Route solvation, equilibration, serialized system, or simulation questions to `system-preparation` only after the structure is validated.

Never silently rename an ID or silently upgrade a homology model into a deposited structure.

## Preparation notes are absent

**Symptom:** A target note mentions a structure or intended simulation but has no preparation record.

**Action:** Keep the target note usable by filling every preparation field with `not supplied`, `unknown`, or `not checked` as appropriate. Record the missing source ID, assembly, transformations, and validation state in `Open questions and provenance gaps`. Link to `system-preparation` for a future preparation request; link to `structure-curation` if the missing information concerns input editing. Do not claim that a system is ready because a publication describes a related structure.

## PDF or network assumptions

**Symptom:** A workflow fails because a PDF is absent, a PDF parser is unavailable, a DOI URL cannot be reached, or an external literature service is offline.

**Action:** Do not make the runtime route depend on the PDF or network. Use supplied README text, citations, metadata, or explicitly provided excerpts. Mark summary and citation fields incomplete where necessary. Keep a source locator for what was actually supplied and add a follow-up item for human retrieval. Do not invent article content, DOI, peer-review status, structure identity, or drug claims.

## Empty or low-evidence publication summary

**Symptom:** The repository README contains placeholder bullets or notes without a source locator.

**Action:** Preserve the article title and citation fields, but write `Summary not available in supplied material` instead of filling generic takeaways. Mark the summary `Unresolved` and list the missing abstract/full text. Placeholder text is not evidence.

## Link or route confusion

**Symptom:** A note links to an original checkout path, an unavailable template, or the wrong sibling skill.

**Action:** Prefer links to bundled references such as `references/templates.md` and `references/troubleshooting.md`. Use sibling routes only for their owned work: `../system-preparation/SKILL.md` for simulation/system setup and `../structure-curation/SKILL.md` for coordinate/input curation. If a sibling file is not yet present, state the intended route in prose rather than depending on an external absolute path.

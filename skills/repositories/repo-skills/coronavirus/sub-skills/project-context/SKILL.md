---
name: project-context
description: "Route potential-target and publication notes for the coronavirus
  repository while preserving scientific evidence, hypotheses, and structure
  provenance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: CC BY 4.0
---

# Project context

Use this sub-skill when the task is about a potential target, target rationale, existing drugs, a target hypothesis, preparation notes, a publication summary, a citation, a DOI or preprint, or SARS/SARS-CoV-2 structural provenance.

This is a context-and-provenance route. It helps a future agent write or review concise Markdown notes; it does not establish medical efficacy, reproduce a paper, curate coordinates, or run molecular dynamics.

## Route the request

1. Identify the note kind before editing:
   - **Target note:** rationale, existing drugs, hypotheses, and preparation notes.
   - **Publication note:** citation and DOI/preprint status, brief summary, and additional notes.
   - **Cross-cutting provenance:** structure IDs, virus lineage, complex or apo state, and any modeled or transformed input.
2. Use the complete bundled field lists in [templates.md](references/templates.md). Do not depend on the repository's original templates being present.
3. Preserve the status of every substantive statement. Mark it as source-backed evidence, a project hypothesis, an unresolved question, or a preparation observation. Never upgrade a hypothesis into a demonstrated effect.
4. Cite the source for scientific claims. If a DOI, preprint, or citation cannot be confirmed from supplied material, write `not verified` or `not supplied`; do not guess.
5. If a note names a structure, cross-check its PDB/structure identifier and name against the documented structural provenance before presenting it as the prepared system. Record any homology model, truncation, alignment, protonation, capping, or other transformation as a transformation—not as the experimental source structure.
6. Link a structure-referencing note to the sibling [system-preparation route](../system-preparation/SKILL.md) for preparation and simulation details. Route residue/chain/ligand edits to [structure-curation](../structure-curation/SKILL.md).

## Target-note contract

Follow the repository's target-note concepts in a compact, explicit record:

- target name and aliases;
- rationale for the target in the SARS/SARS-2 life cycle, with citation and evidence status;
- existing drugs as a neutral inventory table (`Drug`, `Target Location`, `Notes`), with source and status for each row;
- hypotheses about how intervention could affect the target, explicitly labeled as hypotheses;
- preparation notes describing the intended structure, assembly, complex state, and provenance, with a handoff link if a system exists;
- unresolved questions, especially when the target name, lineage, or structural input is ambiguous.

Do not infer drug efficacy, clinical benefit, or safety from an inventory entry, an in-vitro observation, a docking idea, or a molecular-dynamics plan. A note can record a reported observation and separately state what the project proposes to investigate.

## Publication-note contract

Use one folder-level Markdown note per article as the repository convention describes. Include:

- the article title and proper citation;
- DOI when verified, otherwise an explicit missing/unverified marker;
- whether the item is peer-reviewed, a preprint, or unknown from the supplied evidence;
- a brief, source-faithful two- or three-point summary;
- additional notes, quotations, identifiers, or questions with their evidence status;
- any structure IDs mentioned by the article, separately cross-checked against project preparation records.

A PDF is source evidence, not a runtime dependency. Do not make note creation depend on PDF extraction or network retrieval. If the supplied material is only a title, link, or incomplete README, state the limit and leave unverified fields visible.

## Structural provenance rules

Treat an identifier and a scientific interpretation as separate fields. At minimum record:

- structure identifier and exact source name;
- SARS-CoV, SARS-CoV-2, or unknown lineage;
- molecule or complex represented and relevant chains/ranges if known;
- experimental method/resolution when supplied;
- local preparation label, if any;
- transformations and their evidence (extraction, truncation, alignment, homology modeling, protonation, capping, or ligand edits);
- cross-check result and remaining uncertainty.

For example, the repository documents 2AJF as a SARS-CoV spike RBD:ACE2 source while also documenting a SARS-CoV-2 modeled derivative; those must not be collapsed into one source claim. Similar distinctions apply to 6VSB, 6M17, 6LU7, 2FE8, and other IDs recorded by system-preparation documentation. Use only the identity and facts supplied by the note or bundled references.

A structure name mismatch, missing source ID, or unexplained SARS-versus-SARS-2 substitution is a provenance block. Stop the contextual claim, report the mismatch, and route coordinate repair to structure-curation. If the structure is already validated and the question is solvation/equilibration or serialized outputs, route to system-preparation instead.

## Boundaries and safe behavior

- No OpenMM, Folding@home, simulation, equilibration, or long-trajectory commands here.
- No PDB, FASTA, SDF, chain, residue, or ligand manipulation here.
- No PDF reading, DOI lookup, web retrieval, or checkout-path assumption is required at runtime.
- Notes complement structure curation and simulation validation; they never replace either one.
- Do not claim a structure was prepared, simulated, or validated merely because a publication or target note mentions it.
- Keep medical, therapeutic, and drug-effect language scoped to what the cited source actually reports.

## Review checklist

Before handing off a note, verify that the correct note kind and all required fields are present, each claim has an evidence status, citation/DOI/preprint uncertainty is explicit, and the target/structure names agree. Check internal route links and use the troubleshooting guidance in [troubleshooting.md](references/troubleshooting.md) for blocked cases. No executable project-context script is intentionally bundled.

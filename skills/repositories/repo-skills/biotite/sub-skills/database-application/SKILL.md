---
name: database-application
description: "Use Biotite database clients and external application wrappers for
  biological fetch/query planning, BLAST/MSA/DSSP/SRA/Vina/Tantan/ViennaRNA
  orchestration, and optional dependency diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Database and Application

Use this sub-skill when a task centers on `biotite.database` network services or `biotite.application` wrappers around web services and external command-line tools.

## Route Here For

- RCSB PDB, AlphaFold DB, Entrez/NCBI, UniProt, and PubChem search/fetch planning.
- Choosing remote IDs, query objects, formats, target paths, overwrite/cache behavior, and retry/skip strategies for network work.
- BLAST web searches with `BlastWebApp` and NCBI request-rule expectations.
- Multiple sequence alignment wrappers for Clustal Omega, MAFFT, MUSCLE 3, and MUSCLE 5.
- DSSP secondary-structure annotation through `mkdssp` and the distinction from Biotite's local P-SEA-style structure helper.
- SRA reads through `prefetch`/`fasterq-dump`, repeat masking with `tantan`, docking with AutoDock Vina, and RNA secondary-structure tools from ViennaRNA.
- Explaining missing external binaries, wrapper lifecycle errors, timeout/cancel behavior, temporary-output contracts, and optional dependency/version differences.

## Use Another Biotite Sub-skill For

- Sequence construction, symbols, annotations, local alignments, profiles, phylogeny, and analysis after remote sequence data is available: [../sequence-analysis/SKILL.md](../sequence-analysis/SKILL.md).
- In-memory `AtomArray` filtering, geometry, bonds, contacts, superposition, and trajectory analysis after structures are loaded: [../structure-analysis/SKILL.md](../structure-analysis/SKILL.md).
- Parsing fetched FASTA, GenBank, PDB, PDBx/mmCIF, BinaryCIF, SDF/MOL, and trajectory files: [../file-io-formats/SKILL.md](../file-io-formats/SKILL.md).
- PyMOL, RDKit, OpenMM, plotting, display, and visualization-oriented conversion: route to the `interfaces-visualization` sub-skill when available.

## Start With

1. Classify the task as network database, web application, or local external executable; do not run network or external binaries unless the user/environment explicitly allows it.
2. For database work, decide the service, query/ID type, output format, target path/cache policy, and parser handoff before fetching.
3. For application wrappers, check required binaries first, construct the Biotite input objects, set all options while the app is still in `CREATED` state, then use `start()`, `join(timeout=...)`, and result getters only after `JOINED`.
4. Route file parsing and downstream analysis to sibling sub-skills after the remote/application boundary is complete.
5. When dependency availability is uncertain, run the bundled no-network diagnostic instead of probing services or executing analyses.

## References

- API map and ownership boundaries: [references/api-reference.md](references/api-reference.md).
- Database and wrapper recipes: [references/workflows.md](references/workflows.md).
- Failure recovery and safe-skip guidance: [references/troubleshooting.md](references/troubleshooting.md).
- Optional dependency diagnostic: [scripts/check_optional_applications.py](scripts/check_optional_applications.py).

## Quick Dependency Check

From the Biotite skill root, run the safe diagnostic when a task depends on optional wrappers:

```bash
python sub-skills/database-application/scripts/check_optional_applications.py
```

The helper checks Biotite wrapper imports and executable presence/version-output probes only. It does not contact databases, submit BLAST/SRA jobs, or run molecular analyses.

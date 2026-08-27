---
name: coronavirus
description: "Use the Folding@home coronavirus repository conventions to curate
  molecular structures, prepare bounded OpenMM systems, and preserve target,
  publication, and provenance notes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: CC BY 4.0
---

# Coronavirus repository skill

Use this repo-specific operating skill for reusable work derived from the Folding@home coronavirus preparation repository. It covers structure curation, OpenMM preparation/equilibration mechanics, and project-context notes. It does not run Folding@home clients, network acquisition, long production trajectories, or medical/therapeutic interpretation.

## Route first

1. **Need to inspect, select, truncate, or rename a PDB/FASTA/SDF input?** Read [structure-curation](sub-skills/structure-curation/SKILL.md). Validate before changing anything and use its explicit-output helpers.
2. **Need solvent, ions, force fields, minimization, bounded equilibration, XML/PDB serialization, or a 4/5 fs continuation?** Read [system-preparation](sub-skills/system-preparation/SKILL.md). Begin from a validated topology and use CPU OpenMM as the required baseline.
3. **Need a potential-target or publication note, evidence status, source citation, or structural provenance record?** Read [project-context](sub-skills/project-context/SKILL.md). Keep source evidence, hypotheses, and preparation observations separate.
4. **Need a cross-cutting diagnosis?** Read [troubleshooting.md](references/troubleshooting.md), then the nearest sub-skill troubleshooting reference. Run [check_openmm_env.py](scripts/check_openmm_env.py) only for environment/platform diagnostics.

## Integrated operating sequence

For a new simulation input, establish source-structure identity and note provenance first; curate and validate the coordinate topology; choose and document the force-field/ligand parameter path; prepare a small CPU OpenMM system; run only a bounded minimization/equilibration smoke check; inspect energy, atom count, box, and output bundle; then record exact parameters, versions, warnings, and limitations. A later Researcher may expand the run only with an explicit scientific and compute budget.

Do not treat a filename, a successful PDB parse, a short CPU step, or XML serialization as proof of biological identity, force-field suitability, stable long-timestep dynamics, binding, efficacy, or reproducibility across platforms.

## Repository-specific conventions

The source project documents rapidly prepared inputs and commonly uses `equilibrated_4fs.pdb` as the Folding@home handoff. Reusable generated helpers use safer explicit arguments and short defaults instead of historical hard-coded paths or multi-nanosecond defaults. A 4 amu hydrogen mass and 4/5 fs continuation are historical workflow conventions that must be disclosed and validated for the actual system, not universal recommendations.

The required backend for this selected scope is CPU OpenMM. CUDA is optional: platform enumeration succeeded in inspection, but context creation was limited by `CUDA_ERROR_UNSUPPORTED_PTX_VERSION`. Do not claim CUDA verification or require it for a CPU result.

## Handoffs

- Structure edits and post-tool validation: [structure-curation](sub-skills/structure-curation/SKILL.md).
- OpenMM system construction and continuation: [system-preparation](sub-skills/system-preparation/SKILL.md).
- Target/publication/provenance records: [project-context](sub-skills/project-context/SKILL.md).
- Cross-cutting failures and scientific-limit reporting: [troubleshooting](references/troubleshooting.md).

Use [repo-provenance.md](references/repo-provenance.md) to anchor claims to the source revision and evidence paths. This generated skill is intentionally left in the repository-local output tree and is **not imported** into the managed DisCo skill library.

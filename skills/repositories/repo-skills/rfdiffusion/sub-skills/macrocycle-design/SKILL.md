---
name: macrocycle-design
description: "Build RFpeptides macrocyclic peptide monomer and binder
  RFdiffusion commands, including cyclic flags, macrocycle contigs,
  target/binder chain layout, hotspot formatting, and validation checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Macrocycle Design

Use this sub-skill when the user wants RFdiffusion/RFpeptides commands or debugging help for macrocyclic peptide generation, either as a standalone cyclic monomer or as a cyclic peptide binder against a protein target.

## Route Here

Route to `macrocycle-design` for:

- RFpeptides macrocyclic peptide workflows.
- Standalone macrocyclic monomers using a generated-length contig such as `12-18`.
- Macrocyclic binders that combine a generated cyclic peptide with a target chain and hotspot residues.
- `inference.cyclic=True`, `inference.cyc_chains`, and macrocycle-specific chain layout checks.
- RFpeptides-style examples using `diffuser.T=50`.
- Explaining chain ID, residue numbering, hotspot quoting, and output validation caveats for macrocycles.

Route elsewhere when:

- The task is general PPI hotspot selection or non-cyclic binders; use `../binder-design/SKILL.md`.
- The task is cyclic, dihedral, or tetrahedral oligomer symmetry with `inference.symmetry`; use the symmetric-oligomer sub-skill if present.
- The task is tuning general guiding potentials; use the guided-potentials sub-skill if present.
- The task is unconditional non-cyclic monomer generation; use `../unconditional-generation/SKILL.md`.

## Required Inputs

Collect these before drafting a command:

- Runtime path to the user's installed `run_inference.py` launcher or equivalent RFdiffusion entry point.
- Model weights location if the installation does not already discover RFdiffusion weights.
- Output prefix where RFdiffusion can write indexed `.pdb` and `.trb` files.
- Macrocycle length range, such as `12-18`, and which generated chain(s) should be cyclic.
- For binders: target PDB path, target chain/span contig, and hotspot residues in the target PDB numbering.
- Number of designs; start with a pilot batch before scaling.
- Whether the input PDB was renumbered or cropped, because hotspots and contigs must match that exact runtime file.

## Core Command Patterns

Detailed templates are in `references/workflows.md`.

Standalone macrocyclic peptide monomer:

```bash
run_inference.py \
  --config-name base \
  inference.output_prefix=outputs/macro_monomer/design \
  inference.num_designs=10 \
  'contigmap.contigs=[12-18]' \
  inference.cyclic=True \
  diffuser.T=50 \
  inference.cyc_chains='a'
```

Macrocyclic peptide binder:

```bash
run_inference.py \
  --config-name base \
  inference.output_prefix=outputs/macro_binder/design \
  inference.num_designs=10 \
  'contigmap.contigs=[12-18 A3-117/0]' \
  inference.input_pdb=target.pdb \
  inference.cyclic=True \
  diffuser.T=50 \
  inference.cyc_chains='a' \
  'ppi.hotspot_res=[A51,A52,A50,A48,A62,A65]'
```

Keep Hydra list-like values in single quotes. If the user's shell or launcher needs escaped inner quotes for hotspot entries, use the equivalent form documented in `references/workflows.md`.

## Cyclic Flags

RFpeptides macrocycle runs need both cyclic settings:

- `inference.cyclic=True` declares that at least one chain should be designed as cyclic.
- `inference.cyc_chains='a'` names the generated chain IDs to cyclize as a lowercase string.
- Use `inference.cyc_chains='abcd'` only when the contig creates compatible generated chains for those IDs.
- Do not replace these flags with `inference.symmetry=cN`; symmetry oligomer design is a different workflow.

The default base config includes `inference.cyclic=False` and `inference.cyc_chains='a'`, so macrocycle commands must explicitly turn `inference.cyclic=True` on.

## Contig And Chain Layout

Macrocycle contigs follow RFdiffusion's normal contig syntax but the cyclic chain selection makes chain ordering important:

- Monomer macrocycle: use one generated segment, for example `'contigmap.contigs=[12-18]'`; this generated chain is chain `a` for `inference.cyc_chains='a'`.
- Binder macrocycle: put the generated cyclic peptide segment first, then the target segment, then `/0`, for example `'contigmap.contigs=[12-18 A3-117/0]'`.
- The example layout cyclizes the generated peptide chain, not the target chain.
- Use target chain IDs and residue numbers from the runtime input PDB in target contigs and hotspots.
- If a target PDB has been cropped or renumbered, update the contig and hotspots to the cropped/renumbered file rather than to a database accession.

RFpeptides example data notes that the GABARAP target chain A residue indices were shifted by `+2` relative to PDB ID `7zkr`; treat that as a warning pattern, not as a universal rule for user targets.

## Hotspots For Macrocyclic Binders

Use hotspots only for binder workflows with a target:

- Format as a Hydra list: `'ppi.hotspot_res=[A51,A52,A50,A48,A62,A65]'`.
- Hotspot residues belong to the target chain in the input PDB, not the cyclic peptide chain.
- Prefer a small interface-defining set, often 3-6 residues, and run pilots to see whether the macrocycle contacts the intended site.
- Verify each hotspot lies inside the retained target contig and exists in the exact input PDB.
- If copying shell examples that use escaped quoted entries like `ppi.hotspot_res=[\'A51\',\'A52\']`, keep the whole override shell-safe and do not let the shell strip brackets or commas.

For general non-cyclic hotspot strategy, route to `binder-design`; keep this sub-skill focused on the macrocycle-specific flags and layout.

## Validation Checklist

Before handing off a macrocycle command, check:

- `inference.cyclic=True` is present.
- `inference.cyc_chains` names the intended generated chain(s), usually `'a'` for single macrocycles.
- `diffuser.T=50` is set for RFpeptides-style examples unless the user deliberately changes the diffusion schedule.
- The contig is quoted as a single Hydra list and uses `/0` only where a target/binder chain break is intended.
- Binder hotspots are quoted safely and match the runtime input PDB numbering.
- The target chain is not accidentally listed in `inference.cyc_chains`.
- `inference.output_prefix` is a path prefix, not just a directory.
- The command uses user runtime paths, not paths from the RFdiffusion source checkout.

## Output Checks

After a successful run, expect RFdiffusion-style outputs:

- `output_prefix_0.pdb`, `output_prefix_1.pdb`, and so on for final backbones.
- `output_prefix_0.trb` metadata files containing the resolved config and contig mappings.
- Optional trajectory files under a sibling `traj/` directory when `inference.write_trajectory=True`.

Inspect final PDBs to confirm the cyclic peptide is the intended generated chain and that binder outputs include target and peptide chains in the expected layout. Backbone generation does not prove binding; macrocyclic binders still need downstream sequence design and structure/interface assessment.

## References

- `references/workflows.md` for monomer and binder command templates.
- `references/troubleshooting.md` for chain, hotspot, Hydra, numbering, and validation failures.

---
name: structure-generation
description: "Guides agents using datamol to generate and manipulate molecular
  structures, including conformers, SASA, alignment, fragmentation, scaffolds,
  reactions, attachments, and isomer enumeration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datamol Structure Generation

Use this sub-skill when a task asks to create, enumerate, transform, align, fragment, assemble, scaffold, or react molecular structures with datamol beyond basic molecule conversion.

## Route By Task

- **Conformers and 3D features**: Use `dm.conformers.generate`, `dm.conformers.cluster`, `dm.conformers.rmsd`, `dm.conformers.sasa`, `dm.conformers.get_coords`, `dm.conformers.center_of_mass`, and `dm.conformers.keep_conformers`; see [workflows](references/workflows.md#conformer-generation-sasa-and-3d-features) and [API guidance](references/api-reference.md#conformers-and-3d-features).
- **Alignment and atom ordering**: Use `dm.align.template_align`, `dm.align.auto_align_many`, `dm.conformers.align_conformers`, and `dm.reorder_mol_from_template`; see [workflows](references/workflows.md#alignment-and-reordering) and [API guidance](references/api-reference.md#alignment-and-reordering).
- **Fragmentation and assembly**: Use `dm.fragment.brics`, `frag`, `recap`, `anybreak`, `mmpa_cut`, `break_mol`, `build`, and `assemble_fragment_order`; see [workflows](references/workflows.md#fragmentation-and-assembly) and [API guidance](references/api-reference.md#fragmentation-and-assembly).
- **Scaffolds and fuzzy scaffolds**: Use `dm.to_scaffold_murcko`, `dm.make_scaffold_generic`, `dm.strip_mol_to_core`, `dm.compute_ring_system`, and `dm.scaffold.fuzzy_scaffolding`; see [workflows](references/workflows.md#scaffold-and-fuzzy-scaffold-workflows).
- **Reactions and attachments**: Use `dm.reactions.rxn_from_smarts`, `apply_reaction`, `select_reaction_output`, `is_reaction_ok`, `can_react`, `inverse_reaction`, `convert_attach_to_isotope`, `num_attachment_points`, and `open_attach_points`; see [workflows](references/workflows.md#reaction-application-and-attachment-points).
- **Isomer enumeration**: Use `dm.enumerate_tautomers`, `dm.enumerate_stereoisomers`, `dm.count_stereoisomers`, `dm.enumerate_structisomers`, `dm.canonical_tautomer`, and `dm.remove_stereochemistry`; see [workflows](references/workflows.md#isomer-and-tautomer-enumeration).

## Boundaries

- For SMILES parsing, molecule cleaning, neutralization, salt removal, or SDF/dataframe I/O, use the sibling `molecule-io-prep` skill before this one.
- For fingerprints, pairwise distances, clustering generated sets by similarity, or diversity selection, use the sibling `fingerprints-similarity` skill after structure generation.
- For drawing products, conformers, highlights, or scaffold grids, use the sibling `visualization-utilities` skill after this one.

## Safety Defaults

- Convert inputs with `dm.to_mol`, then sanitize or standardize through `molecule-io-prep` before reactions, conformers, and enumeration.
- Bound expensive operations with small `n_confs`, `n_variants`, `depth`, `timeout_seconds`, `max_n_mols`, `rms_cutoff`, and `num_threads=1` until the workflow is proven.
- Treat reaction SMARTS, structural isomer enumeration, fuzzy scaffolds, MCS alignment, and fragment assembly as potentially combinatorial.
- See [troubleshooting](references/troubleshooting.md) when embedding fails, no conformers exist, template matches are ambiguous, reactions return no products, or enumeration grows too large.

## Bundled Smoke Script

Run a deterministic tiny exercise of conformer generation, scaffold extraction, reaction application, and isomer counting:

```bash
python sub-skills/structure-generation/scripts/structure_generation_smoke.py --help
python sub-skills/structure-generation/scripts/structure_generation_smoke.py
```

The script prints JSON and uses only local CPU chemistry operations.

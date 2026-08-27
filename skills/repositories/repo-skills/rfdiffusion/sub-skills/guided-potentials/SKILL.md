---
name: guided-potentials
description: "Configure RFdiffusion auxiliary guiding potentials, including
  monomer compactness/contact, oligomer contacts, binder compactness/contact
  potentials, substrate contacts, guide scale/decay, Hydra quoting, and
  workflow-specific caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RFdiffusion Guided Potentials

Use this sub-skill when a user wants to add, tune, validate, or debug RFdiffusion auxiliary potentials during inference.

Guiding potentials bias the reverse-diffusion update toward differentiable objectives. They are useful for compact monomers, contact-rich symmetric oligomers, motif scaffolding with compactness pressure, and enzyme active-site workflows that implicitly model a substrate. They are not a substitute for a correct contig, checkpoint, or design strategy.

## Route Here

Route to `guided-potentials` for:

- `potentials.guiding_potentials` syntax, quoting, and comma-separated per-potential arguments.
- Tuning `potentials.guide_scale` and `potentials.guide_decay`.
- Monomer compactness or contact bias with `monomer_ROG` or `monomer_contacts`.
- Symmetric oligomer contact bias with `olig_contacts`, `potentials.olig_intra_all`, `potentials.olig_inter_all`, or `potentials.olig_custom_contact`.
- Binder compactness/contact potentials such as `binder_ROG`, `binder_ncontacts`, `interface_ncontacts`, or `dimer_ROG` when the run already has a binder-style contig.
- Enzyme or active-site substrate contact bias with `substrate_contacts` and `potentials.substrate`.
- Troubleshooting unknown potential names, Hydra list quoting, unsupported decay types, bad oligomer contact strings, and substrate atom failures.

Route elsewhere when:

- The user only needs a plain de novo monomer command; use `../unconditional-generation/SKILL.md`.
- The user needs target/binder contig ordering, hotspot choice, or PPI strategy; use `../binder-design/SKILL.md` first, then return here only for intentional potential pilots.
- The user needs cyclic, dihedral, tetrahedral, or other symmetry setup; use `../symmetric-oligomers/SKILL.md` first.
- The user needs motif or active-site contig construction; use `../motif-scaffolding/SKILL.md` first, then return here for potential parameters.

## Required Context

Collect these before recommending potential overrides:

- Base workflow type: unconditional monomer, symmetric oligomer, binder/PPI, motif scaffolding, or active-site/enzyme.
- Existing working command without potentials, or enough inputs to route to the sibling sub-skill that owns the base command.
- Intended objective: compactness, more intra-chain contacts, more inter-chain contacts, repulsion between selected oligomer chains, binder compactness, interface contacts, or substrate packing.
- Whether the user can run short pilot batches and compare against a no-potential baseline.
- Runtime-visible paths for input PDBs, output prefixes, and optional checkpoints; do not reuse paths from the RFdiffusion source checkout.

## Override Pattern

RFdiffusion expects a Hydra list of strings. In shell commands, quote the whole override with single quotes and put each potential as a double-quoted string inside the list:

```bash
'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]' \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Each potential string is parsed as comma-separated `key:value` pairs. `type` is required and remains a string; all other per-potential values are parsed as floats by RFdiffusion's potential manager.

Available source-backed potential names:

- `monomer_ROG`: compact a monomer by minimizing radius of gyration; useful for compact de novo or motif scaffolds.
- `monomer_contacts`: maximize contacts within a monomer; example weight is small, such as `0.05`.
- `olig_contacts`: add attractive or repulsive contact objectives between chains in symmetric runs.
- `binder_ROG`: compact the binder segment of a binder-style run; requires a detected binder length.
- `binder_ncontacts`: increase contacts within the binder segment; requires a detected binder length.
- `interface_ncontacts`: increase contacts across binder and target segments; requires a detected binder length.
- `dimer_ROG`: compact both halves of a dimer-style run; requires a detected binder length.
- `substrate_contacts`: implicitly model ligand/substrate contacts for active-site scaffolding; requires `potentials.substrate` and an input motif PDB containing that residue.

See `references/potential-reference.md` for parameters, defaults, and caveats.

## Safe Starting Points

Always recommend a no-potential baseline first when the user is not reproducing a known example. Then make a small pilot batch with one potential family and conservative weights.

Monomer compactness:

```bash
run_inference.py \
  inference.output_prefix=outputs/compact_monomer/design \
  'contigmap.contigs=[100-200]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:monomer_ROG,weight:1,min_dist:5"]' \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Monomer contacts:

```bash
run_inference.py \
  inference.output_prefix=outputs/contact_monomer/design \
  'contigmap.contigs=[100-200]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:monomer_contacts,weight:0.05"]'
```

Symmetric oligomer contacts:

```bash
run_inference.py \
  --config-name=symmetry \
  inference.symmetry=C6 \
  inference.output_prefix=outputs/c6/design \
  'contigmap.contigs=[480-480]' \
  inference.num_designs=10 \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay=quadratic
```

Enzyme substrate contacts:

```bash
run_inference.py \
  inference.output_prefix=outputs/enzyme/design \
  inference.input_pdb=active_site_input.pdb \
  'contigmap.contigs=[10-100/A1083-1083/10-100/A1051-1051/10-100/A1180-1180/10-100]' \
  'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' \
  potentials.substrate=LLK \
  potentials.guide_scale=1 \
  inference.ckpt_override_path=/path/to/ActiveSite_ckpt.pt
```

The active-site checkpoint path must be supplied by the user from their installed model location.

## Tuning Rules

- Start with the published examples, then vary one knob at a time.
- Use small pilot batches before production; excessive potential strength can produce poor proteins.
- `potentials.guide_scale` globally scales potential gradients; examples use `2` for compactness/oligomers and `1` for substrate contacts.
- `potentials.guide_decay` accepts `constant`, `linear`, `quadratic`, or `cubic`; `quadratic` applies the potential more strongly early in denoising and weakens it later.
- For `olig_contacts`, start with intra-chain weight larger than inter-chain weight, such as `weight_intra:1,weight_inter:0.1` or `0.06`.
- For PPI/hotspot workflows, warn that repository guidance says potentials can interact oddly with hotspot residues. Baseline without potentials, then pilot compactness/contact potentials only if the user has a clear reason.

## Validator Helper

Use the bundled helper for lightweight syntax checks before giving a command:

```bash
python sub-skills/guided-potentials/scripts/validate_potential_override.py \
  --guiding-potentials '["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
  --guide-decay quadratic \
  --symmetry C6 \
  --olig-intra-all \
  --olig-inter-all
```

The helper does not run RFdiffusion and does not need model weights. It validates source-backed potential names, numeric parameters, guide decay, oligomer contact strings, and substrate requirements.

## Validation Checklist

Before finalizing a guided command, verify:

- The base command is valid for the workflow before adding potentials.
- `potentials.guiding_potentials` is a quoted Hydra list of quoted strings.
- Each potential string includes `type:<implemented_name>`.
- Non-`type` potential arguments are numeric because RFdiffusion parses them as floats.
- `potentials.guide_decay` is one of `constant`, `linear`, `quadratic`, or `cubic`.
- `olig_contacts` is used with symmetry and an all/custom contact specification.
- `substrate_contacts` includes `potentials.substrate=<resname>` and an input PDB with that substrate residue.
- Binder potentials are only used when RFdiffusion can infer a binder length from the binder-style run.
- Hotspot/PPI runs include a no-potential baseline and a small pilot if potentials are added.

## References

- `references/potential-reference.md` for implemented potential names, arguments, defaults, and source behavior.
- `references/workflows.md` for concrete monomer, oligomer, binder, and enzyme command patterns.
- `references/troubleshooting.md` for Hydra, unknown potential, oligomer, substrate, and hotspot interaction failures.

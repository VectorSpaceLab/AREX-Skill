---
name: rfdiffusion
description: "Use RFdiffusion for protein backbone generation workflows,
  including unconditional design, motif scaffolding, partial diffusion, binder
  design, symmetric oligomers, guided potentials, scaffold-guided design, and
  RFpeptides macrocycles."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RFdiffusion

Use this skill when a user wants practical RFdiffusion command construction, workflow routing, input validation, or troubleshooting for protein structure generation. RFdiffusion generates protein backbones with Hydra-configured inference workflows, model checkpoints, contigs, optional targets, optional potentials, and workflow-specific inputs.

## First Checks

Before building a production command, confirm:

- RFdiffusion imports in the active Python environment: `python -c "import rfdiffusion; import rfdiffusion.inference.utils"`.
- The user has downloaded model weights and knows their runtime model directory, or will pass `inference.model_directory_path=/path/to/models`.
- The intended runtime has a compatible PyTorch backend; GPU is strongly preferred for real designs.
- Every input PDB, scaffold tensor, checkpoint, or output prefix is a user runtime path, not a path from any source checkout.
- Hydra list overrides are shell-quoted, for example `'contigmap.contigs=[100-200]'`.

Use `scripts/check_rfdiffusion_environment.py` for a safe import/model-weight preflight and `scripts/build_inference_command.py` for reusable command assembly.

## Route By Workflow

- Use `sub-skills/unconditional-generation/SKILL.md` for de novo monomer or backbone generation from only a length/range and output prefix.
- Use `sub-skills/motif-scaffolding/SKILL.md` for fixed motifs, active sites, inpaint sequence/structure masks, target-aware motif contigs, and motif checkpoint choices.
- Use `sub-skills/partial-diffusion/SKILL.md` for diversifying an existing backbone or complex with `diffuser.partial_T` and optional `contigmap.provide_seq`.
- Use `sub-skills/binder-design/SKILL.md` for PPI binders, hotspots, target/binder contigs, flexible peptide targets, scaffolded PPI, and downstream assessment boundaries.
- Use `sub-skills/symmetric-oligomers/SKILL.md` for cyclic, dihedral, tetrahedral, octahedral, or icosahedral oligomers and symmetric motif scaffolding.
- Use `sub-skills/guided-potentials/SKILL.md` for `potentials.guiding_potentials`, compactness/contact/substrate/oligomer potentials, guide scale, and guide decay.
- Use `sub-skills/scaffold-guided-design/SKILL.md` for fold conditioning with scaffold directories, secondary-structure tensors, block adjacency tensors, target tensors, and sampled insertions.
- Use `sub-skills/macrocycle-design/SKILL.md` for RFpeptides macrocyclic monomers and macrocyclic binders using `inference.cyclic=True` and `inference.cyc_chains`.

## Shared References

- Read `references/configuration-reference.md` when translating a natural-language request into Hydra overrides.
- Read `references/model-weights.md` when the task depends on checkpoint filenames, model directories, or download expectations.
- Read `references/troubleshooting.md` for install/import, SE(3)-Transformer, DGL/e3nn, CUDA, model-weight, quoting, and output failures.
- Read `references/repo-provenance.md` before deciding whether this skill matches a current RFdiffusion checkout.

## Common Command Shape

RFdiffusion’s central entrypoint is the installed `run_inference.py` script from the package distribution. Do not require a future agent to reopen the original repository examples; build commands from the bundled sub-skill references.

```bash
run_inference.py \
  inference.output_prefix=outputs/design \
  inference.num_designs=10 \
  inference.model_directory_path=/path/to/models \
  'contigmap.contigs=[100-200]'
```

For symmetric designs, add `--config-name=symmetry`. For macrocycles, do not use symmetry config unless the task is a symmetric oligomer; use the macrocycle sub-skill’s `inference.cyclic=True` route instead.

## Output Expectations

A design prefix such as `outputs/run/design` normally yields numbered files such as `outputs/run/design_0.pdb` and `outputs/run/design_0.trb`. With trajectories enabled, RFdiffusion also writes multi-model trajectory PDBs below a sibling `traj/` directory. The `.trb` file stores resolved config, timing/device information, pLDDT arrays, and contig mappings.

## Boundaries

This skill helps future agents assemble and debug RFdiffusion workflows. It does not provide model weights, run network downloads by default, validate scientific binding success, replace downstream ProteinMPNN/structure-prediction pipelines, or promise CPU production performance. Treat native RFdiffusion examples as evidence; use the bundled references and scripts as the self-contained runtime guidance.

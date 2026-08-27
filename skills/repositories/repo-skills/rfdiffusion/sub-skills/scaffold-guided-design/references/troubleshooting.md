# Scaffold-Guided Troubleshooting

Use this reference when RFdiffusion scaffold-guided commands fail before sampling, silently select the wrong workflow, or produce suspicious input-shape errors.

## `can't provide scaffold_dir if you're also specifying per-residue ss`

Cause: the command mixes scaffold directory tensor inputs with `contigmap.inpaint_str_helix`, `contigmap.inpaint_str_strand`, or `contigmap.inpaint_str_loop`.

Fix:

- For scaffold libraries, keep `scaffoldguided.scaffold_dir=...` and remove the per-residue secondary-structure masks.
- For flexible peptide or per-residue secondary-structure tasks, remove `scaffoldguided.scaffold_dir` and keep the relevant `contigmap.inpaint_str_*` override.

## `can't add length if not masking loops`

Cause: `scaffoldguided.mask_loops=False` is combined with `sampled_insertion`, `sampled_N`, or `sampled_C` set above zero.

Fix:

- For fixed scaffold PPI, keep `mask_loops=False` and set all sampled additions to `0`.
- For variable-length monomer fold conditioning, set `mask_loops=True` and then use sampled loop/terminal additions.

## Missing Or Unpaired Scaffold Tensors

Symptoms:

- File-not-found errors for `ID_ss.pt` or `ID_adj.pt`.
- Empty scaffold list because no `*_ss.pt` files are found.
- A scaffold list item fails even though a similarly named tensor exists.

Fix:

- Place paired tensors in the same `scaffold_dir`.
- Use shared IDs: `foo_ss.pt` and `foo_adj.pt`.
- Put suffix-free IDs such as `foo` in `scaffold_list` text files.
- Run `scripts/check_scaffold_inputs.py --scaffold-dir ... --scaffold-list ...` before inference.

## Tensor Shape Errors

Symptoms:

- One-hot encoding errors.
- Matrix reshape failures.
- Length mismatch between secondary structure and adjacency.
- Target tensor shape mismatch after crop.

Fix:

- Scaffold `*_ss.pt` should be a 1D tensor of length `L`.
- Scaffold `*_adj.pt` should be square with shape `(L, L)`.
- Target `*_ss.pt` should be 1D length `T` and `target_adj.pt` should be `(T, T)`.
- If `contig_crop` or an externally cropped target PDB is used, regenerate or select target tensors for that exact target residue set.

## Target PDB Mode Starts But Binder Context Is Wrong

Symptoms:

- The run behaves like monomer fold conditioning even though a target was intended.
- Hotspots are ignored or cannot be mapped.
- Target residues appear inconsistent with tensor lengths.

Fix:

- Set `scaffoldguided.target_pdb=True`.
- Provide `scaffoldguided.target_path=target.pdb`.
- Provide `ppi.hotspot_res` using chain-qualified target PDB residue numbers.
- Route target crop and hotspot selection decisions to `../binder-design/SKILL.md`.

## Scaffolded PPI Quality Is Poor Or Too Diverse

Likely causes:

- Noise scales are too high for target-bound scaffolded design.
- Hotspots are too broad, buried, or not on the intended interface.
- The scaffold library is too small or incompatible with the target site.
- Loops are being lengthened unnecessarily for a large scaffold library.

Fix:

- Try `denoiser.noise_scale_ca=0` and `denoiser.noise_scale_frame=0` for a strict low-noise pilot, or `0.5` for a diversity compromise.
- Keep `mask_loops=False` for large PPI scaffold sets unless there is a specific reason to add length diversity.
- Confirm hotspot choices with the binder-design sub-skill.
- Run a small pilot before a large campaign.

## Per-Residue Secondary-Structure Run Fails Without Scaffold Directory

Cause: scaffold-guided mode without `scaffold_dir` requires at least one of the per-residue masks.

Fix:

```bash
scaffoldguided.scaffoldguided=True \
'contigmap.inpaint_str_helix=[B165-178]'
```

or use `contigmap.inpaint_str_strand` / `contigmap.inpaint_str_loop` as appropriate. If specifying loop secondary structure, also set `scaffoldguided.mask_loops=False`.

## Hydra Parsing Problems

Symptoms:

- Shell expands brackets or spaces.
- `ppi.hotspot_res` or contigs parse incorrectly.
- Chain break `/0 ` loses its required space in contig strings.

Fix:

- Wrap list-like Hydra overrides in single quotes, for example `'ppi.hotspot_res=[A59,A83,A91]'`.
- Preserve the space after `/0` inside contig strings, for example `'contigmap.contigs=[70-100/0 B1-100]'`.
- Use plain `key=value` for simple scalar overrides such as `scaffoldguided.target_pdb=True`.

## PyRosetta Or Tensor Generation Is Unavailable

This sub-skill's checker does not require PyRosetta. If the user needs to generate new tensors from PDBs:

- Use any local tensor-generation workflow that saves the expected `*_ss.pt` and `*_adj.pt` layout.
- PyRosetta is optional for higher-quality secondary-structure assignment but not mandatory for validation.
- Do not tell users to run a helper from an original source checkout path; copy or adapt a generator into their project or describe the required output format.

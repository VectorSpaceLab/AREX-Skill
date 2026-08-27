# Source Evidence Summary

This runtime reference records the repository evidence distilled into the motif-scaffolding guidance without requiring future agents to read the original checkout.

## Evidence Consulted

- README motif scaffolding section: chain-prefixed motif residues, numeric generated ranges, `/0 ` chain breaks, `contigmap.length`, and `inference.input_pdb`.
- README active-site section: very small motifs can drift with the base model; use `ActiveSite_ckpt.pt` for tiny active sites.
- README inpaint sequence section: `contigmap.inpaint_seq` masks amino-acid identities and uses an inpaint-capable model.
- README model-weight notes: checkpoint defaults are chosen from inputs; manual `inference.ckpt_override_path` should be compatible with the requested features.
- Example motif scaffolding command: `10-40/A163-181/10-40` around RSV-F site residues.
- Example inpaint sequence command: same motif with `A163-168/A170-171/A179` masked.
- Example target-aware motif command: target `A25-109/0` plus motif `B17-29`, `contigmap.length=70-120`, and `Complex_base_ckpt.pt`.
- Example enzyme command: discontinuous single-residue active-site motifs with `ActiveSite_ckpt.pt` and optional `substrate_contacts` guidance.
- `ContigMap` behavior: contigs are parsed from `contigs[0]`, whitespace separates blocks, `/0` marks receptor/chain breaks, length ranges are sampled, and incompatible length ranges exit.
- Inference config: relevant groups include `inference`, `contigmap`, `diffuser`, `ppi`, `potentials`, and `scaffoldguided`.
- Model runner behavior: `contigmap.inpaint_seq`, `contigmap.inpaint_str`, or `provide_seq` select inpaint checkpoints automatically; `ppi.hotspot_res` can select `Complex_base_ckpt.pt`; explicit `ckpt_override_path` takes precedence.

## Live Inspection Facts Used

- `ContigMap(parsed_pdb, contigs=None, inpaint_seq=None, inpaint_str=None, length=None, ref_idx=None, hal_idx=None, idx_rf=None, inpaint_seq_tensor=None, inpaint_str_tensor=None, topo=False, provide_seq=None, inpaint_str_strand=None, inpaint_str_helix=None, inpaint_str_loop=None)`.
- Distribution metadata: `rfdiffusion` version `1.1.0` with `scripts/run_inference.py` as the inference script.
- Verified import modules include `rfdiffusion.contigs`, `rfdiffusion.diffusion`, `rfdiffusion.potentials.manager`, `rfdiffusion.potentials.potentials`, `rfdiffusion.inference.symmetry`, and `rfdiffusion.inference.utils`.

## Source Script Decision

No source example script was copied. The examples are short command wrappers tied to repository-relative paths, so their safe content was distilled into portable templates using `$RFDIFFUSION_HOME`, `$MODEL_DIR`, `$INPUT_PDB`, and `$OUT_DIR`.

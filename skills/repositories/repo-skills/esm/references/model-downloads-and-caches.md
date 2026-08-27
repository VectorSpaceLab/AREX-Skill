# Model Downloads and Caches

ESM model loaders normally resolve public model names by downloading checkpoint files through PyTorch Hub when they are not already cached. Treat model loading as a network and disk operation unless the user provides local `.pt` paths or confirms a populated cache.

## Public Loader Names

Common names include:

- ESM-2: `esm2_t6_8M_UR50D`, `esm2_t12_35M_UR50D`, `esm2_t30_150M_UR50D`, `esm2_t33_650M_UR50D`, `esm2_t36_3B_UR50D`, `esm2_t48_15B_UR50D`.
- MSA Transformer: `esm_msa1b_t12_100M_UR50S`.
- ESM-1v: `esm1v_t33_650M_UR90S_1` through `_5`.
- ESM-IF1: `esm_if1_gvp4_t16_142M_UR50`.
- ESMFold: `esmfold_v1` through the ESMFold loader.

Use smaller models for smoke checks and larger models only when the user needs accuracy/capacity and the machine can support them.

## Local Checkpoints

`esm.pretrained.load_model_and_alphabet(model_location)` treats values ending in `.pt` as local files. For contact prediction with local checkpoints, keep the corresponding `<model-name>-contact-regression.pt` file next to the model checkpoint when that model expects regression weights.

## Cache Control

- Python loaders use Torch Hub cache behavior.
- The `esm-fold` CLI has `--model-dir` to set the parent path for pretrained ESM data.
- The structure-prediction helper can print commands with `--model-dir` without downloading weights.

Do not hard-code machine-specific cache locations in reusable instructions. Ask the user where model weights should live if disk quotas, shared caches, or offline execution matter.

## Network-Heavy Areas

The source repository also documents ESM Atlas resources and bulk manifests. Those are intentionally not bundled into this skill because they are network-heavy data acquisition workflows. If a user asks for Atlas bulk downloads, confirm network/disk policy and treat the manifests as external resources rather than runtime skill dependencies.

## Safe Validation Without Downloads

Use these checks before model downloads:

```bash
python scripts/check_esm_install.py
python sub-skills/model-embeddings/scripts/esm_extract_command_builder.py esm2_t6_8M_UR50D input.fasta out --include mean --print-only
python sub-skills/structure-prediction/scripts/esm_fold_command_builder.py -i input.fasta -o pdbs --print-only
```

The command builders validate syntax and paths but do not load model weights unless explicitly executed through the underlying ESM tools.

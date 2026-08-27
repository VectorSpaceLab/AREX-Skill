---
name: structure-prediction
description: "Predict protein structures from sequences or FASTA files with
  ESMFold Python APIs and the esm-fold CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Structure Prediction

Use this sub-skill when a task needs ESMFold to convert amino-acid sequences or FASTA records into PDB strings/files, including Python `infer_pdb` calls, bulk `esm-fold` command construction, chunking, recycle counts, CPU-only execution, CPU offload, and confidence interpretation.

## Start Here

- Read [references/api-reference.md](references/api-reference.md) for `esm.pretrained.esmfold_v1()`, `model.infer_pdb`, `model.infer`, `model.output_to_pdb`, `model.set_chunk_size`, devices, and PDB/confidence semantics.
- Read [references/cli-reference.md](references/cli-reference.md) for `esm-fold` flags, FASTA-to-PDB behavior, batching, cache/model directory options, and pLDDT/pTM logs.
- Read [references/workflows.md](references/workflows.md) for single-sequence Python folding, bulk FASTA folding, CPU-only dry runs, CPU offload, and multimer inputs with colon-separated chains.
- Read [references/troubleshooting.md](references/troubleshooting.md) for ESMFold optional dependencies, CUDA/OpenFold/dllogger install failures, CUDA OOM, slow CPU runs, model downloads, and invalid paths.
- Run `python scripts/esm_fold_command_builder.py --help` from this sub-skill directory to build safe printable `esm-fold` commands without loading models or running inference.

## Routing Boundaries

- Use this sub-skill for ESMFold structure prediction, `esm.pretrained.esmfold_v1()`, `esm.pretrained.esmfold_v0()`, `model.infer_pdb`, `model.infer`, `model.output_to_pdb`, `model.set_chunk_size`, the `esm-fold` console script, PDB output, pLDDT, pTM, axial-attention chunking, `--cpu-only`, and `--cpu-offload`.
- Route representation extraction, `esm-extract`, per-token/mean/BOS/contact tensors, and language-model embeddings to `../model-embeddings/SKILL.md`.
- Route fixed-backbone inverse design, coordinate-conditioned scoring, `esm.inverse_folding`, and ESM-IF1 workflows to `../inverse-folding/SKILL.md`.
- Route zero-shot mutation scoring and DMS/variant-effect workflows to `../variant-effect-prediction/SKILL.md`.
- Treat ESM Atlas web/API/bulk resources as setup alternatives only; this sub-skill does not cover Atlas API automation or bulk downloads.

## Safe Default Pattern

1. Confirm the caller wants predicted structures, not embeddings or inverse design.
2. Prefer Python `model.infer_pdb(sequence)` for one short sequence and `esm-fold -i input.fasta -o output_dir` for many records.
3. Set `model.eval()` and use `torch.no_grad()` for inference; move to CUDA only when a compatible GPU stack is available.
4. For long sequences or memory pressure, lower `--max-tokens-per-batch`, add `--chunk-size 128` or smaller, and consider fewer recycles before trying CPU offload.
5. Preserve PDB strings/files as the deliverable; use pLDDT from B-factors or `output["mean_plddt"]` and pTM logs as confidence signals, not as sequence embeddings.

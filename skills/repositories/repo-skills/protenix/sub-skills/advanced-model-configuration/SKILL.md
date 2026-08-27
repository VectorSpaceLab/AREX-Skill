---
name: advanced-model-configuration
description: "Inspect and troubleshoot Protenix configs, model internals, kernel
  backends, TFG guidance, confidence utilities, metrics, and safe runtime
  fallbacks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Protenix Advanced Model Configuration

Use this sub-skill for expert Protenix internals work: configuration parsing, model-type defaults, optional CUDA/Triton/cuEquivariance/DeepSpeed paths, conservative backend fallbacks, Training-Free Guidance (TFG), confidence post-processing, and direct metrics calls.

## Start Here

1. Run `python scripts/protenix_runtime_doctor.py --json` for a read-only report of package metadata, PyTorch/CUDA, optional backend imports, relevant environment switches, CLI availability, and external tool availability.
2. Read `references/config-api.md` before using `parse_configs`, saving configs, composing dotted overrides, or comparing model-name-specific defaults.
3. Read `references/kernels-and-backends.md` before changing `LAYERNORM_TYPE`, `triangle_attention`, `triangle_multiplicative`, `--triatt_kernel`, `--trimul_kernel`, TF32, cache, fusion, dtype, cuEquivariance, Triton, or DeepSpeed behavior.
4. Read `references/tfg-confidence-and-metrics.md` before enabling TFG, editing potential terms, calling confidence helpers, interpreting pTM/gPDE/PAE outputs, or using RMSD/LDDT metrics directly.
5. Read `references/troubleshooting.md` when optional dependency imports, CUDA visibility, ABI mismatches, kernel-image failures, config overrides, TFG feature validation, or metric tensor shapes fail.

## Bundled Tool

- `scripts/protenix_runtime_doctor.py`: read-only runtime checker with text and `--json` output. It does not run kernels, compile extensions intentionally, download checkpoints, run inference, run training, or inspect local source paths.
- Add `--include-model-imports` only when import probing is the goal; model-module imports may trigger fast layer norm behavior unless `LAYERNORM_TYPE=torch` is already set.

## Route Elsewhere

- Routine prediction command assembly, checkpoint/cache download behavior, output folders, and CLI inference workflows belong to `../cli-and-inference/SKILL.md`.
- Protenix input JSON authoring, ligands, bonds, constraints, seed fields, and feature-file paths belong to `../input-data-and-features/SKILL.md`.
- Training data preparation, database layout, fine-tuning launches, optimizer/scheduler usage, and distributed training belong to `../training-and-data-pipeline/SKILL.md`.

## Safety Rules

- Prefer reversible runtime/config overrides before code changes: `triangle_attention="torch"`, `triangle_multiplicative="torch"`, `--triatt_kernel torch`, `--trimul_kernel torch`, and `LAYERNORM_TYPE=torch` are the first isolation path.
- Set `LAYERNORM_TYPE=torch` before importing model modules when the task is config inspection, CPU debugging, tensor-shape debugging, or fallback triage rather than proving the fused layer norm extension works.
- Treat cuEquivariance, Triton, and DeepSpeed as optional acceleration paths. Do not promise they work on every GPU or ABI combination; verify imports, CUDA visibility, and selected config values first.
- Treat TFG, confidence, and metrics symbols as current implementation entry points for expert debugging, not as a stable public API contract.

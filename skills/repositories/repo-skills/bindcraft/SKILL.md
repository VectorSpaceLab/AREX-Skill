---
name: bindcraft
description: "Guide CUDA-enabled BindCraft protein-binder design from target PDB
  preparation through AF2/MPNN/PyRosetta execution, filtering, output analysis,
  and conservative troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BindCraft

BindCraft is a GPU-first de-novo protein-binder design pipeline that combines
AlphaFold2 backpropagation, ProteinMPNN sequence redesign, AF2 complex/monomer
validation, and PyRosetta relaxation and interface scoring. Use this skill to
plan and operate a reproducible campaign; do not treat it as a generic CPU
protein-design library.

## Route the request

- **Prepare or repair a target PDB and target JSON:** read
  [target-preparation](sub-skills/target-preparation/SKILL.md). It covers chain
  selection, hotspot syntax, binder lengths, and safe validation.
- **Install prerequisites, choose presets, build a launch, run or resume a
  campaign:** read [design-pipeline](sub-skills/design-pipeline/SKILL.md).
  It owns CUDA/JAX, AF2-weight, MPNN, PyRosetta, direct, and SLURM decisions.
- **Inspect results, rejection causes, scores, and ranked binders:** read
  [results-analysis](sub-skills/results-analysis/SKILL.md). It owns output
  reconciliation and conservative metric interpretation.

Before using any route, read [installation](references/installation.md) for
external prerequisites and licensing, [configuration](references/configuration.md)
for the three JSON families, and [troubleshooting](references/troubleshooting.md)
for cross-cutting failures. Read [repo-provenance](references/repo-provenance.md)
when checking whether this graph matches a repository revision.

## Minimal operating contract

1. Work on Linux with Python 3.10 and an NVIDIA GPU. The main design path
   requires a CUDA-visible JAX runtime; a CPU import is not a valid substitute.
2. Obtain the AlphaFold2 parameter bundle, configure its directory, and ensure
   DSSP and DAlphaBall are readable/executable. BindCraft's installer downloads
   large external artifacts; review and run setup commands manually rather than
   blindly executing a bundled installer.
3. Install ColabDesign and PyRosetta in a private, compatible environment.
   PyRosetta may have commercial-license restrictions; resolve those before a
   production run.
4. Validate the target JSON and PDB, then use the design route's command builder
   to print a direct or SLURM command. The builder never executes or submits.
5. Use a distinct writable `design_path` per campaign. Expect hundreds or
   thousands of target-dependent trajectories for difficult targets; monitor
   GPU memory, disk use, `failure_csv.csv`, and acceptance rate.
6. Rank and select candidates from recorded artifacts, not from confidence
   metrics alone. BindCraft documents `Average_i_pTM` as a useful binding
   binary/ranking signal, not an affinity measurement.

## Safe helpers

- From the generated skill root, `python scripts/check_bindcraft_env.py` reports
  import/backend/asset readiness and never installs, downloads, or launches a
  design.
- From the generated skill root, `python scripts/validate_bindcraft_config.py`
  checks the target, filter, and advanced JSON contracts without editing them.
- The focused routes link additional read-only target and results helpers. All
  paths in examples are placeholders that must be replaced on the launch host.

## Non-goals and stop conditions

This graph does not download AF2 weights, submit SLURM jobs, run a full design
campaign, promise a binder, or infer experimental affinity. Stop and repair the
specific prerequisite when CUDA/JAX, ColabDesign, PyRosetta, AF2 weights, DSSP,
DAlphaBall, PDB chains, settings, output permissions, or disk/VRAM capacity are
not verified. A successful JSON/PDB check or generated command is not evidence
that the GPU design loop will complete.

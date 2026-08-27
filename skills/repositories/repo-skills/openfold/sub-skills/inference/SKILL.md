---
name: inference
description: "Plan and validate OpenFold monomer, multimer, SoloSeq,
  precomputed-alignment, custom-template, threading, output, relaxation, and
  acceleration inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFold Inference

Use this sub-skill when the task is to plan, validate, or explain OpenFold prediction commands. It covers `run_pretrained_openfold.py` for monomer, multimer, SoloSeq/single-sequence, precomputed-alignment, custom-template, long-sequence, output, relaxation, and acceleration planning, plus `thread_sequence.py` for threading one sequence onto one template mmCIF.

## Route Quickly

- Read `references/cli-reference.md` for positional arguments, flags, presets, database/tool differences, output flags, and command patterns.
- Read `references/inference-workflows.md` for mode selection and workflows for monomer, multimer, SoloSeq, precomputed alignments, custom templates, long sequences, and threading.
- Read `references/troubleshooting.md` when inference fails because of missing extensions, weights, databases, binaries, precomputed layouts, template mismatches, SoloSeq length, acceleration dependencies, or relaxation.
- Use `scripts/build_inference_command.py` to build dry-run commands for monomer, multimer, SoloSeq, and threading without importing OpenFold or executing inference.
- Use `scripts/validate_inference_inputs.py` to inspect FASTA files, template mmCIF directories, precomputed alignment or embedding layouts, SoloSeq length limits, threading inputs, and optional checkpoint paths.

## Boundaries

- Route OpenFold installation, CUDA/PyTorch/OpenMM, parameters, sequence databases, external binaries, and optional backend readiness to `../installation-assets/`.
- Route alignment/database/cache production and deep alignment layout conversion to `../data-preparation/`.
- Route low-level config internals, model APIs, checkpoint conversion, tensor shapes, and acceleration implementation details to `../model-apis/`.
- Route training, fine-tuning, Lightning, and DeepSpeed training commands to `../training/`.

## Verified OpenFold Facts

- `run_pretrained_openfold.py` takes required positionals `fasta_dir` and `template_mmcif_dir`, writes under `--output_dir`, and accepts `--use_precomputed_alignments` to skip alignment generation.
- Monomer inference uses HHSearch/PDB70 for template search; multimer inference uses presets such as `model_1_multimer_v3` and PDB SeqRes with HMMSearch/HMBuild plus UniProt and UniRef30 inputs.
- SoloSeq uses `seq_model_esm1b_ptm`, ESM-1b embeddings, a SoloSeq OpenFold checkpoint, optional HHSearch template hits, and a 1022-residue sequence limit.
- `thread_sequence.py` accepts one FASTA file and one template mmCIF file, expects exactly one query sequence, and uses `--template_id` plus `--chain_id` to select the template chain.
- Current CLI help may fail in incomplete environments if the `attn_core_inplace_cuda` extension is missing; the bundled helper scripts avoid OpenFold imports and should still work.

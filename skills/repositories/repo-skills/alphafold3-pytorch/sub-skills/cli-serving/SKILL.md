---
name: cli-serving
description: "Operate the alphafold3_pytorch CLI and alphafold3_pytorch_app
  Gradio entry points, construct safe multimolecule commands, and diagnose
  checkpoint, device, output, entity, cache, and precision behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI and local serving

Use this sub-skill when the task is to plan or operate the package's two
console entry points, construct a command without executing it, or explain the
local Gradio application's entity and cache lifecycle.

## Route first

- For checkpoint format, model construction, `init_and_load`, tensor shapes, or
  inference internals, use [model-inference](../model-inference/SKILL.md).
- For sequence-to-`Alphafold3Input` semantics, ligand chemistry, ion handling,
  or output structure conversion, use
  [input-representation](../input-representation/SKILL.md).
- Do not treat this sub-skill as a production deployment or public-server
  hardening guide; the app launches a local Gradio UI with its own defaults.

## Operating path

1. Confirm that the target checkpoint is an existing regular file and that the
   package entry point is available.
2. Choose the plain CLI for a non-interactive run. Repeat `--protein`, `--rna`,
   and `--dna` once per entity; pass Click's boolean value explicitly when
   using `--use-cuda`.
3. Build and inspect a command with
   [`build_cli_command.py`](scripts/build_cli_command.py). The helper validates
   inputs and prints only a shell-quoted command; it never imports the package,
   runs inference, creates output directories, or launches Gradio.
4. Use the app only when an interactive local UI is wanted. Treat its cache
   directory as disposable because startup removes the whole directory before
   creating it again.
5. Use the bundled references for exact flags, entity normalization, output
   formats, CUDA fallback, cache/session cleanup, and the precision limitation.

The CLI writes a structure as mmCIF. The app writes per-session PDB files for
its molecule viewer. Neither entry point supplies a dry-run inference mode.
The app's `--precision` argument is accepted for compatibility/documentation,
but the current executable code does not convert model device or dtype; do not
claim that it enables mixed precision, quantization, or CUDA.

## Bundled material

- [CLI reference](references/cli-reference.md) — exact entry points, flags,
  Click syntax, repeated entities, and output behavior.
- [Serving workflow](references/serving-workflow.md) — safe preflight,
  non-interactive command construction, app lifecycle, and synthetic cases.
- [Troubleshooting](references/troubleshooting.md) — checkpoint, input,
  device, path, cache, UI normalization, and precision failure recovery.
- [Safe command builder](scripts/build_cli_command.py) — validates a command
  specification and prints a shell-safe command without running it.

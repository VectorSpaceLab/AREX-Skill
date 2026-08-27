---
name: tools-and-demos
description: "Routes detrex demo, analysis, visualization, benchmark planning,
  and MOT demo cautions safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# tools-and-demos

Use this sub-skill when you need to build or choose a safe command for:

- image, video, or webcam demo runs
- model analysis such as FLOPs, activations, parameters, or structure
- dataset or prediction visualization
- benchmark command construction without execution
- project-specific MOT demo cautions and routing

Do not use this sub-skill for:

- training or evaluation launchers
- model zoo selection or checkpoint conversion
- package installation or CUDA extension repair

## Read first

- `references/tools-reference.md` for the CLI surface and input/output rules.
- `references/demo-workflows.md` for workflow selection and command-building choices.
- `references/troubleshooting.md` for checkpoint, codec, dataset, and dependency failures.
- `scripts/build_tool_command.py` for a safe command plan with no execution.

## Skill-owned script

- `scripts/build_tool_command.py` — prints a shell command or JSON plan for demo, analysis, visualization, or benchmark workflows. It does not download weights, scan datasets, or run a benchmark by itself.

## Typical workflow

1. Pick the workflow and confirm whether you want a command plan or a runnable command.
2. Use the bundled command builder to assemble explicit config, checkpoint, input, and output arguments.
3. Check the workflow notes for checkpoint responsibility, output handling, and MOT cautions.
4. Run the printed command only after the required files and dataset registration are ready.

## Routing notes

- Use the generic demo route for independent images or videos.
- Use the visualization routes for dataset inspection or saved prediction JSON.
- Use the analysis route when you need parameters, FLOPs, activations, or a structure summary.
- Treat MOT paths as project-specific and sequence-dependent; do not feed unrelated still images to a tracking workflow.
- If you only need to plan a command, stop at the helper output and do not run the underlying tool.

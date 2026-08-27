---
name: game24
description: "Routes Game of 24 workflows for arithmetic puzzle solving with
  Tree of Thoughts BFS and naive sampling baselines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Game24

Use this sub-skill when the user wants to solve or reproduce the paper's
arithmetic puzzle workflow for the 24 game.

## Covers

- `task=game24` runs.
- Naive `standard` and `cot` sampling baselines.
- The paper-style BFS path using `propose` generation and `value`
  evaluation.
- Final-answer validation through the `Game24Task.test_output` rules.

## Excludes

- Coherent passage generation; use `sub-skills/text/`.
- Mini crossword solving; use `sub-skills/crosswords/`.
- New task authoring; see the shared `references/workflows.md` notes.

## Read and run

- `references/workflows.md` for the data file, prompt families, and the
  recommended BFS settings.
- `references/troubleshooting.md` for malformed answers, parser drift, and
  score-format problems.
- `scripts/run_game24.sh` for the bundled command wrapper.

## Quick command shapes

- BFS: `bash sub-skills/game24/scripts/run_game24.sh bfs`
- Naive standard: `bash sub-skills/game24/scripts/run_game24.sh standard`
- Naive CoT: `bash sub-skills/game24/scripts/run_game24.sh cot`

## Acceptance cues

A future agent should be able to:

- explain why the final answer must use every input number exactly once;
- choose between naive sampling and BFS with the right flags;
- inspect or adapt the `value` prompt when the frontier ranking is poor;
- interpret a `r=0` result as a formatting or arithmetic failure, not a
  package-install failure.

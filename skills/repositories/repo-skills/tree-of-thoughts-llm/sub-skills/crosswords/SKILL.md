---
name: crosswords
description: "Routes 5x5 mini crossword workflows for Tree of Thoughts sampling,
  BFS, and DFS search over clue grids."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Crosswords

Use this sub-skill when the user wants to solve or inspect the 5x5 mini
crossword workflow.

## Covers

- `task=crosswords` runs.
- Naive `standard` and `cot` sampling baselines.
- The paper-style BFS path with proposal generation and value checks.
- The notebook-derived DFS search workflow.
- `MiniCrosswordsTask` / `MiniCrosswordsEnv` state handling and validation.

## Excludes

- Arithmetic puzzle solving; use `sub-skills/game24/`.
- Text passage generation; use `sub-skills/text/`.
- New task authoring; see the shared `references/workflows.md` notes.

## Read and run

- `references/workflows.md` for the board format, DFS helper, and sample
  command shapes.
- `references/troubleshooting.md` for invalid actions, row parsing, and DFS
  pruning problems.
- `scripts/run_crosswords.sh` for the bundled wrapper that dispatches to
  sampling or DFS mode.

## Quick command shapes

- BFS-style sampling: `bash sub-skills/crosswords/scripts/run_crosswords.sh bfs`
- Naive standard: `bash sub-skills/crosswords/scripts/run_crosswords.sh standard`
- Naive CoT: `bash sub-skills/crosswords/scripts/run_crosswords.sh cot`
- DFS search: `bash sub-skills/crosswords/scripts/run_crosswords.sh dfs`

## Acceptance cues

A future agent should be able to:

- distinguish the board state from the clue/answer state;
- explain why a candidate must be exactly five letters;
- choose DFS pruning only when the status counts still allow a viable path;
- tell whether a failed output is a parsing issue or a crossword-logic issue.

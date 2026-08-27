---
name: text
description: "Routes coherent passage generation workflows for the Tree of
  Thoughts text task, including sample/vote BFS and scoring helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Text

Use this sub-skill when the user wants to generate coherent passages or
replay the paper's text workflow.

## Covers

- `task=text` runs.
- BFS with `sample` generation and `vote` evaluation.
- Naive `standard` and `cot` passage sampling.
- The GPT-4-based coherency scoring helpers used by `TextTask.test_output`.

## Excludes

- Arithmetic puzzle solving; use `sub-skills/game24/`.
- Mini crossword solving; use `sub-skills/crosswords/`.
- General package installation; use the root skill.

## Read and run

- `references/workflows.md` for the text data file, prompt families, and
  the sample/vote settings.
- `references/troubleshooting.md` for score-format drift and vote parser
  issues.
- `scripts/run_text.sh` for the bundled command wrapper.

## Quick command shapes

- BFS: `bash sub-skills/text/scripts/run_text.sh bfs`
- Naive standard: `bash sub-skills/text/scripts/run_text.sh standard`
- Naive CoT: `bash sub-skills/text/scripts/run_text.sh cot`

## Acceptance cues

A future agent should be able to:

- explain why the BFS path uses `sample` + `vote` rather than `propose` +
  `value`;
- tell when the final coherency score comes from the GPT-4 judge path;
- tune the sample counts when the passage quality or vote stability is low;
- interpret the returned `rs` and `r` fields from the scorer.

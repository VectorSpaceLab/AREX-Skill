# Crosswords Workflows

## Task shape

- Packaged input file: `mini0505.json` from the crossword data bundle
- Input format: 5 horizontal clues and 5 vertical clues describing a 5x5
  mini crossword.
- Output format: five rows of five letters separated by spaces.
- Validation: `MiniCrosswordsTask.test_output` replays the five rows into
  the environment and reports row/letter/game scores.

## Recommended commands

```bash
bash sub-skills/crosswords/scripts/run_crosswords.sh bfs
bash sub-skills/crosswords/scripts/run_crosswords.sh standard
bash sub-skills/crosswords/scripts/run_crosswords.sh cot
bash sub-skills/crosswords/scripts/run_crosswords.sh dfs
```

The sampling modes dispatch into the bundled `scripts/run_tot.py` helper.
The DFS mode dispatches to `sub-skills/crosswords/scripts/dfs_search.py`,
which is adapted from the notebook-derived DFS workflow.

## Prompt families

- `standard_prompt_wrap` asks for a direct five-row crossword fill.
- `cot_prompt_wrap` asks for thoughts before the final board.
- `propose_prompt_wrap` shows the current board and asks for candidate
  words with confidence labels.
- `propose_outputs_unwrap` accepts lines like `h1. apple (medium)`.

## DFS helper notes

The DFS helper mirrors the notebook logic:

- get candidate moves from `propose_prompt`;
- score them with confidence weights;
- keep the board consistent with `MiniCrosswordsEnv.step`;
- optionally prune when the current status counts mark a word as impossible.

## When to use this file

Read this file when the user wants to replay the crossword experiments,
debug the state machine, or adapt the notebook-derived search into a CLI script.

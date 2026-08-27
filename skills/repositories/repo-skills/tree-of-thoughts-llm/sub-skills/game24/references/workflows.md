# Game24 Workflows

## Task shape

- Packaged input file: `24.csv` from the Game24 data bundle
- Input format: four integers separated by spaces.
- Output format: three intermediate arithmetic steps followed by a final
  `Answer: ... = 24` line.
- Validation: `Game24Task.test_output` checks that the final expression uses
  the same numbers exactly once and simplifies to 24.

## Recommended commands

```bash
bash sub-skills/game24/scripts/run_game24.sh bfs
bash sub-skills/game24/scripts/run_game24.sh standard
bash sub-skills/game24/scripts/run_game24.sh cot
```

The wrapper dispatches into the bundled `scripts/run_tot.py` helper with
the paper's typical settings:

- BFS: `--method_generate propose --method_evaluate value --method_select greedy --n_evaluate_sample 3 --n_select_sample 5`
- Naive standard: `--naive_run --prompt_sample standard --n_generate_sample 100`
- Naive CoT: `--naive_run --prompt_sample cot --n_generate_sample 100`

## Prompt families

- `standard_prompt_wrap` asks for a direct arithmetic solution.
- `cot_prompt_wrap` asks for step-by-step reasoning and a final equation.
- `propose_prompt_wrap` narrows the search to the current remaining numbers.
- `value_prompt_wrap` asks whether the current numbers can still reach 24.

## Output scoring

The value path unwraps the labels `impossible`, `likely`, and `sure` into a
numeric ranking. If the frontier looks flat, increase `n_evaluate_sample`
before changing the task logic.

## When to use this file

Read this file when the user wants to replay the paper's Game24 result,
tune the BFS settings, or adapt the arithmetic prompt family to a nearby
puzzle.

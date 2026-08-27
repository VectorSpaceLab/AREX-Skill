# Text Workflows

## Task shape

- Packaged input file: `data_100_random_text.txt` from the text data bundle
- Input format: one instruction per line.
- Output format: a coherent passage, optionally with a `Plan:` section in
  the CoT path and a `Passage:` section before the final passage.
- Validation: `TextTask.test_output` scores the passage with the GPT-4
  coherency judge and returns a mean score.

## Recommended commands

```bash
bash sub-skills/text/scripts/run_text.sh bfs
bash sub-skills/text/scripts/run_text.sh standard
bash sub-skills/text/scripts/run_text.sh cot
```

The wrapper dispatches into the bundled `scripts/run_tot.py` helper with
the paper's typical settings:

- BFS: `--method_generate sample --method_evaluate vote --method_select greedy --n_generate_sample 5 --n_evaluate_sample 5 --n_select_sample 1 --prompt_sample cot --temperature 1.0`
- Naive standard: `--naive_run --prompt_sample standard --n_generate_sample 10 --temperature 1.0`
- Naive CoT: `--naive_run --prompt_sample cot --n_generate_sample 10 --temperature 1.0`

## Prompt families

- `standard_prompt_wrap` asks for a direct four-paragraph passage.
- `cot_prompt_wrap` asks for a brief plan followed by the passage.
- `vote_prompt_wrap` ranks several candidate passages.
- `compare_prompt_wrap` and `compare_output_unwrap` support pairwise
  coherency checks.

## Output scoring

`TextTask.test_output` uses `score_prompt` and a GPT-4 judge prompt to
assign a coherency score from 1 to 10. That means the evaluation step may
cost additional API calls even after the passage itself is generated.

## When to use this file

Read this file when the user wants to replay the text experiment, adjust
vote/sample counts, or debug coherency-scoring output.

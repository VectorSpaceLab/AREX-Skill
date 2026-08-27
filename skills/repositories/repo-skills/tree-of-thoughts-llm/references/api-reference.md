# API Reference

This repository is small enough that the most useful public surface is the
installed `tot` package plus the bundled runner script.

## Model helpers

| API | Signature | Notes |
| --- | --- | --- |
| `tot.models.gpt` | `gpt(prompt, model='gpt-4', temperature=0.7, max_tokens=1000, n=1, stop=None) -> list` | Wraps a single user message into `openai.ChatCompletion.create`. Returns a list of text completions. |
| `tot.models.chatgpt` | `chatgpt(messages, model='gpt-4', temperature=0.7, max_tokens=1000, n=1, stop=None) -> list` | Low-level chat completion helper used by `gpt`. |
| `tot.models.gpt_usage` | `gpt_usage(backend='gpt-4')` | Returns token counters and an estimated cost by backend name. |
| `tot.models.completions_with_backoff` | `completions_with_backoff(**kwargs)` | Backoff wrapper around the OpenAI chat completion call. |

## Search helpers

| API | Signature | Notes |
| --- | --- | --- |
| `tot.methods.bfs.solve` | `solve(args, task, idx, to_print=True)` | Runs Tree of Thoughts BFS over the chosen task. It expands proposals or samples, scores candidates, selects the next frontier, and returns `(ys, info)`. |
| `tot.methods.bfs.naive_solve` | `naive_solve(args, task, idx, to_print=True)` | Runs the naive IO/CoT sampling path instead of BFS. |
| `tot.methods.bfs.get_value` | `get_value(task, x, y, n_evaluate_sample, cache_value=True)` | Scores a single partial state. |
| `tot.methods.bfs.get_values` | `get_values(task, x, ys, n_evaluate_sample, cache_value=True)` | Scores a list of partial states, de-duplicating repeated candidates locally. |
| `tot.methods.bfs.get_votes` | `get_votes(task, x, ys, n_evaluate_sample)` | Calls the task vote prompt and unwraps the result into candidate votes. |
| `tot.methods.bfs.get_proposals` | `get_proposals(task, x, y)` | Generates next-step thoughts by calling the task propose prompt. |
| `tot.methods.bfs.get_samples` | `get_samples(task, x, y, n_generate_sample, prompt_sample, stop)` | Generates sampled continuations from the task standard or CoT prompt. |

## Task factory

| API | Signature | Notes |
| --- | --- | --- |
| `tot.tasks.get_task` | `get_task(name)` | Returns `Game24Task`, `TextTask`, or `MiniCrosswordsTask` for `game24`, `text`, or `crosswords`. |

## Task classes

### `Game24Task`

- Constructor: `Game24Task(file='24.csv')`
- Packaged data: default file `24.csv` in the Game24 data bundle
- `steps = 4`
- `stops = ['
'] * 4`
- `test_output(idx, output)` returns `{'r': 0}` or `{'r': 1}`.
- Prompt helpers: `standard_prompt_wrap`, `cot_prompt_wrap`, `propose_prompt_wrap`, `value_prompt_wrap`, `value_outputs_unwrap`.
- Final answers must use each input number exactly once and simplify to 24.

### `TextTask`

- Constructor: `TextTask(file='data_100_random_text.txt')`
- Packaged data: default file `data_100_random_text.txt` in the text data bundle
- `steps = 2`
- `stops = ['
Passage:
', None]`
- `test_output(idx, output)` returns a dict with `rs` for the raw scores and `r` for the mean coherency score.
- Prompt helpers: `standard_prompt_wrap`, `cot_prompt_wrap`, `vote_prompt_wrap`, `vote_outputs_unwrap`, `compare_prompt_wrap`, `compare_output_unwrap`.
- `TextTask.test_output` calls `tot.models.gpt` with `model='gpt-4'` to score the passage, so it may incur extra API cost.

### `MiniCrosswordsTask` and `MiniCrosswordsEnv`

- Constructors: `MiniCrosswordsTask(file='mini0505.json')`, `MiniCrosswordsEnv(file='mini0505.json')`
- Packaged data: default file `mini0505.json` in the crossword data bundle
- `MiniCrosswordsTask.steps = 10`
- `MiniCrosswordsTask.test_output(idx, output)` parses the last five output lines after `Output:
` as rows of the crossword.
- `MiniCrosswordsTask.propose_outputs_unwrap` expects lines like `h1. apple (medium)` or `v3. panel (high)`.
- `MiniCrosswordsTask.evaluate(x, y, n_evaluate_sample)` returns the same sure/maybe/impossible-style counts used by the notebook DFS path.
- `MiniCrosswordsEnv.reset(idx, board=None, status=None, steps=None)` initializes a board state.
- `MiniCrosswordsEnv.step(action)` expects actions like `h1. apple` or `v3. panel` and returns `(rendered_state, reward, done, info)`.

## Runtime notes

- Importing `tot.models` without `OPENAI_API_KEY` prints a warning, but the package still imports.
- The installed package exposes no console entry point; use the bundled runner script instead.
- The generated helpers call the installed `tot` package; use a PyPI install for a checkout-independent runtime or an editable install only when working inside a repository checkout.

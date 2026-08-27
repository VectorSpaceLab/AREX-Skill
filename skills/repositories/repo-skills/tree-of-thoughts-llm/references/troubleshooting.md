# Troubleshooting

## Install and import problems

### `ModuleNotFoundError: No module named 'tot'`

Likely cause: the package was not installed into the active environment.

Recovery:

- Reinstall with `pip install -e .` from a checkout or `pip install tree-of-thoughts-llm` from PyPI.
- Re-run `python scripts/check_install.py`.

### Dependency conflicts during install

Likely cause: a stale environment with incompatible pinned versions.

Recovery:

- Create a fresh environment instead of mutating an old one.
- Keep the install pinned to the repository's `requirements.txt` versions.

## API key and endpoint problems

### `Warning: OPENAI_API_KEY is not set`

Likely cause: the environment does not provide the key expected by `tot.models`.

Recovery:

- Set `OPENAI_API_KEY` before running any task mode.
- If you use a proxy or compatible endpoint, also set `OPENAI_API_BASE`.

### OpenAI auth, rate-limit, or network errors

Likely cause: invalid credentials, quota exhaustion, or no access to the chosen backend.

Recovery:

- Confirm the key is valid and has model access.
- Lower `n_generate_sample`, `n_evaluate_sample`, or the dataset slice.
- Retry with a lower-cost backend such as `gpt-3.5-turbo` or `gpt-4o` when appropriate.

## Data and task selection problems

### `FileNotFoundError` for task data

Likely cause: the package was not installed with its bundled data files or the active environment is wrong.

Recovery:

- Reinstall the package in the active environment and rerun the smoke check.
- Confirm the task constructors work with `python scripts/check_install.py`.

### `argument --task: invalid choice`

Likely cause: the runner only accepts the three bundled tasks.

Recovery:

- Use `game24`, `text`, or `crosswords`.
- Add a new `Task` subclass and prompt family if you need another mode.

## Output parsing problems

### Game24 returns `r=0` unexpectedly

Likely cause: the final answer does not use each input number exactly once, uses the wrong arithmetic, or does not simplify to 24.

Recovery:

- Make sure the last line looks like `Answer: ... = 24`.
- Keep the three intermediate steps consistent with the chosen numbers.

### Text scoring returns empty or zero scores

Likely cause: the judge output did not end with `Thus the coherency score is N`.

Recovery:

- Keep the output format stable.
- Reduce sampling temperature if the parser drifts.

### Crossword proposals are ignored

Likely cause: the model did not emit lines like `h1. apple (medium)` or the row length is not five letters.

Recovery:

- Use the exact `h1`/`v1` notation.
- Ensure each candidate word is five letters.

## Cross-cutting fallback

When a workflow becomes noisy or expensive, try a smaller dataset slice, a lower
sampling count, or the naive path before assuming the package is broken.

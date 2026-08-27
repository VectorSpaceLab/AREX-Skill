# Reward Functions

## How GRPO discovers rewards

The training script imports `train.reward_funcs` and keeps callables whose names end with `_reward`.

## Built-in examples

- `accuracy_reward(completions, assistant, **kwargs)`
  - compares the generated answer against the solution text
  - falls back to a string match when symbolic parsing packages are unavailable
- `format_reward(completions, **kwargs)`
  - checks for the `<think>...</think><answer>...</answer>` shape used in the repo docs

## Good reward-function habits

- Keep reward functions small and deterministic.
- Return a list of floats, one per completion.
- Make the failure mode obvious if an optional package is missing.
- Keep any domain-specific parsing close to the reward function so it remains easy to inspect.

## When to extend

Add a new reward only when the user’s task really needs a domain-specific signal. Otherwise, use the built-in examples or keep the workflow in DPO.

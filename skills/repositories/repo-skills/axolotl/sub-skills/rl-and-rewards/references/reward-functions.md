# Reward Functions and Safe Validation

Axolotl GRPO reward functions must be importable from the directory where `axolotl train` runs. The YAML uses fully qualified names such as `rewards.accuracy_reward` or integration-provided reward functions.

## Interface Expectations

Use reward functions that accept batched prompts/completions and return one score per completion:

```python
def accuracy_reward(completions, answer=None, **kwargs) -> list[float]:
    scores = []
    for completion, gold in zip(completions, answer, strict=True):
        text = completion[0]["content"]
        scores.append(1.0 if str(gold) in text else 0.0)
    return scores
```

Some integration paths and older helpers pass `prompts` as a first argument:

```python
def reward_with_prompts(prompts, completions, **kwargs) -> list[float]:
    return [0.0 for _ in completions]
```

Keep functions tolerant of keyword arguments because dataset columns that survive the transform are passed through for scoring. If the reward needs `answer`, `unit_tests`, or metadata, do not remove that column in the dataset transform.

Valid return values:

- A `list` or `tuple` with exactly one element per completion.
- Each element is a finite `int` or `float`; `None` can be used only when the intended trainer path supports excluding individual samples from aggregation.
- No scalar return for a batch, no nested arrays, no strings, no booleans, no NaN or infinity.

## Validate Before Training

Run the bundled local-only helper against a reward file before using it in YAML:

```bash
python scripts/validate_reward_function.py rewards.py:accuracy_reward
python scripts/validate_reward_function.py rewards.py:accuracy_reward --completion-style strings
python scripts/validate_reward_function.py rewards.py:accuracy_reward --extra-json '{"difficulty": ["easy", "hard"]}'
```

The helper imports one local Python file, calls the selected function on two tiny completions, checks return type and length, checks numeric finiteness, and calls the function twice to catch obvious nondeterminism. It does not import Axolotl, load models, download data, train, or write outputs.

If the helper reports nondeterminism, remove uncontrolled `random`, wall-clock time, global mutable counters, network calls, or filesystem-dependent state from the reward. Deterministic rewards make reward variance meaningful; random rewards can create unstable advantages without task signal.

## Multiple Rewards

Combine rewards with weights when the task needs both correctness and format shaping:

```yaml
trl:
  reward_funcs:
    - rewards.accuracy_reward
    - rewards.format_reward
    - rewards.length_penalty
  reward_weights:
    - 1.0
    - 0.5
    - 0.1
```

Guidelines:

- Put the objective reward first and use auxiliary rewards as shaping signals.
- Keep reward scales compatible or use `multi_objective_aggregation: normalize_then_sum` for GDPO-style independent normalization.
- Log individual reward means when possible so a high auxiliary reward does not hide a broken correctness reward.
- Make reward outputs vary within each prompt group; if every completion receives the same score, GRPO has zero advantage signal.

## Dataset Transform Contract

A GRPO transform commonly returns chat prompts and preserved answer fields:

```python
def transform(cfg, *args, **kwargs):
    def transform_fn(example, tokenizer=None):
        return {
            "prompt": [
                {"role": "user", "content": example["question"]},
            ],
            "answer": example["answer"],
        }
    return transform_fn, {"remove_columns": ["question"]}
```

Do not remove columns consumed by rewards. Do remove large unused strings, raw traces, or metadata that should not reach the trainer.

## Reward Models and Rollout Functions

`trl.reward_funcs` can also point to reward model identifiers or local reward model directories when the installed stack supports that path. Treat this as a model-loading runtime path; it is not validated by the safe helper.

`trl.rollout_func` accepts an importable custom rollout function. Use it only for environment-style flows where generation is not the standard vLLM completion loop. Invalid rollout imports should fail early with a clear "not found" or "must be callable" style error.

## NeMo Gym Rewards

For NeMo Gym, prefer the integration reward functions instead of writing wrappers:

```yaml
trl:
  reward_funcs:
    - axolotl.integrations.nemo_gym.rewards.reward_nemo_gym_verify
```

Use `reward_env` when the multi-turn data producer already computed environment rewards:

```yaml
trl:
  reward_funcs:
    - axolotl.integrations.nemo_gym.rewards.reward_env
```

Multi-environment data can route per row through an `agent_ref` or through the `nemo_gym_datasets` entries. Tool schemas for agent environments should be strict and deterministic so rewards reflect task success rather than parser ambiguity.

## Hatchery Reward Hooks

Hatchery-style RL exposes reward function names in the nested `hatchery.reward_funcs` list. Keep those functions importable in the runtime working directory, deterministic, and free of secrets. Remote backend connection details belong in user configs or environment variables, not in reusable skill content.

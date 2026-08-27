# Action Masking

Action masks tell policies which discrete actions are valid in the current state. They are most useful for board games, grid movement, card games, and any environment where some actions are illegal only at certain times.

## Supported Schemas

Use one of these schemas consistently.

### Observation Dictionary Mask

Return each observation as a dictionary with the true observation and a mask:

```text
{
  "observation": <space-matching observation>,
  "action_mask": <1D integer array of 0/1 values>
}
```

Declare the observation space as a `spaces.Dict` with matching keys. The action mask length should equal the number of discrete actions.

### Info Dictionary Mask

Keep the observation unchanged and put the mask in `infos[agent]["action_mask"]`. This is useful when a downstream wrapper or training library expects masks in info rather than in the observation object.

Whichever schema you choose, make it available after `reset()` and after every `step()` for every agent that is expected to act next.

## Mask Shape And Dtype

For a `Discrete(n)` action space:

- Shape: `(n,)`.
- Values: `1` for valid actions and `0` for invalid actions.
- Dtype: an integer or boolean dtype; `np.int8` is a portable default.
- At least one action should be valid whenever the agent is expected to choose an action.

For non-discrete action spaces, action masking is library-specific. Prefer redesigning the action space into a discrete choice set before relying on masks.

## Sampling With Masks

A safe random policy should sample only valid actions:

```python
mask = observation.get("action_mask") if isinstance(observation, dict) else info.get("action_mask")
valid_actions = np.flatnonzero(mask)
action = int(rng.choice(valid_actions))
```

Do not sample from an all-zero mask. Treat it as an environment bug unless the agent is already terminated or truncated and should receive `None` in AEC mode.

## Invalid Action Strategy

Choose one invalid-action policy and document it in the environment:

- Advisory masks: invalid in-space actions are handled deterministically, often as no-ops with optional penalties. This keeps random API tests from crashing but may hide policy bugs.
- Strict masks: invalid masked actions terminate or penalize the acting agent. If using strict enforcement, make sure wrapper ordering and observation masks agree for the current selected agent.
- Assertion-only: invalid actions raise an error during development. Avoid this in public defaults unless compliance tests and callers are expected to submit only masked actions.

`AssertOutOfBoundsWrapper` checks whether a discrete action is inside the declared action space. It does not by itself prove that a masked action is legal in the current state.

## Parallel Masks

For `ParallelEnv`, return masks for all live agents from `reset()` and `step()` when those agents are expected to act on the next tick. If the episode ends and `self.agents` becomes empty, final masks are usually irrelevant, but returned dictionaries should still be internally consistent for the final transition.

## AEC Masks

For direct AEC environments, `last()` returns the selected agent's observation and info. The mask must describe the selected agent's valid actions at that moment, not another agent's future turn. Dead agents should be stepped with `None`; do not require a non-empty mask for dead-agent cleanup.

## Common Pitfalls

- Mask length differs from `action_space(agent).n`.
- Mask dtype is a floating array with non-binary values.
- Mask is stale after moving an agent or changing a board state.
- Reset observations include masks, but step observations forget them.
- One agent's mask is accidentally copied to all agents.
- All actions are masked out while the agent is still live.
- Observation space is not updated after wrapping observations in a dictionary.
- A training loop checks only observation masks while the environment emits masks in infos, or the reverse.

The bundled [custom environment template](../scripts/custom_env_template.py) can run with `--action-masks` to show a small observation-dictionary mask pattern.

---
name: spaces-data
description: "Design Gymnasium action and observation spaces, validate samples,
  flatten/unflatten data, serialize JSONable batches, and debug dtype/shape
  mismatches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gymnasium Spaces and Data Contracts

Use this sub-skill when a task involves choosing Gymnasium action or observation spaces, validating samples with `contains`, seeding or sampling spaces, flattening nested data for model inputs, unflattening model vectors back to structured observations/actions, or serializing space samples.

## Start Here

- For constructor choices and data contracts, use `references/space-design.md` before modifying an environment's `action_space` or `observation_space`.
- For `flatdim`, `flatten_space`, `flatten`, `unflatten`, `to_jsonable`, and `from_jsonable`, use `references/flattening-and-json.md`.
- For `Box.contains` surprises, integer starts, nested flatten shape mismatches, dynamic spaces, and wrapper space updates, use `references/troubleshooting.md`.
- To smoke-test the local Gymnasium install and demonstrate the core contract, run `python sub-skills/spaces-data/scripts/space_contract_smoke.py --help` and then `python sub-skills/spaces-data/scripts/space_contract_smoke.py` from the root Gymnasium skill directory.

## Scope Boundaries

- Use `../environment-api/SKILL.md` for custom `Env` lifecycle, `reset`/`step`, registration, `check_env`, and seeding an environment through `reset(seed=...)`.
- Use `../wrappers-recording/SKILL.md` when a wrapper changes `observation_space`, `action_space`, observations, actions, rewards, rendering, or recording behavior.
- Use `../vectorization/SKILL.md` for batched/vector spaces, `gym.vector` utilities, `single_observation_space`, `single_action_space`, and vector wrapper space transforms.

## Minimum Correct Patterns

```python
import numpy as np
from gymnasium import spaces

observation_space = spaces.Dict({
    "position": spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32),
    "inventory": spaces.Tuple((spaces.Discrete(5), spaces.MultiBinary(3))),
})

observation = observation_space.sample()
assert observation_space.contains(observation)
```

```python
from gymnasium.spaces import utils as space_utils

flat = space_utils.flatten(observation_space, observation)
restored = space_utils.unflatten(observation_space, flat)
assert observation_space.contains(restored)
```

Keep runtime guidance self-contained. Do not depend on Gymnasium source, tests, examples, or documentation paths at runtime.

# Workflows

## Tiny bandit policy loop

```python
from numpy_ml.bandits import BernoulliBandit
from numpy_ml.bandits.policies import EpsilonGreedy, UCB1

bandit = BernoulliBandit([0.2, 0.8])
policies = [EpsilonGreedy(epsilon=0.1), UCB1(C=1)]

for policy in policies:
    rewards = []
    actions = []
    for _ in range(10):
        reward, arm_id = policy.act(bandit)
        rewards.append(reward)
        actions.append(arm_id)
    print(policy, sum(rewards), actions)
```

This is the safest first workflow because it does not need Gym or plotting.

## BanditTrainer comparison

Use the trainer only after the basic policy loop works. Disable plotting unless
the user explicitly wants figures and has installed plotting dependencies.

```python
from numpy_ml.bandits.trainer import BanditTrainer

trainer = BanditTrainer()
# trainer.compare([...], bandit, n_trials=100, n_duplicates=3, plot=False)
```

Keep trial counts small for smoke tests.

## RL/Gym preparation checklist

1. Decide whether real environment training is required. If not, use `EnvModel`
   or bandit smokes instead.
2. Install the optional RL dependency (`gym`) in a user-approved runtime.
3. Check whether the environment follows the older Gym API expected by this
   legacy snapshot or the newer Gymnasium-style reset/step signatures.
4. Start with very small episode counts and `render=False`.
5. Treat plotting as optional; headless environments should avoid it.

## EnvModel tiny check

```python
from numpy_ml.rl_models.rl_utils import EnvModel

model = EnvModel()
model[(0, 1, 1, 2)] += 1
print(model.state_action_pairs())
print(model.outcome_probs(0, 1))
```

Use this to validate tabular RL utilities without requiring a live Gym
environment.

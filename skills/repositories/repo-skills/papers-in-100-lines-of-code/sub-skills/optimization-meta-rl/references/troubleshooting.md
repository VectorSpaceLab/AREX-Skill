# Optimization, Meta-Learning, and RL Troubleshooting

## Keras MNIST or plotting scaffolding dominates the task

Symptoms: importing an optimizer/layer script starts dataset loading, or a quick
run spends time downloading MNIST and saving plots.

Recovery:

- Extract only the optimizer/layer class into a small guarded script.
- Use synthetic tensors for shape and gradient checks.
- Add plotting only after the algorithmic update has been validated.

## Optimizer state behaves incorrectly

Symptoms: custom Adam/RAdam does not update, loses state, or references an
unexpected global variable.

Recovery:

1. Verify the optimizer stores state per parameter and iterates over its own
   model or parameter list.
2. Run one update with known gradients and compare the sign/magnitude against
   a rough manual expectation.
3. Keep bias correction and epsilon placement consistent with the paper
   implementation before comparing to PyTorch.

## CUDA hard-code blocks small tests

Symptoms: `.cuda()` fails or tensor/device mismatch appears in activation,
meta-learning, or RL scripts.

Recovery:

- Replace hard-coded CUDA with explicit `device` plumbing for CPU shape tests.
- Keep GPU requirements for actual long training if the user needs performance
  or large image/RL experiments.
- Do not combine CPU validation with a claim that CUDA reproduction passed.

## Meta-learning gradients disappear or explode

Symptoms: `None` gradients, in-place modification errors, exploding losses, or
no meta-update after adapting MAML/Reptile/hypergradient code.

Recovery:

- Inspect where parameters are cloned, detached, or updated through `.data`.
- Use one task and one inner step first; assert every expected parameter has a
  gradient or intentionally detached update.
- Lower the inner-loop learning rate and check finite losses before increasing
  task count or epochs.

## Atari/gym environment setup fails

Symptoms: `gym.error.NameNotFound`, missing Atari ROMs, wrapper import errors,
`stable_baselines3` version conflict, or observations with unexpected shape.

Recovery:

1. Do not install ROMs or launch long training without user approval.
2. Verify the environment id, wrappers, observation shape, action count, and one
   reset/step in a scratch environment before training.
3. Keep the older Gym/Stable-Baselines3 pins isolated; modern Gymnasium APIs may
   return `(obs, info)` and split terminated/truncated flags, which requires
   adaptation.

## Long training loops are mistaken for smoke tests

Symptoms: a command starts 5k, 70k, or 30M updates; verification stalls.

Recovery:

- Use `scripts/estimate_training_steps.py` to make loop scale explicit.
- Reduce epochs/steps/batch for diagnostics and state that the run only checks
  wiring.
- For real reproduction, set a time/compute budget and checkpoint/output policy
  before starting.

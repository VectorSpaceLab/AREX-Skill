# Troubleshooting

## Symptom: DPO rejects reasoning data

Likely cause:

- Only one of `chosen_reasoning` or `rejected_reasoning` is present.
- The model family does not allow reasoning in the way the sample is written.

Fix:

- Keep the reasoning pair synchronized.
- Re-check the model-family rules in the root compatibility reference.

## Symptom: GRPO generates but the trainer looks incompatible

Likely cause:

- The reward-function module has no callable ending in `_reward`.
- The reward function signature is not shaped like the repo examples.

Fix:

- Add or rename a callable so it ends with `_reward`.
- Keep the return value as a list of floats.

## Symptom: Liger configuration is confusing

Likely cause:

- A user selected an unavailable Liger GRPO loss variant.

Fix:

- Restrict the choice to the documented variants.
- Remember that `dr_grpo` needs `--max_completion_length`.

## Symptom: reference-model or generation setup is unstable

Likely cause:

- The user is trying to run a heavy preference workflow without a clear CUDA/runtime plan.

Fix:

- Check the environment diagnostic.
- Confirm the model family and data schema before the launch command is emitted.

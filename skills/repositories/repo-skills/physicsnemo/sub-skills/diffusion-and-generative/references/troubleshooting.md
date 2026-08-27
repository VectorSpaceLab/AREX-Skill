# Diffusion troubleshooting

## Missing weights or data

- Symptom: the workflow cannot generate or train because a checkpoint, statistics file, or dataset is missing.
- Likely cause: the example is a full recipe, not a self-contained smoke.
- Fix: document the required asset explicitly and keep the smoke API-only.

## Shape / channel mismatch

- Symptom: the diffusion model or solver errors on input size or channels.
- Likely cause: the example-specific image/grid shape was not matched to the model constructor.
- Fix: confirm the constructor arguments and the expected tensor layout first.

## Scheduler / sigma / guidance issues

- Symptom: sampling is unstable or a solver raises because a scheduler/guidance setting is inconsistent.
- Likely cause: the wrong predictor, sigma range, or preconditioner was chosen.
- Fix: inspect the workflow reference and check the constructor arguments against the chosen route.

## Optional backend or patching issues

- Symptom: a patch-based or multi-diffusion route fails under CUDA or with collectives.
- Likely cause: the user mixed patching and domain-parallel logic or assumed a CPU path would prove a GPU route.
- Fix: separate the diffusion API smoke from the distributed/path-heavy recipe.

## Over-eager inference mode

- Symptom: guidance-based workflows stop producing useful gradients.
- Likely cause: the code wrapped a gradient-dependent guidance path in the wrong inference context.
- Fix: preserve the autograd pattern described in the workflow reference.

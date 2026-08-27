# Troubleshooting

## Symptom: labels do not line up with the class heads

Likely cause:

- The dataset labels do not match the class map expected by the repo.

Fix:

- Normalize the labels before launching the classification run.
- Make sure train and eval splits share the same mapping.

## Symptom: loss choice seems unstable

Likely cause:

- The class imbalance is large and the selected loss does not match it.

Fix:

- Try focal loss or a class-balanced loss.
- Start with the simplest stable baseline and then increase complexity.

## Symptom: early stopping never triggers

Likely cause:

- The monitored metric is not improving enough for the configured threshold.

Fix:

- Re-check the eval split.
- Make sure the chosen metric matches the user’s real goal.

## Symptom: Liger or LoRA interactions are confusing

Likely cause:

- The classification wrapper already manages the head and save path specially.

Fix:

- Keep the classification-specific save and wrapper rules in mind.
- Use the command builder and inspect the final printed command before launching.

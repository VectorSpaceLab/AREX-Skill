# Troubleshooting

## Checkpoint URL, network, and cache problems

Symptoms:

- the pretrained checkpoint never downloads,
- `torch.hub` reports a network, proxy, or SSL failure,
- repeated runs keep redownloading the same file.

What to check:

- confirm the pretrained name is one of the documented registry entries,
- verify the network can reach the checkpoint host,
- make sure the cache location is writable,
- retry after the cache is cleared only if the file may be corrupted.

Notes:

- the download path comes from the pretrained registry,
- distributed runs use rank-specific cache names before synchronizing,
- one OC20 pretrained entry is marked temporarily unavailable in source.

## Output-layer mismatch

Symptoms:

- the checkpoint loads but the final prediction head fails shape checks,
- validation metrics look wrong after transfer,
- strict loading rejects the state dict.

What to check:

- if you want the source checkpoint head, keep `--load-pretrained-model-output-layer`,
- if the target task needs a new head, omit that flag so Graphormer resets the output layer,
- confirm that `--num-classes`, hidden width, layer count, and architecture name match the checkpoint family.

## CUDA-only evaluation behavior

Symptoms:

- evaluation crashes before the first batch,
- CUDA is unavailable even though the command looks correct,
- CPU-only environments cannot make progress.

What to check:

- `graphormer/evaluate/evaluate.py` moves the model to the current CUDA device,
- each batch is moved to CUDA before inference,
- this script is not CPU-safe as written.

## Metric mismatch

Symptoms:

- the command renders successfully but the reported metric is inappropriate,
- a classification task is evaluated with MAE,
- a regression task is evaluated with AUC.

What to check:

- use `auc` for binary classification-style checkpoint evaluation,
- use `mae` for regression-style checkpoint evaluation,
- pretrained PCQM4M evaluation uses the built-in OGB evaluators rather than the generic metric branch.

## OGB split or evaluator mismatch

Symptoms:

- the checkpoint loads, but the evaluator disagrees with the dataset,
- a split name is accepted but the downstream evaluator is wrong,
- the result looks inconsistent with the task family.

What to check:

- pair PCQM4M pretrained checkpoints with the PCQM4M evaluator branch,
- pair MolHIV fine-tuning with `ogbg-molhiv` and AUC,
- make sure the split matches the intended protocol before evaluation,
- if the split is external to the checkpoint family, render the command only after confirming the dataset contract.

## Save-dir checkpoint iteration surprises

Symptoms:

- evaluation tries to open a non-checkpoint file,
- results appear in a surprising order,
- one bad file stops the whole loop.

What to check:

- keep the save directory checkpoint-only,
- rename or move logs and temporary files out of the directory,
- remember that directory iteration order is not guaranteed.

## Strict checkpoint load

Symptoms:

- `load_state_dict` fails even though the name looks right,
- a transfer run used a different head, encoder width, or layer count,
- a model family switch was made without updating the architecture flags.

What to check:

- strict loading means the state dict must match the constructed model exactly,
- confirm `--arch`, `--encoder-*`, `--num-classes`, and `--pre-layernorm` choices,
- keep the checkpoint family and task family aligned.

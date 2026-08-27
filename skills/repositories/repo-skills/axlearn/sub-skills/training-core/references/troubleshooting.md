# training-core troubleshooting

## Purpose

Read this when core trainer or tokenizer workflows fail.

## Common failures

### `ImportError` for `axlearn.common.launch_trainer_main` or `SpmdTrainer`

**Likely cause:** The package was installed without the base AXLearn dependency set.

**Recovery:** Reinstall the editable package and include the core runtime dependencies used by the training stack.

### `ModuleNotFoundError` for TensorFlow or TensorFlow Datasets

**Likely cause:** The trainer/input stack needs TensorFlow, TFDS, and related packages.

**Recovery:** Install the core extra set used by the training workflows and rerun the import check.

### A fake-data tutorial still tries to read a real dataset

**Likely cause:** `DATA_DIR` was not set to `FAKE`, or the trainer config does not have a fake-data branch.

**Recovery:** Set `DATA_DIR=FAKE` before the command and use a config that explicitly supports fake inputs.

### `launch_trainer_main` fails because the module/config name is wrong

**Likely cause:** The module path needs the `axlearn.` package prefix, or the config name is not present in `named_trainer_configs()`.

**Recovery:** Inspect the module's exported config names with `scripts/inspect_trainer_config.py`.

### SentencePiece training is slow or memory-heavy

**Likely cause:** The tokenizer workflow can process a large TFDS corpus and uses substantial RAM.

**Recovery:** Use a smaller dataset or fewer training examples when you are only validating wiring, not producing a full tokenizer.

## Recovery order

1. Re-run the install smoke check.
2. Verify the target module exports the expected config name.
3. Confirm `DATA_DIR=FAKE` if the workflow is meant to stay synthetic.
4. Only then escalate to a larger run or a domain-specific sub-skill.

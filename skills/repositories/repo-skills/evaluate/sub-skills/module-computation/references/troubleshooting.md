# Computation Troubleshooting

## Missing Required Inputs

Symptom: `ValueError: Evaluation module inputs are missing...` or `Bad inputs for evaluation module...`.

Fix:

1. Print `module.features`.
2. Pass every required feature name exactly.
3. Do not assume every module uses `predictions` and `references`; tests cover modules that require `inputs` and `targets`.
4. Keep module-specific options separate from feature inputs; options go through `compute(..., **kwargs)` only when documented by that module.

## Mismatched Prediction and Reference Lengths

Symptom: `ValueError` containing `Mismatch in the number of predictions ... and references ...`.

Fix: make every batch column the same length before calling `add_batch` or direct `compute`. If your dataloader drops or pads examples, align predictions and labels after filtering.

## Wrong Scalar vs Batch Method

Symptom: `add` rejects list-shaped values, `add_batch` rejects scalars, or sequence features report an unexpected scalar/string.

Fix:

- Use `add(prediction=item, reference=item)` for one example.
- Use `add_batch(predictions=[...], references=[...])` for multiple examples.
- Remember `features` describes a single example. A `Sequence(Value("int64"))` feature means one example is list-like, so a batch is a list of those list-like examples.

## Feature Type or Casting Errors

Symptom: errors mention expected `Features`, Arrow conversion, string values, or `Got a string but expected a list instead`.

Fix:

1. Compare the failing input to `module.features`.
2. Convert framework tensors to CPU/list forms if a module or downstream code does not handle the framework object as expected.
3. For `Value("string")`, pass real strings; evaluate intentionally avoids silently casting arbitrary objects to strings.
4. For `Sequence(...)`, pass list-like values and avoid bare strings.
5. If `features` is a list of alternatives, test one representative example before a long batch run.

## Cache Lock or Concurrent Metric Collisions

Symptom: errors mention `another evaluation module instance is already using the local cache file`, `Cannot acquire lock`, or too many concurrent cache files.

Fix:

- Set a unique `experiment_id` for concurrent jobs sharing a cache directory.
- Use separate `cache_dir` values for unrelated runs if isolation is easier.
- Increase `max_concurrent_cache_files` only for high-concurrency single-process evaluations that genuinely need many simultaneous cache files.
- Ensure old crashed processes are gone before deleting stale cache/lock files.

## Distributed Hang or Timeout

Symptom: worker waits indefinitely or fails with `Expected to find locked file`, `Cannot acquire lock on cached file`, or rendezvous lock errors.

Fix:

1. Confirm every worker uses the same `cache_dir`, `num_process`, and `experiment_id`.
2. Confirm each worker has a unique `process_id` in `[0, num_process - 1]`.
3. Confirm all workers can read and write the shared cache directory.
4. Confirm all workers call `add`, `add_batch`, or direct `compute`; worker `0` waits for other workers' cache locks.
5. Increase `timeout` for slow startup or slow storage.
6. Do not set `keep_in_memory=True` in distributed mode.

## Invalid Distributed Settings

Symptom: constructor raises about `process_id`, `num_process`, or `keep_in_memory`.

Fix:

- `process_id` must be a non-negative integer.
- `num_process` must be an integer greater than `process_id`.
- `keep_in_memory=True` is allowed only when `num_process == 1`.

## Duplicate Combined Output Keys

Symptom: result keys are unexpectedly prefixed, such as `dummy_metric_set_equality`, or duplicate module names gain indexes.

Fix:

- This is expected when modules return the same metric key.
- Use a dict in `evaluate.combine({"name": module_or_string})` for stable names.
- Use `force_prefix=True` when downstream code needs every key to include its module prefix, even when keys are unique.

## Combined Module Option Conflicts

Symptom: a combined evaluation receives a keyword argument intended for only one module and another module rejects it.

Fix: `CombinedEvaluations` forwards the same kwargs to each module after selecting feature inputs. If compute options differ, run modules separately or combine only modules with compatible compute kwargs.

## Empty Inputs or Empty Results

Symptom: result is `{}` or a module-specific empty result.

Fix: Some modules return an empty dict for empty prediction/reference lists. Check whether upstream filtering removed all examples before treating `{}` as a valid score.

## Saved JSON Contains Local Metadata

Symptom: `evaluate.save` output includes `_interpreter_path`, `_python_version`, `_git_commit_hash`, and timestamps.

Fix: Keep raw saved files for internal reproducibility. Before sharing externally, review whether the interpreter path or commit hash is acceptable to disclose.


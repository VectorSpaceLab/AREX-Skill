# Results and DataProto

## Result Saving

LMFlow inference can save outputs to a directory rather than a single file. When `save_inference_results` is true, the path should point to a directory and LMFlow writes an `inference_results.pkl` file inside it.

## DataProto Shape

The vLLM route uses `tensordict`-style data containers. In the inspected package, `DataProto` round-trips with:

- a tensor or array-like `inputs` batch;
- optional `outputs` batch;
- `meta_info` containing sampling parameters.

## Practical Consequences

- When the engine repeats outputs per prompt, the inputs are repeated accordingly.
- `sampling_params["n"]` may represent the internal generation batch rather than the user-facing rollout count in the repeated structure.
- Keep output directories separate from training checkpoints to avoid accidental overwrite confusion.

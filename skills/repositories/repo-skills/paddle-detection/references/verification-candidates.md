# Verification Candidates

This file records safe, representative checks that mirror the repository's public workflows without requiring the original checkout to remain available.

## Safe CPU-oriented checks

- `python -c "import paddle, ppdet; print(paddle.__version__, ppdet.__version__)"`
- `python -c "import paddle; paddle.utils.run_check()"`
- `python tools/train.py --help`
- `python tools/eval.py --help`
- `python tools/infer.py --help`
- `python tools/export_model.py --help`
- `python deploy/pipeline/pipeline.py --help`
- `python -m pip check`
- `python ppdet/modeling/tests/test_ops.py` when the target checkout has a compatible Paddle build and the test is safe in the prepared environment.
- `python ppdet/modeling/tests/test_architectures.py` for a representative model-construction smoke check when memory is sufficient.
- `python ppdet/model_zoo/tests/test_list_model.py` and `python ppdet/model_zoo/tests/test_get_model.py` only when network/cache policy is explicit; `get_model` may download weights.

## Backend or network-gated checks to keep explicit

- CUDA/Paddle Inference/TensorRT training and inference commands.
- `test_tipc/*` certified chains.
- PP-Human/PP-Vehicle full pipeline runs using auto-downloaded models.
- Paddle Serving, Paddle Lite, FastDeploy, and ONNXRuntime runtime checks.
- Benchmark scripts and multi-GPU launchers.

Use the sub-skill routes and troubleshooting references to decide whether a candidate is safe, optional, or blocked by hardware or network policy.

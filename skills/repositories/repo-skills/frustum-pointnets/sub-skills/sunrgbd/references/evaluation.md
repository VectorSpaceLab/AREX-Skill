# SUN RGB-D evaluation

`test_one_hot.py` accepts `--gpu`, `--num_point` (2048 default), `--model`,
`--model_path`, `--output`, `--data_path`, `--from_rgb_detection`, `--idx_path`,
and `--dump_result`. A normal validation run dumps a result pickle; `evaluate.py`
then receives `--data_path` and `--result_path`, with
`--from_rgb_detection` when the input came from detected boxes.

The repository's Python evaluator computes 3D detection AP and was written to
avoid the slower original MATLAB evaluator. Treat its result as tied to the
exact class ordering, data split, detector mode, checkpoint, and generated
pickle schema. Preserve these metadata beside every result.

No benchmark score is implied by a successful file check. Compare with the
source evaluator only in a prepared legacy environment and with the external
SUNRGB-D assets present.

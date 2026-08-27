# Training, Evaluation, and Inference CLI Reference

Live inspection confirmed these parser surfaces in the inspected source checkout:

- `tools/train.py`: `-c/--config`, `-o/--opt`, `--eval`, `-r/--resume`, `--slim_config`, `--enable_ce`, `--amp`, `--fleet`, `--use_vdl`, `--vdl_log_dir`, `--use_wandb`, `--save_prediction_only`, `--profiler_options`, `--save_proposals`, `--proposals_path`, `--to_static`.
- `tools/eval.py`: `-c/--config`, `-o/--opt`, `--output_eval`, `--json_eval`, `--slim_config`, `--bias`, `--classwise`, `--save_prediction_only`, `--amp`, and small-object slice options `--slice_infer`, `--slice_size`, `--overlap_ratio`, `--combine_method`, `--match_threshold`, `--match_metric`.
- `tools/infer.py`: `-c/--config`, `-o/--opt`, `--infer_dir`, `--infer_list`, `--infer_img`, `--output_dir`, `--draw_threshold`, `--save_threshold`, `--slim_config`, `--use_vdl`, `--do_eval`, `--vdl_log_dir`, `--save_results`, `--slice_infer`, `--slice_size`, `--overlap_ratio`, `--combine_method`, `--match_threshold`, `--match_metric`, `--visualize`, `--rtn_im_file`.
- `tools/export_model.py` lives in the deployment route but shares the same `-c/--config` and `-o/--opt` parser behavior.

Command tips:

- Quote overrides that contain strings or YAML lists; the parser passes values through YAML loading.
- A missing `-c` is a hard parse error.
- `--eval` on train enables evaluation during training.
- `--classwise` and `--json_eval` only make sense when the selected metric and dataset produce compatible evaluator outputs.
- `--slice_infer` adds sliced-image merge behavior; the combine method and overlap ratio must be chosen consistently between train/eval/infer paths.

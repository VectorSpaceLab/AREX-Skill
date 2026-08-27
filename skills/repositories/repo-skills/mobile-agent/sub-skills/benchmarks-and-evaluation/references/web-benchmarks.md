# Web Benchmarks

Use this reference for Mobile-Agent-v3.5 web benchmark evaluation with WebArena, WebVoyager, VisualWebArena, Online Mind2Web-style judge modes, or similar browser task suites.

The benchmark runner resembles the browser GUI-Owl launcher but defaults to evaluation-oriented settings such as `--image_type oss`, `--max_iter 50`, and judge flags.

## Common fields

- `--task_id`: benchmark task id when available.
- `--task`: natural-language web task.
- `--web`: site URL or benchmark service placeholder.
- `--login`: use only with private prepared login state.
- `--output_dir`, `--rollout_id`, `--seed`: result and reproducibility controls.
- `--image_type`: `oss`, `base64`, or `file`; benchmark defaults often use `oss`.
- `--model`, `--base_url`: agent model endpoint.
- `--eval`, `--eval_mode`, `--eval_model`, `--eval_score_threshold`: judge/evaluation options.
- `--use_css_som`, `--use_omni_som`, `--omni_url`: perception overlays.
- `--headless`: browser window visibility; still needs Playwright browser install.

Use `scripts/build_web_benchmark_command.py`.

## Safety notes

- Benchmark websites/services may require logins, cookies, local service containers, or official task files.
- `image_type=oss` requires object-store credentials; choose `base64` where supported for safer local staging.
- Do not run judge evaluation with raw API keys in command history.
- Browser/eval runs can create result directories and downloaded files; stage them in a private output directory.

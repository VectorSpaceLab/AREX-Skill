# Browser GUI-Owl Workflow

Use the browser route for websites, browser tasks, WebAgent prompts, Playwright browser operation, image upload mode, CSS SoM, and OmniParser. Use benchmarks-and-evaluation instead when the user asks for WebArena/WebVoyager/VisualWebArena benchmark scoring or task suites.

## Main launcher surface

```text
python run_gui_owl_1_5_for_web.py \
  [--task_id WebAgent_task_0] \
  --task <browser-task> \
  [--web <url-or-site-name>] \
  [--login] \
  [--rollout_id 0] \
  [--max_iter 100] \
  [--output_dir results_log] \
  [--seed 1234] \
  [--max_attached_imgs 2] \
  [--text_only] \
  [--image_type base64|file|oss] \
  [--init_image_path <path-or-url>] \
  [--download_dir downloads] \
  --model <model-name> \
  --base_url <openai-compatible-base-url> \
  [--eval --eval_mode <mode> --eval_model <judge-model>] \
  [--use_css_som | --use_omni_som --omni_url <url>] \
  [--headless] \
  [--save_accessibility_tree] \
  [--force_device_scale] \
  [--window_width 1080 --window_height 1440]
```

Build the command with `scripts/build_browser_command.py`.

## Image mode decision

- `base64`: safest default for OpenAI-compatible APIs that accept inline images.
- `file`: useful when a local model/server can read local image paths.
- `oss`: only when the runtime environment has private OSS credentials and the model server expects object-store image URLs. Do not use this mode accidentally in shared logs.

## SoM/perception decision

- `--use_css_som`: browser DOM/CSS based set-of-mark overlay; good first option for ordinary webpages.
- `--use_omni_som --omni_url <url>`: use OmniParser when visual grounding is needed and an OmniParser service is already running.
- Use only one SoM mode at a time.

## Headless mode

`--headless` hides the browser window, but it does not remove runtime requirements: Playwright browser binaries and system dependencies must be installed, the website must be reachable, login/session state must be handled privately, and the model API must be available.

## Eval flags

`--eval`, `--eval_only`, `--eval_model`, `--eval_mode`, and `--eval_score_threshold` configure a judge/evaluation flow. Use this only when the user has an evaluation dataset/task setup and a judge model/API. For formal benchmark suites, prefer the benchmarks sub-skill.

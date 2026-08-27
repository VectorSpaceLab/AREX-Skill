# PC-Agent Configuration

## Current PC-Agent

Current `PC-Agent/run.py` reads model config from `config.json`:

```json
{
  "vl_model_name": "your-vl-model",
  "llm_model_name": "your-planner-model",
  "token": "<private-token>",
  "url": "https://your-openai-compatible-endpoint/v1/chat/completions"
}
```

Some runtime setups also need OCR API fields:

```json
{
  "OCR_ACCESS_KEY_ID": "<private>",
  "OCR_ACCESS_KEY_SECRET": "<private>"
}
```

Validate safely:

```bash
python sub-skills/pc-agent/scripts/validate_pc_agent_config.py --config config.json
```

Use `--require-ocr-api` only when `--ocr_api 1` is required and no local OCR fallback is planned.

## Current command knobs

- `--mac 1` for Mac behavior, `--mac 0` for Windows behavior.
- `--ratio`: often `2.0` on Mac Retina screenshots, `1.0` on Windows.
- `--font_path`: Windows default often `C:\Windows\Fonts\arial.ttf`; Mac v1 uses `/System/Library/Fonts/Times.ttc`.
- `--use_som`, `--draw_text_box`, `--use_a11y`, `--use_perception_info`: perception/action context controls.
- `--ocr_api`: `1` for OCR API mode, `0` for local/fallback mode if supported by the runtime environment.
- `--num_step_limit`, `--disable_reflection`, `--clear_history_each_subtask`: execution loop controls.

## PC-Agent v1

Use v1 only for legacy workflows that specifically depend on `run_v1.py`. v1 puts endpoint fields on the CLI: `--api_url`, `--api_token`, and optional `--qwen_api` for icon captioning.

Keep raw tokens out of shell history by using environment variables and private wrapper scripts.

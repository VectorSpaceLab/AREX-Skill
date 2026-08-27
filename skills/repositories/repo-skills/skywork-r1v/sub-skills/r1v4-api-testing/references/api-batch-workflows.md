# API Batch Workflows

This reference distills the source R1V4 batch scripts into a self-contained workflow map. It keeps the request shape, Chinese terminology, and model choices visible without requiring the original checkout.

## Chinese terminology

| Term | Meaning | Used for |
| --- | --- | --- |
| 非流式 | non-stream | One final JSON response, `stream: false` |
| 流式 | stream | SSE chunked response, `stream: true` |
| 规划器 | planner | The planning model family |
| 图文问答 | image + text QA | An optional image plus a question |
| 纯文本 | text-only | Empty or omitted image field |
| 工具调用 | tool call | `<tool_call>` tagged JSON block |
| 观察 | observation | `<observation>` tagged JSON block |
| 最终答案 | final answer | `<answer>` tagged text block |
| 结果 JSONL | result JSONL | Batch output file with one record per case |

## Shared request contract

Every batch variant uses the same base API shape:

- `base_url`: `https://api.skyworkmodel.ai`
- `endpoint`: `/api/v1/chat/completions`
- `Authorization`: `Bearer <API_KEY_FROM_ENV_OR_CALLER_CONFIG>`
- `messages[0].content`: image block first, then text block
- image block format: `{"type": "image_url", "image_url": {"url": "data:<mime>;base64,..."}}`
- text block format: `{"type": "text", "text": "..."}`

The source scripts concatenate the image block before the question text. Keep that order.

## Batch mode matrix

| Source batch script | Model | Stream | Search | What it is for | Notes |
| --- | --- | --- | --- | --- | --- |
| `batch_nonstream.py` | `skywork/r1v4-lite` | `false` | `false` | Regular API batch testing | Source code waits for one JSON response and stores `response.full_response` plus `response.raw_response`. |
| `batch_stream.py` | `skywork/r1v4-lite` | `true` | `false` | Regular API batch testing with SSE output | Source code collects `data:` lines, concatenates `delta.content`, and stores `response.full_response` plus `response.raw_events`. |
| `batch_planner_nonstream.py` | `skywork/r1v4-vl-planner-lite` | `false` | not set in source | Planner batch testing | Same input schema as the regular scripts. |
| `batch_planner_stream.py` | `skywork/r1v4-vl-planner-lite` | `true` | not set in source | Planner batch testing with SSE output | Same input schema as the regular scripts. |

## Safe dry-run path

Use the bundled payload builder to inspect the exact request before any live call:

```bash
python scripts/build_api_payload.py \
  --image ./demo_image/demo_1.png \
  --question '右边第二个小孩子的裙子是什么颜色？' \
  --model skywork/r1v4-lite \
  --stream false \
  --enable-search false
```

Planner example:

```bash
python scripts/build_api_payload.py \
  --image ./demo_image/demo_1.png \
  --question '右边第二个小孩子的裙子是什么颜色？' \
  --model skywork/r1v4-vl-planner-lite \
  --stream true \
  --enable-search false
```

## Operational reminders

- Keep API keys out of the script body. Use env or caller config.
- Do not reverse the message order.
- Do not assume `enable_search` is on unless you explicitly set it in a dry-run payload.
- Treat the planner scripts as a separate model family, not just a stream toggle.

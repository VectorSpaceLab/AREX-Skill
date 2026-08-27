#!/usr/bin/env python3
"""No-network LazyLLM model helper smoke checks."""
from __future__ import annotations

import argparse
import json
from typing import Dict, List


def run(model_name: str) -> Dict[str, object]:
    from lazyllm.module.llms.onlinemodule.base.onlineChatModuleBase import (
        LazyLLMOnlineChatModuleBase,
        _is_input_inspection_failure,
        _remove_prior_tool_traces,
    )
    from lazyllm.module.llms.onlinemodule.map_model_type import get_model_type
    import requests

    model_type = get_model_type(model_name)

    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "original"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "old"}]},
        {"role": "tool", "tool_call_id": "old", "content": "stale"},
        {"role": "assistant", "content": "prior answer"},
        {"role": "user", "content": "continue"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "current"}]},
        {"role": "tool", "tool_call_id": "current", "content": "current observation"},
    ]
    sanitized = _remove_prior_tool_traces(messages)
    if "stale" in [item.get("content") for item in sanitized]:
        raise AssertionError("prior tool trace was not removed")
    if sanitized[-1]["content"] != "current observation":
        raise AssertionError("current tool observation was not preserved")

    module = LazyLLMOnlineChatModuleBase.__new__(LazyLLMOnlineChatModuleBase)
    merged = module._merge_stream_result([
        [{"index": 0, "id": "call-0", "type": "function", "function": {"name": "tool", "arguments": "{"}}],
        [{"index": 0, "id": "", "type": "function", "function": {"arguments": "}"}}],
    ])
    if merged[0]["function"]["arguments"] != "{}":
        raise AssertionError("streamed tool-call arguments did not merge")

    inspection = _is_input_inspection_failure(requests.RequestException('400: {"code":"data_inspection_failed"}'))
    return {
        "model_name": model_name,
        "model_type": model_type,
        "input_inspection_detection": inspection,
        "sanitized_message_count": len(sanitized),
        "stream_merge": merged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe LazyLLM model surface smoke checks.")
    parser.add_argument("--model-name", default="qwen3-coder-plus", help="Provider model name to classify.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    result = run(args.model_name)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

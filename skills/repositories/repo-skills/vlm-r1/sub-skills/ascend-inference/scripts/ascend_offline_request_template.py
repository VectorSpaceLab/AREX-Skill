#!/usr/bin/env python3
"""Render safe VLM-R1 Ascend offline inference request scaffolds.

This helper does not import vLLM, qwen_vl_utils, torch_npu, or start inference.
It prints or writes a parameterized scaffold that can be copied into a prepared
Ascend vllm-ascend environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_MODEL = "VLM-R1-Qwen2.5VL-3B-OVD-0321"
DEFAULT_DESCRIBE = "杯子在哪个位置？请输出杯子的bbox坐标。"
DEFAULT_EVENT = "杯子"
DEFAULT_IMAGE = "resources/test.jpg"


def build_prompt(describe: str, event: str, include_function_tags: bool = False) -> str:
    """Return the normalized Chinese VLM-R1 OVD prompt."""
    json_example = (
        '{"answer": "yes or no", "explanations": '
        '[{"bbox_2d": [xx, xx, xx, xx], "label": "xxx"}]}'
    )
    begin = "<|FunctionCallBegin|>\n" if include_function_tags else ""
    end = "\n<|FunctionCallEnd|>" if include_function_tags else ""
    return textwrap.dedent(
        f"""
        请分析图像并回答以下问题。您的回答应包含对图像内容的简要描述和最终答案。描述使用 `<description></description>` 标签包裹。答案必须以 JSON 格式输出，包含 "answer"（"yes" 或 "no"），并提供相关物体的边界框坐标作为解释。如果没有涉及具体物体，则将 "explanations" 设为 "None"。输出格式如下：

        <description>对图像内容的简要描述写在这里</description>

        {begin}```json
        {json_example}
        ```{end}

        具体问题:根据规则或识别要求，{describe}。图中是否出现{event}？
        """
    ).strip()


def build_messages(args: argparse.Namespace) -> List[Dict[str, Any]]:
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": args.image,
                    "min_pixels": args.min_pixels,
                    "max_pixels": args.max_pixels,
                },
                {
                    "type": "text",
                    "text": build_prompt(args.describe, args.event, args.include_function_tags),
                },
            ],
        },
    ]


def resolved_dtype(args: argparse.Namespace) -> str | None:
    if args.dtype:
        return args.dtype
    if args.hardware == "300iduo":
        return "float16"
    return None


def render_messages_json(args: argparse.Namespace) -> str:
    scaffold = {
        "purpose": "VLM-R1 Ascend offline vLLM message scaffold; not executable by itself.",
        "hardware": args.hardware,
        "model_path": args.model_path,
        "llm_settings": {
            "max_model_len": args.max_model_len,
            "limit_mm_per_prompt": {"image": args.limit_images},
            "dtype": resolved_dtype(args),
            "enforce_eager": args.enforce_eager,
        },
        "sampling_params": {"max_tokens": args.max_tokens},
        "messages": build_messages(args),
    }
    return json.dumps(scaffold, ensure_ascii=False, indent=2)


def render_vllm_python(args: argparse.Namespace) -> str:
    messages_json = json.dumps(build_messages(args), ensure_ascii=False, indent=4)
    dtype = resolved_dtype(args)
    dtype_line = f'    dtype={dtype!r},\n' if dtype else ""
    eager_line = "    enforce_eager=True,\n" if args.enforce_eager else ""
    limit_line = f'    limit_mm_per_prompt={{"image": {args.limit_images}}},\n'
    return f'''#!/usr/bin/env python3
"""Rendered VLM-R1 vllm-ascend offline inference scaffold.

Run this only inside a prepared Ascend vllm-ascend environment with visible NPU
hardware, the VLM-R1 checkpoint available at MODEL_PATH, and the required Python
packages installed. This file was generated as a template; review paths and dtype
before execution.
"""

from transformers import AutoProcessor
from vllm import LLM, SamplingParams
from qwen_vl_utils import process_vision_info

MODEL_PATH = {args.model_path!r}

MESSAGES = {messages_json}

llm = LLM(
    model=MODEL_PATH,
    max_model_len={args.max_model_len},
{limit_line}{dtype_line}{eager_line})

sampling_params = SamplingParams(max_tokens={args.max_tokens})

processor = AutoProcessor.from_pretrained(MODEL_PATH)
prompt = processor.apply_chat_template(
    MESSAGES,
    tokenize=False,
    add_generation_prompt=True,
)

image_inputs, _, _ = process_vision_info(MESSAGES, return_video_kwargs=True)
mm_data = {{}}
if image_inputs is not None:
    mm_data["image"] = image_inputs

llm_inputs = {{"prompt": prompt, "multi_modal_data": mm_data}}
outputs = llm.generate([llm_inputs], sampling_params=sampling_params)
print(outputs[0].outputs[0].text)
'''


def write_or_print(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"Wrote scaffold to {output}", file=sys.stderr)
    else:
        print(text)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render VLM-R1 Ascend offline request scaffolds without executing inference.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              scripts/ascend_offline_request_template.py --format messages
              scripts/ascend_offline_request_template.py --hardware 300iduo --format vllm-python --output rendered_ascend_offline_request.py
              scripts/ascend_offline_request_template.py --image resources/test.jpg --describe '杯子在哪个位置？' --event '杯子'
            """
        ),
    )
    parser.add_argument("--format", choices=["messages", "vllm-python"], default="messages")
    parser.add_argument("--hardware", choices=["a2", "300iduo"], default="a2", help="Target Ascend recipe family; 300iduo defaults dtype to float16.")
    parser.add_argument("--model-path", default=DEFAULT_MODEL, help="Container-visible or local checkpoint path used in the rendered scaffold.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Image path visible to offline inference.")
    parser.add_argument("--describe", default=DEFAULT_DESCRIBE, help="Chinese natural-language object/event query.")
    parser.add_argument("--event", default=DEFAULT_EVENT, help="Object/event name inserted into the yes/no OVD question.")
    parser.add_argument("--min-pixels", type=int, default=224 * 224)
    parser.add_argument("--max-pixels", type=int, default=1280 * 28 * 28)
    parser.add_argument("--limit-images", type=int, default=10)
    parser.add_argument("--max-model-len", type=int, default=16384)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--dtype", default=None, help="Override dtype; default is float16 for 300iduo and engine default for a2.")
    parser.add_argument("--no-enforce-eager", dest="enforce_eager", action="store_false", help="Omit enforce_eager=True from the Python scaffold.")
    parser.set_defaults(enforce_eager=True)
    parser.add_argument("--include-function-tags", action="store_true", help="Wrap the JSON answer example in FunctionCallBegin/FunctionCallEnd sentinels.")
    parser.add_argument("--output", help="Optional output file for the rendered scaffold. Without it, print to stdout.")
    args = parser.parse_args(argv)
    if args.min_pixels <= 0 or args.max_pixels <= 0 or args.min_pixels > args.max_pixels:
        parser.error("pixel bounds must be positive and min-pixels must be <= max-pixels")
    if args.limit_images <= 0:
        parser.error("limit-images must be positive")
    if args.max_model_len <= 0 or args.max_tokens <= 0:
        parser.error("max-model-len and max-tokens must be positive")
    return args


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.format == "messages":
        rendered = render_messages_json(args)
    else:
        rendered = render_vllm_python(args)
    write_or_print(rendered, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

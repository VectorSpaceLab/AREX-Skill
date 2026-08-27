#!/usr/bin/env python3
"""Smoke-test Qwen2.5-VL conversation and detection formatting.

This script does not load a model. It only exercises the chat-conversation
builder, the Qwen detection suffix formatter, and the qwen-vl-utils resize
path used by the current source tree.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from PIL import Image
from qwen_vl_utils import smart_resize

from maestro.trainer.models.qwen_2_5_vl.detection import detections_to_suffix_formatter
from maestro.trainer.models.qwen_2_5_vl.loaders import format_conversation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test the Qwen2.5-VL conversation and detection formatters without loading a model."
    )
    return parser


def expected_suffix() -> str:
    classes = ["crate", "forklift"]
    xyxy = np.array([[1, 2, 5, 6], [7, 8, 10, 11]], dtype=np.float32)
    class_id = np.array([0, 1], dtype=np.int64)
    image_w = image_h = 28
    min_pixels = 28 * 28
    max_pixels = 28 * 28

    input_h, input_w = smart_resize(height=image_h, width=image_w, min_pixels=min_pixels, max_pixels=max_pixels)
    assert (input_h, input_w) == (28, 28), (input_h, input_w)

    scaled = xyxy / [image_w, image_h, image_w, image_h]
    scaled = scaled * [input_w, input_h, input_w, input_h]
    scaled = scaled.astype(int)

    lines = []
    for cid, box in zip(class_id, scaled):
        label = classes[int(cid)]
        bbox_str = ", ".join(str(int(num)) for num in box.tolist())
        lines.append(f'\t{{"bbox_2d": [{bbox_str}], "label": "{label}"}}')

    joined_lines = ",\n".join(lines)
    return f"```json\n[\n{joined_lines}\n]\n```"


def main() -> None:
    build_parser().parse_args()

    image = Image.new("RGB", (28, 28), color="white")
    system_message = "You are a helpful assistant."
    prefix = "Outline the position of crate, forklift. Output all the coordinates in JSON format."
    suffix = expected_suffix()

    conversation = format_conversation(
        image=image,
        prefix=prefix,
        suffix=suffix,
        system_message=system_message,
    )

    assert len(conversation) == 3, conversation
    assert conversation[0]["role"] == "system", conversation
    assert conversation[0]["content"][0]["type"] == "text", conversation
    assert conversation[0]["content"][0]["text"] == system_message, conversation
    assert conversation[1]["role"] == "user", conversation
    assert conversation[1]["content"][0]["type"] == "image", conversation
    assert conversation[1]["content"][1]["type"] == "text", conversation
    assert conversation[1]["content"][1]["text"] == prefix, conversation
    assert conversation[2]["role"] == "assistant", conversation
    assert conversation[2]["content"][0]["text"] == suffix, conversation

    output = detections_to_suffix_formatter(
        xyxy=np.array([[1, 2, 5, 6], [7, 8, 10, 11]], dtype=np.float32),
        class_id=np.array([0, 1], dtype=np.int64),
        classes=["crate", "forklift"],
        resolution_wh=(28, 28),
        min_pixels=28 * 28,
        max_pixels=28 * 28,
    )

    assert output == suffix, (output, suffix)
    assert output.startswith("```json\n[")
    assert output.endswith("\n```")

    payload = output.removeprefix("```json\n").removesuffix("\n```")
    parsed = json.loads(payload)
    assert parsed == [
        {"bbox_2d": [1, 2, 5, 6], "label": "crate"},
        {"bbox_2d": [7, 8, 10, 11], "label": "forklift"},
    ], parsed

    print("Qwen2.5-VL formatter smoke passed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Standalone AutoTrain LoRA-to-Kohya conversion helper.

Source-derived from `src/autotrain/tools/convert_to_kohya.py` with a small CLI wrapper.
Requires diffusers and safetensors in the active env.
"""

from __future__ import annotations

import argparse

from diffusers.utils import convert_all_state_dict_to_peft, convert_state_dict_to_kohya
from safetensors.torch import load_file, save_file

from autotrain import logger


def convert_to_kohya(input_path, output_path):
    logger.info(f"Converting Lora state dict from {input_path} to Kohya state dict at {output_path}")
    lora_state_dict = load_file(input_path)
    peft_state_dict = convert_all_state_dict_to_peft(lora_state_dict)
    kohya_state_dict = convert_state_dict_to_kohya(peft_state_dict)
    save_file(kohya_state_dict, output_path)
    logger.info(f"Kohya state dict saved at {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    args = parser.parse_args()
    convert_to_kohya(args.input_path, args.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

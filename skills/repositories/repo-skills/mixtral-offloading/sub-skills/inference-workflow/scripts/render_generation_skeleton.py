#!/usr/bin/env python3
"""Render a safe starter script for mixtral-offloading generation without running it."""
from __future__ import annotations

import argparse
from textwrap import dedent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-path', default='/path/to/quantized-state', help='Placeholder path to the quantized safetensors state directory.')
    parser.add_argument('--repo-root', default='/path/to/mixtral-offloading', help='Placeholder path to a user checkout whose root contains src/.')
    parser.add_argument('--offload-per-layer', type=int, default=4, help='Experts per layer to offload; use 5 as a starting point for smaller VRAM.')
    parser.add_argument('--max-new-tokens', type=int, default=128, help='Starter generation length.')
    parser.add_argument('--prompt', default='Explain mixture-of-experts offloading in one paragraph.', help='Starter prompt text.')
    return parser


def main() -> int:
    args = build_parser().parse_args()
    code = f"""
    # Generated skeleton only: review paths and run environment checks before executing.
    import json
    import sys
    from pathlib import Path

    repo_root = Path({args.repo_root!r})
    state_path = Path({args.state_path!r})
    sys.path.insert(0, str(repo_root))

    import torch
    from hqq.core.quantize import BaseQuantizeConfig
    from transformers import AutoConfig, AutoTokenizer, TextStreamer
    from src.build_model import OffloadConfig, QuantConfig, build_model

    index_path = state_path / 'model.safetensors.index.json'
    if not index_path.exists():
        raise FileNotFoundError(f'Missing safetensors index: {{index_path}}')
    weight_map = json.loads(index_path.read_text()).get('weight_map', {{}})
    required_prefix = 'model.layers.0.block_sparse_moe.experts.0.w1.W_q'
    if 'model.embed_tokens.weight' not in weight_map or required_prefix not in weight_map:
        raise ValueError('State directory does not look like the expected quantized offloading layout')

    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required for offloaded Mixtral generation')
    device = torch.device('cuda:0')

    model_name = 'mistralai/Mixtral-8x7B-Instruct-v0.1'
    config = AutoConfig.from_pretrained(str(state_path))
    num_experts = config.num_local_experts
    offload_per_layer = {args.offload_per_layer}
    offload_config = OffloadConfig(
        main_size=config.num_hidden_layers * (num_experts - offload_per_layer),
        offload_size=config.num_hidden_layers * offload_per_layer,
        buffer_size=4,
        offload_per_layer=offload_per_layer,
    )

    attn_config = BaseQuantizeConfig(nbits=4, group_size=64, quant_zero=True, quant_scale=True)
    attn_config['scale_quant_params']['group_size'] = 256
    ffn_config = BaseQuantizeConfig(nbits=2, group_size=16, quant_zero=True, quant_scale=True)
    quant_config = QuantConfig(ffn_config=ffn_config, attn_config=attn_config)

    model = build_model(device=device, quant_config=quant_config, offload_config=offload_config, state_path=str(state_path))
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    user_entry = dict(role='user', content={args.prompt!r})
    input_ids = tokenizer.apply_chat_template([user_entry], return_tensors='pt').to(device)
    attention_mask = torch.ones_like(input_ids)
    result = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        streamer=streamer,
        do_sample=True,
        temperature=0.9,
        top_p=0.9,
        max_new_tokens={args.max_new_tokens},
        pad_token_id=tokenizer.eos_token_id,
        return_dict_in_generate=True,
        output_hidden_states=True,
    )
    print(tokenizer.decode(result['sequences'][0], skip_special_tokens=True))
    """
    print(dedent(code).strip() + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

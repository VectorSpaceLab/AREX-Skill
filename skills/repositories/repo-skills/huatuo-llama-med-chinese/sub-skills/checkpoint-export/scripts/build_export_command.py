#!/usr/bin/env python3
"""Build dry-run LoRA checkpoint export commands for Huatuo-Llama-Med-Chinese.

The helper is intentionally lightweight: it imports no ML libraries and does not
run an export. It prints environment variables, warnings, and a self-contained
Python heredoc command that can be reviewed before execution in a prepared ML
environment.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List

SOURCE_ADAPTER_DEFAULT = "tloen/alpaca-lora-7b"
LLAMA_7B_WARNING = (
    "state-dict mode assumes an original LLaMA-7B-compatible architecture "
    "(dim=4096, n_heads=32, n_layers=32) and LLaMA Hugging Face key names; "
    "do not use it for Bloom, Huozi, ChatGLM, non-LLaMA, or non-7B checkpoints "
    "without redesigning and validating the translator."
)


def q(value: str) -> str:
    """Shell-quote one value."""
    return shlex.quote(value)


def hf_exporter_lines() -> List[str]:
    """Return inline exporter source without importing ML packages in this helper."""
    return [
        "import os",
        "from pathlib import Path",
        "import " + "torch",
        "from " + "peft import PeftModel",
        "from " + "transformers import LlamaForCausalLM, LlamaTokenizer",
        "",
        "BASE_MODEL = os.environ.get('BASE_MODEL', None)",
        "assert BASE_MODEL, (",
        "    'Please specify a value for BASE_MODEL environment variable, '",
        "    'e.g. `export BASE_MODEL=decapoda-research/llama-7b-hf`'",
        ")",
        f"ADAPTER_WEIGHTS = os.environ.get('ADAPTER_WEIGHTS', {SOURCE_ADAPTER_DEFAULT!r})",
        "OUTPUT_ROOT = Path(os.environ.get('OUTPUT_DIR', '.')).expanduser()",
        "OUTPUT_PATH = OUTPUT_ROOT / 'hf_ckpt'",
        "OUTPUT_PATH.mkdir(parents=True, exist_ok=True)",
        "",
        "tokenizer = LlamaTokenizer.from_pretrained(BASE_MODEL)",
        "base_model = LlamaForCausalLM.from_pretrained(",
        "    BASE_MODEL,",
        "    load_in_8bit=False,",
        "    torch_dtype=torch.float16,",
        "    device_map={'': 'cpu'},",
        ")",
        "first_weight = base_model.model.layers[0].self_attn.q_proj.weight",
        "first_weight_old = first_weight.clone()",
        "lora_model = PeftModel.from_pretrained(",
        "    base_model,",
        "    ADAPTER_WEIGHTS,",
        "    device_map={'': 'cpu'},",
        "    torch_dtype=torch.float16,",
        ")",
        "assert torch.allclose(first_weight_old, first_weight)",
        "",
        "if hasattr(lora_model, 'merge_and_unload'):",
        "    merged_model = lora_model.merge_and_unload()",
        "    merged_model.save_pretrained(str(OUTPUT_PATH), max_shard_size='400MB')",
        "else:",
        "    for layer in lora_model.base_model.model.model.layers:",
        "        if hasattr(layer.self_attn.q_proj, 'merge_weights'):",
        "            layer.self_attn.q_proj.merge_weights = True",
        "        if hasattr(layer.self_attn.v_proj, 'merge_weights'):",
        "            layer.self_attn.v_proj.merge_weights = True",
        "    lora_model.train(False)",
        "    assert not torch.allclose(first_weight_old, first_weight)",
        "    lora_model_sd = lora_model.state_dict()",
        "    deloreanized_sd = {",
        "        k.replace('base_model.model.', ''): v",
        "        for k, v in lora_model_sd.items()",
        "        if 'lora' not in k",
        "    }",
        "    LlamaForCausalLM.save_pretrained(",
        "        base_model,",
        "        str(OUTPUT_PATH),",
        "        state_dict=deloreanized_sd,",
        "        max_shard_size='400MB',",
        "    )",
        "try:",
        "    tokenizer.save_pretrained(str(OUTPUT_PATH))",
        "except Exception as exc:",
        "    print(f'WARNING: tokenizer was loaded but not saved cleanly: {exc}')",
        "print(f'Saved Hugging Face checkpoint to {OUTPUT_PATH}')",
    ]


def state_dict_exporter_lines() -> List[str]:
    """Return inline state-dict exporter source without helper-side ML imports."""
    return [
        "import json",
        "import os",
        "from pathlib import Path",
        "import " + "torch",
        "from " + "peft import PeftModel",
        "from " + "transformers import LlamaForCausalLM, LlamaTokenizer",
        "",
        "BASE_MODEL = os.environ.get('BASE_MODEL', None)",
        "assert BASE_MODEL, (",
        "    'Please specify a value for BASE_MODEL environment variable, '",
        "    'e.g. `export BASE_MODEL=decapoda-research/llama-7b-hf`'",
        ")",
        f"ADAPTER_WEIGHTS = os.environ.get('ADAPTER_WEIGHTS', {SOURCE_ADAPTER_DEFAULT!r})",
        "OUTPUT_ROOT = Path(os.environ.get('OUTPUT_DIR', '.')).expanduser()",
        "OUTPUT_PATH = OUTPUT_ROOT / 'ckpt'",
        "OUTPUT_PATH.mkdir(parents=True, exist_ok=True)",
        "",
        "_tokenizer = LlamaTokenizer.from_pretrained(BASE_MODEL)",
        "base_model = LlamaForCausalLM.from_pretrained(",
        "    BASE_MODEL,",
        "    load_in_8bit=False,",
        "    torch_dtype=torch.float16,",
        "    device_map={'': 'cpu'},",
        ")",
        "lora_model = PeftModel.from_pretrained(",
        "    base_model,",
        "    ADAPTER_WEIGHTS,",
        "    device_map={'': 'cpu'},",
        "    torch_dtype=torch.float16,",
        ")",
        "if hasattr(lora_model, 'merge_and_unload'):",
        "    merged_model = lora_model.merge_and_unload()",
        "    lora_model_sd = merged_model.state_dict()",
        "else:",
        "    for layer in lora_model.base_model.model.model.layers:",
        "        if hasattr(layer.self_attn.q_proj, 'merge_weights'):",
        "            layer.self_attn.q_proj.merge_weights = True",
        "        if hasattr(layer.self_attn.v_proj, 'merge_weights'):",
        "            layer.self_attn.v_proj.merge_weights = True",
        "    lora_model.train(False)",
        "    lora_model_sd = lora_model.state_dict()",
        "",
        "params = {",
        "    'dim': 4096,",
        "    'multiple_of': 256,",
        "    'n_heads': 32,",
        "    'n_layers': 32,",
        "    'norm_eps': 1e-06,",
        "    'vocab_size': -1,",
        "}",
        "n_heads = params['n_heads']",
        "dim = params['dim']",
        "",
        "def unpermute(w):",
        "    return (",
        "        w.view(n_heads, 2, dim // n_heads // 2, dim)",
        "        .transpose(1, 2)",
        "        .reshape(dim, dim)",
        "    )",
        "",
        "def translate_state_dict_key(k):",
        "    k = k.replace('base_model.model.', '')",
        "    if k == 'model.embed_tokens.weight':",
        "        return 'tok_embeddings.weight'",
        "    if k == 'model.norm.weight':",
        "        return 'norm.weight'",
        "    if k == 'lm_head.weight':",
        "        return 'output.weight'",
        "    if k.startswith('model.layers.'):  # LLaMA decoder block",
        "        layer = k.split('.')[2]",
        "        if k.endswith('.self_attn.q_proj.weight'):",
        "            return f'layers.{layer}.attention.wq.weight'",
        "        if k.endswith('.self_attn.k_proj.weight'):",
        "            return f'layers.{layer}.attention.wk.weight'",
        "        if k.endswith('.self_attn.v_proj.weight'):",
        "            return f'layers.{layer}.attention.wv.weight'",
        "        if k.endswith('.self_attn.o_proj.weight'):",
        "            return f'layers.{layer}.attention.wo.weight'",
        "        if k.endswith('.mlp.gate_proj.weight'):",
        "            return f'layers.{layer}.feed_forward.w1.weight'",
        "        if k.endswith('.mlp.down_proj.weight'):",
        "            return f'layers.{layer}.feed_forward.w2.weight'",
        "        if k.endswith('.mlp.up_proj.weight'):",
        "            return f'layers.{layer}.feed_forward.w3.weight'",
        "        if k.endswith('.input_layernorm.weight'):",
        "            return f'layers.{layer}.attention_norm.weight'",
        "        if k.endswith('.post_attention_layernorm.weight'):",
        "            return f'layers.{layer}.ffn_norm.weight'",
        "        if k.endswith('rotary_emb.inv_freq') or 'lora' in k:",
        "            return None",
        "        raise NotImplementedError(k)",
        "    raise NotImplementedError(k)",
        "",
        "new_state_dict = {}",
        "for k, v in lora_model_sd.items():",
        "    new_k = translate_state_dict_key(k)",
        "    if new_k is None:",
        "        continue",
        "    new_state_dict[new_k] = unpermute(v) if ('wq' in new_k or 'wk' in new_k) else v",
        "torch.save(new_state_dict, OUTPUT_PATH / 'consolidated.00.pth')",
        "with open(OUTPUT_PATH / 'params.json', 'w', encoding='utf-8') as f:",
        "    json.dump(params, f)",
        "print(f'Saved original LLaMA-style checkpoint to {OUTPUT_PATH}')",
    ]


def heredoc_command(args: argparse.Namespace, lines: Iterable[str]) -> str:
    code = "\n".join(lines)
    env = " ".join(
        [
            f"BASE_MODEL={q(args.base_model)}",
            f"ADAPTER_WEIGHTS={q(args.adapter_weights)}",
            f"OUTPUT_DIR={q(args.output_dir)}",
        ]
    )
    return f"{env} {q(args.python)} - <<'PY'\n{code}\nPY"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a dry-run command for Huatuo-Llama-Med-Chinese LoRA "
            "adapter merge/export. The helper prints commands only; it does "
            "not import torch, transformers, or peft and does not execute the export."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("hf", "state-dict"),
        required=True,
        help="Export target: Hugging Face hf_ckpt/ or original LLaMA ckpt/ layout.",
    )
    parser.add_argument(
        "--base-model",
        required=True,
        help="Base model local path or Hugging Face id; emitted as BASE_MODEL.",
    )
    parser.add_argument(
        "--adapter-weights",
        default=SOURCE_ADAPTER_DEFAULT,
        help=(
            "PEFT LoRA adapter directory or Hugging Face id. Defaults to the "
            "legacy source-script adapter value to make that inherited assumption visible."
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output root; hf mode writes hf_ckpt/ and state-dict mode writes ckpt/ under it.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable to place in the generated command (default: python).",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.adapter_weights == SOURCE_ADAPTER_DEFAULT:
        print(
            "WARNING: --adapter-weights is using the source-script default "
            f"{SOURCE_ADAPTER_DEFAULT!r}; replace it with the Huatuo adapter path/id for real exports.",
            file=sys.stderr,
        )
    if args.mode == "state-dict":
        print(f"WARNING: {LLAMA_7B_WARNING}", file=sys.stderr)
        lines = state_dict_exporter_lines()
        expected = "${OUTPUT_DIR}/ckpt/{consolidated.00.pth,params.json}"
    else:
        lines = hf_exporter_lines()
        expected = "${OUTPUT_DIR}/hf_ckpt/"

    print("# Dry-run LoRA checkpoint export command")
    print("# Review the command before executing it in a prepared ML environment.")
    print(f"# BASE_MODEL env var: {args.base_model}")
    print(f"# ADAPTER_WEIGHTS: {args.adapter_weights}")
    print(f"# OUTPUT_DIR root: {args.output_dir}")
    print(f"# Expected output: {expected}")
    if args.mode == "state-dict":
        print(f"# WARNING: {LLAMA_7B_WARNING}")
    print("\n# Command:\n")
    print(heredoc_command(args, lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

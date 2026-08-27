#!/usr/bin/env python3
"""Print a ShardFormer model-family checklist."""
import argparse

FAMILIES = [
    "BERT", "GPT-2", "GPT-J", "OPT", "Bloom", "LLaMA", "Mistral", "Mixtral",
    "Falcon", "T5", "ViT", "SAM", "Whisper", "Qwen", "ChatGLM", "DeepSeek", "BLIP2",
]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="List model-family signals to check before using ShardFormer.")
    ap.add_argument("--family", help="Optional family name to search for.")
    args = ap.parse_args()
    rows = [f for f in FAMILIES if not args.family or args.family.lower() in f.lower()]
    for fam in rows:
        print(f"- {fam}: check installed Transformers version, ColossalAI policy support, TP/SP/PP compatibility, and optional fused-kernel dependencies.")
    if not rows:
        print("No known family matched. Consider a custom policy or route away from ShardFormer.")

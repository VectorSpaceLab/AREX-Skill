#!/usr/bin/env python3
"""Print ColossalAI application package/environment notes."""
import argparse

APPS = {
    "colossalchat": ("coati", "RLHF/SFT/preference optimization; requires model/data assets and often flash-attn/PEFT/datasets."),
    "colossal-llama": ("colossal_llama", "LLaMA continual pretraining/SFT; requires tokenizer/model/data prep and CUDA GPUs."),
    "colossaleval": ("colossal_eval", "LLM evaluation configs; may require vLLM/OpenAI/evaluation data packages."),
    "colossalqa": ("colossalqa", "Retrieval QA; can pin older torch/langchain/chromadb stack and requires documents/vector store/LLM."),
    "colossalmoe": ("colossal_moe", "MoE train/infer examples; requires CUDA GPUs and model/data assets."),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Show first-party ColossalAI application package and isolation notes.")
    ap.add_argument("app", nargs="?", choices=sorted(APPS), help="Specific application key.")
    args = ap.parse_args()
    keys = [args.app] if args.app else sorted(APPS)
    for key in keys:
        pkg, note = APPS[key]
        print(f"{key}: package={pkg}; isolate environment; {note}")

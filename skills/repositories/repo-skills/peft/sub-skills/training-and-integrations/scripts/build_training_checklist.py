#!/usr/bin/env python3
"""Build a PEFT training integration checklist without downloads or training."""

import argparse
import json
from textwrap import indent


WORKFLOW_ITEMS = {
    "trainer": [
        "Load the base model/tokenizer with the intended dtype and device strategy.",
        "For k-bit quantized training, call prepare_model_for_kbit_training before PEFT wrapping.",
        "Wrap with get_peft_model before constructing Trainer unless the trainer owns peft_config wrapping.",
        "Print or inspect trainable parameters before training.",
        "Save with trainer.save_model() or a main-process PEFT save path.",
    ],
    "accelerate": [
        "Create Accelerator with the intended mixed precision and project settings.",
        "Build the PEFT model before accelerator.prepare(...).",
        "Optimize only parameters where requires_grad is true.",
        "Use accelerator.backward(loss) in the loop.",
        "Save from accelerator.is_main_process using accelerator.unwrap_model(model).save_pretrained(...).",
    ],
    "diffusers": [
        "Install diffusers only when adapting diffusion training workflows.",
        "Identify whether adapters belong on UNet, text encoder, or both.",
        "Freeze non-adapter parameters and verify trainable names.",
        "Keep VAE dtype, latent caching, resolution, and pipeline arguments in the Diffusers script.",
        "Save adapters in a PEFT-compatible format; route third-party conversion to save-load-merge.",
    ],
}

BACKEND_ITEMS = {
    "single-gpu": [
        "Start with a tiny batch/sequence or image resolution before scaling.",
        "Prefer bf16 on supported hardware; use fp16 only with adapter dtype checks.",
        "Avoid distributed-only save or launcher assumptions.",
    ],
    "fsdp": [
        "Use an Accelerate FSDP config and launch with accelerate launch.",
        "Set fsdp_use_orig_params: false when memory savings are required.",
        "Apply peft.utils.other.fsdp_auto_wrap_policy to the trainer FSDP plugin.",
        "Switch to FULL_STATE_DICT before final trainer.save_model() when adapters must reload normally.",
        "Do not assume bitsandbytes 8-bit is compatible with FSDP.",
    ],
    "deepspeed": [
        "Use an Accelerate DeepSpeed config and choose the ZeRO stage deliberately.",
        "Keep gradient_accumulation_steps aligned between config and training args.",
        "Use zero3_init_flag for large ZeRO-3 initialization when needed.",
        "Save through Trainer/Accelerate/DeepSpeed helpers instead of rank-local save_pretrained calls.",
        "Review offload settings as memory-throughput tradeoffs.",
    ],
    "cpu": [
        "Use CPU for parser, config, and tiny logic checks rather than real fine-tuning.",
        "Skip GPU-only quantization/offload claims unless separately verified on target hardware.",
        "Keep output directories local and small for smoke tests.",
    ],
}

QUANTIZED_ITEMS = [
    "Install and verify the selected quantization backend before loading the model.",
    "Use prepare_model_for_kbit_training for k-bit bitsandbytes training before PEFT wrapping.",
    "Align quantization compute/storage dtype with trainer mixed precision and backend support.",
    "Save adapters separately when the quantized backend cannot safely merge adapter deltas.",
]

TROUBLESHOOTING_ITEMS = [
    "If FP16 unscale errors occur, check trainable adapter dtype or prefer bf16.",
    "If checkpointing fails, set use_cache=False and review use_reentrant for this backend.",
    "If examples fail, check upstream package API drift before changing PEFT semantics.",
    "If distributed save fails, use framework-aware main-process save helpers.",
]


def build_checklist(args):
    title = f"PEFT {args.workflow} checklist on {args.backend}"
    sections = [
        ("Workflow", WORKFLOW_ITEMS[args.workflow]),
        ("Backend", BACKEND_ITEMS[args.backend]),
        ("Troubleshooting", TROUBLESHOOTING_ITEMS),
    ]
    if args.quantized:
        sections.insert(2, ("Quantized training", QUANTIZED_ITEMS))
    return {"title": title, "quantized": args.quantized, "sections": sections}


def render_markdown(checklist):
    lines = [f"# {checklist['title']}", ""]
    for heading, items in checklist["sections"]:
        lines.extend([f"## {heading}", ""])
        lines.extend(f"- [ ] {item}" for item in items)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_text(checklist):
    chunks = [checklist["title"]]
    for heading, items in checklist["sections"]:
        body = "\n".join(f"[ ] {item}" for item in items)
        chunks.append(f"{heading}:\n{indent(body, '  ')}")
    return "\n\n".join(chunks) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=sorted(WORKFLOW_ITEMS), required=True)
    parser.add_argument("--backend", choices=sorted(BACKEND_ITEMS), required=True)
    parser.add_argument("--quantized", action="store_true", help="Include quantized/QLoRA integration checks.")
    parser.add_argument("--format", choices=["markdown", "text", "json"], default="markdown")
    args = parser.parse_args()

    checklist = build_checklist(args)
    if args.format == "json":
        print(json.dumps(checklist, indent=2))
    elif args.format == "text":
        print(render_text(checklist), end="")
    else:
        print(render_markdown(checklist), end="")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build a DALLE-pytorch transformer training command template."""
import argparse, json, shlex


def main():
    p = argparse.ArgumentParser(description="Build a command matching the DALLE-pytorch DALL-E training helper surface.")
    p.add_argument("--image-text-folder", required=True)
    src = p.add_mutually_exclusive_group()
    src.add_argument("--vae-path")
    src.add_argument("--dalle-path")
    p.add_argument("--taming", action="store_true")
    p.add_argument("--vqgan-model-path")
    p.add_argument("--vqgan-config-path")
    p.add_argument("--wds", default="")
    p.add_argument("--truncate-captions", action="store_true")
    p.add_argument("--random-resize-crop-lower-ratio", type=float, default=0.75)
    p.add_argument("--bpe-path")
    p.add_argument("--hug", action="store_true")
    p.add_argument("--chinese", action="store_true")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--learning-rate", type=float, default=3e-4)
    p.add_argument("--save-every-n-steps", type=int, default=1000)
    p.add_argument("--keep-n-checkpoints", type=int)
    p.add_argument("--dalle-output-file-name", default="dalle")
    p.add_argument("--dim", type=int, default=512)
    p.add_argument("--text-seq-len", type=int, default=256)
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--dim-head", type=int, default=64)
    p.add_argument("--attn-types", default="full")
    p.add_argument("--reversible", action="store_true")
    p.add_argument("--stable-softmax", action="store_true")
    p.add_argument("--shift-tokens", action="store_true")
    p.add_argument("--rotary-emb", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--amp", action="store_true")
    p.add_argument("--deepspeed", action="store_true")
    p.add_argument("--distributed-backend", choices=["deepspeed", "horovod"])
    p.add_argument("--ga-steps", type=int, default=1)
    p.add_argument("--wandb-name", default="dalle_train_transformer")
    p.add_argument("--wandb-entity")
    p.add_argument("--as-json", action="store_true")
    args = p.parse_args()

    cmd = ["python", "train_dalle.py"]
    def val(flag, value):
        if value is not None and value != "":
            cmd.extend([flag, str(value)])
    def fl(flag, enabled):
        if enabled:
            cmd.append(flag)

    val("--image_text_folder", args.image_text_folder)
    val("--vae_path", args.vae_path)
    val("--dalle_path", args.dalle_path)
    val("--vqgan_model_path", args.vqgan_model_path)
    val("--vqgan_config_path", args.vqgan_config_path)
    val("--wds", args.wds)
    val("--random_resize_crop_lower_ratio", args.random_resize_crop_lower_ratio)
    val("--bpe_path", args.bpe_path)
    val("--epochs", args.epochs)
    val("--batch_size", args.batch_size)
    val("--learning_rate", args.learning_rate)
    val("--save_every_n_steps", args.save_every_n_steps)
    val("--keep_n_checkpoints", args.keep_n_checkpoints)
    val("--dalle_output_file_name", args.dalle_output_file_name)
    val("--dim", args.dim)
    val("--text_seq_len", args.text_seq_len)
    val("--depth", args.depth)
    val("--heads", args.heads)
    val("--dim_head", args.dim_head)
    val("--attn_types", args.attn_types)
    val("--ga_steps", args.ga_steps)
    val("--wandb_name", args.wandb_name)
    val("--wandb_entity", args.wandb_entity)
    backend = "deepspeed" if args.deepspeed else args.distributed_backend
    val("--distributed_backend", backend)
    fl("--taming", args.taming)
    fl("--truncate_captions", args.truncate_captions)
    fl("--hug", args.hug)
    fl("--chinese", args.chinese)
    fl("--reversible", args.reversible)
    fl("--stable_softmax", args.stable_softmax)
    fl("--shift_tokens", args.shift_tokens)
    fl("--rotary_emb", args.rotary_emb)
    fl("--fp16", args.fp16)
    fl("--amp", args.amp)
    fl("--deepspeed", args.deepspeed)

    warnings = [
        "Validate image-text folders before training; WebDataset sources may stream network data.",
        "The historical helper calls CUDA, logs to W&B, and writes checkpoints.",
        "No --vae_path means OpenAIDiscreteVAE unless --taming is set; this can require torch <= 1.10 and downloads.",
        "Keep tokenizer and model hparams compatible when resuming checkpoints.",
    ]
    payload = {"command": cmd, "shell": " ".join(shlex.quote(x) for x in cmd), "warnings": warnings}
    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload["shell"])
        for warning in warnings:
            print(f"# WARNING: {warning}")


if __name__ == "__main__":
    main()

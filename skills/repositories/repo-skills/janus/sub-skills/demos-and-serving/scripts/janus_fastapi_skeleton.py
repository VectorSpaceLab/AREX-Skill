#!/usr/bin/env python3
"""Lazy-loading FastAPI skeleton for Janus / Janus-Pro demos.

Safe default: parser help works without importing FastAPI, torch, or model
libraries. Use --run-server to start the API.
"""

from __future__ import annotations

import argparse
import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Sequence


@lru_cache(maxsize=1)
def _load_runtime(model_id: str, family: str, device: str, dtype: str):
    import numpy as np
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM
    from janus.models import VLChatProcessor

    config = AutoConfig.from_pretrained(model_id)
    if hasattr(config, "language_config"):
        config.language_config._attn_implementation = "eager"

    processor = VLChatProcessor.from_pretrained(model_id)
    tokenizer = processor.tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)

    device_name = "cuda" if device == "auto" and torch.cuda.is_available() else device
    if device_name == "auto":
        device_name = "cpu"
    dtype_map = {
        "auto": torch.bfloat16 if device_name == "cuda" else torch.float32,
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    model = model.to(dtype=dtype_map[dtype])
    if device_name == "cuda":
        model = model.cuda().eval()
    else:
        model = model.to(device_name).eval()

    return {
        "model": model,
        "processor": processor,
        "tokenizer": tokenizer,
        "device": device_name,
        "dtype": dtype_map[dtype],
        "np": np,
        "torch": torch,
    }


def create_app(model_id: str, family: str, device: str, dtype: str):
    try:
        from fastapi import FastAPI, File, Form, HTTPException, UploadFile
        from fastapi.responses import JSONResponse, StreamingResponse
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - import-time diagnostics only.
        raise SystemExit(
            "Missing FastAPI demo dependencies. Install fastapi, uvicorn, and python-multipart before running the server."
        ) from exc

    app = FastAPI(title="Janus Demo Skeleton")

    def runtime():
        return _load_runtime(model_id, family, device, dtype)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "model_id": model_id, "family": family}

    @app.post("/understand_image_and_question/")
    async def understand_image_and_question(
        file: UploadFile = File(...),
        question: str = Form(...),
        seed: int = Form(42),
        top_p: float = Form(0.95),
        temperature: float = Form(0.1),
    ):
        rt = runtime()
        torch = rt["torch"]
        np = rt["np"]
        model = rt["model"]
        processor = rt["processor"]
        tokenizer = rt["tokenizer"]

        if rt["device"] == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.manual_seed(seed)
        torch.manual_seed(seed)
        np.random.seed(seed)

        image_data = await file.read()
        pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        conversation = [
            {"role": "<|User|>" if family == "janus-pro" else "User", "content": f"<image_placeholder>\n{question}", "images": [image_data]},
            {"role": "<|Assistant|>" if family == "janus-pro" else "Assistant", "content": ""},
        ]
        prepare_inputs = processor(conversations=conversation, images=[pil_image], force_batchify=True).to(rt["device"], dtype=rt["dtype"])
        inputs_embeds = model.prepare_inputs_embeds(**prepare_inputs)
        outputs = model.language_model.generate(
            inputs_embeds=inputs_embeds,
            attention_mask=prepare_inputs.attention_mask,
            pad_token_id=tokenizer.eos_token_id,
            bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            max_new_tokens=512,
            do_sample=False if temperature == 0 else True,
            use_cache=True,
            temperature=temperature,
            top_p=top_p,
        )
        answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
        return JSONResponse({"response": answer})

    @app.post("/generate_images/")
    async def generate_images(
        prompt: str = Form(...),
        seed: int | None = Form(None),
        guidance: float = Form(5.0),
    ):
        rt = runtime()
        torch = rt["torch"]
        np = rt["np"]
        model = rt["model"]
        processor = rt["processor"]
        tokenizer = rt["tokenizer"]

        if rt["device"] == "cuda" and seed is not None:
            torch.cuda.manual_seed(seed)
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)

        width = 384
        height = 384
        parallel_size = 5
        messages = [{"role": "<|User|>" if family == "janus-pro" else "User", "content": prompt}, {"role": "<|Assistant|>" if family == "janus-pro" else "Assistant", "content": ""}]
        text = processor.apply_sft_template_for_multi_turn_prompts(conversations=messages, sft_format=processor.sft_format, system_prompt="")
        text = text + processor.image_start_tag
        input_ids = torch.LongTensor(tokenizer.encode(text)).to(rt["device"])

        tokens = torch.zeros((parallel_size * 2, len(input_ids)), dtype=torch.int, device=rt["device"])
        for i in range(parallel_size * 2):
            tokens[i, :] = input_ids
            if i % 2 != 0:
                tokens[i, 1:-1] = processor.pad_id
        inputs_embeds = model.language_model.get_input_embeddings()(tokens)
        generated_tokens = torch.zeros((parallel_size, 576), dtype=torch.int, device=rt["device"])

        pkv = None
        for i in range(576):
            outputs = model.language_model.model(inputs_embeds=inputs_embeds, use_cache=True, past_key_values=pkv)
            pkv = outputs.past_key_values
            hidden_states = outputs.last_hidden_state
            logits = model.gen_head(hidden_states[:, -1, :])
            logit_cond = logits[0::2, :]
            logit_uncond = logits[1::2, :]
            logits = logit_uncond + guidance * (logit_cond - logit_uncond)
            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            generated_tokens[:, i] = next_token.squeeze(dim=-1)
            next_token = torch.cat([next_token.unsqueeze(1), next_token.unsqueeze(1)], dim=1).reshape(-1)
            img_embeds = model.prepare_gen_img_embeds(next_token)
            inputs_embeds = img_embeds.unsqueeze(1)

        patches = model.gen_vision_model.decode_code(generated_tokens.to(dtype=torch.int), shape=[parallel_size, 8, width // 16, height // 16])
        dec = patches.to(torch.float32).cpu().numpy().transpose(0, 2, 3, 1)
        dec = np.clip((dec + 1) / 2 * 255, 0, 255).astype(np.uint8)

        def stream_images():
            for img in dec:
                buffer = io.BytesIO()
                Image.fromarray(img).save(buffer, format="PNG")
                buffer.seek(0)
                yield buffer.read()

        return StreamingResponse(stream_images(), media_type="multipart/related")

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lazy-loading Janus / Janus-Pro FastAPI demo skeleton.")
    parser.add_argument("--model-id", default="deepseek-ai/Janus-1.3B", help="Hugging Face model id.")
    parser.add_argument("--family", choices=["janus", "janus-pro"], default="janus", help="Model family for the service.")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto", help="Execution device for the lazy-loaded model.")
    parser.add_argument("--dtype", choices=["auto", "bfloat16", "float16", "float32"], default="auto", help="Model dtype for the lazy-loaded model.")
    parser.add_argument("--host", default="0.0.0.0", help="Server host.")
    parser.add_argument("--port", type=int, default=8000, help="Server port.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload mode for local development.")
    parser.add_argument("--run-server", action="store_true", help="Import FastAPI and start the service.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.run_server:
        print(json.dumps({"model_id": args.model_id, "family": args.family, "device": args.device, "dtype": args.dtype, "run_server": False}, indent=2, sort_keys=True))
        return 0

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Missing uvicorn. Install fastapi, uvicorn, and python-multipart before starting the service.") from exc

    app = create_app(args.model_id, args.family, args.device, args.dtype)
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

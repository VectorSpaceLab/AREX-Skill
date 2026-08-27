#!/usr/bin/env python3
"""Bundled simple ChatGLM2-6B FastAPI server adapted from the repository sample.

Safe check: `python simple_api_server.py --help`.
Running without --dry-run loads model weights and opens a local listener.
"""
from __future__ import annotations

import argparse
import datetime as _dt
from typing import Any

import torch
from fastapi import FastAPI, Request
import uvicorn
from transformers import AutoModel, AutoTokenizer

app = FastAPI(title="ChatGLM2-6B simple API")
model: Any = None
tokenizer: Any = None
cuda_device = "cuda:0"


def torch_gc() -> None:
    if torch.cuda.is_available():
        with torch.cuda.device(cuda_device):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


@app.post("/")
async def create_item(request: Request):
    global model, tokenizer
    if model is None or tokenizer is None:
        return {"response": "model not loaded", "history": [], "status": 503, "time": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    payload = await request.json()
    prompt = payload.get("prompt")
    history = payload.get("history") or []
    if not isinstance(prompt, str):
        return {"response": "prompt must be a string", "history": history, "status": 400, "time": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    response, history = model.chat(
        tokenizer,
        prompt,
        history=history,
        max_length=payload.get("max_length") or 2048,
        top_p=payload.get("top_p") or 0.7,
        temperature=payload.get("temperature") or 0.95,
    )
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    torch_gc()
    return {"response": response, "history": history, "status": 200, "time": now}


def load_runtime(args: argparse.Namespace) -> None:
    global model, tokenizer, cuda_device
    cuda_device = f"cuda:{args.cuda_device}" if args.device == "cuda" else args.device
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, revision=args.revision)
    loaded = AutoModel.from_pretrained(args.model, trust_remote_code=True, revision=args.revision)
    if args.quantization_bit is not None:
        loaded = loaded.quantize(args.quantization_bit)
    if args.device == "cuda":
        loaded = loaded.cuda()
    elif args.device == "cpu":
        loaded = loaded.float()
    elif args.device == "mps":
        loaded = loaded.to("mps")
    else:
        loaded = loaded.cuda() if torch.cuda.is_available() else loaded.float()
    model = loaded.eval()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Local model directory or Hub id")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda", "mps"), default="cuda")
    parser.add_argument("--cuda-device", default="0")
    parser.add_argument("--quantization-bit", type=int, choices=(4, 8), default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dry-run", action="store_true", help="Validate arguments without loading weights or opening a listener")
    args = parser.parse_args()
    if args.dry_run:
        print(f"would load {args.model!r} on {args.device} and serve http://{args.host}:{args.port}/")
        return 0
    load_runtime(args)
    uvicorn.run(app, host=args.host, port=args.port, workers=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

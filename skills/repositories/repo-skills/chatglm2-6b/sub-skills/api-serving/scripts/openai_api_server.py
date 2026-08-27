#!/usr/bin/env python3
"""Bundled OpenAI-compatible ChatGLM2-6B FastAPI server.

Safe check: `python openai_api_server.py --help` or `--dry-run`.
Running without --dry-run loads model weights and opens a local listener.
"""
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import time
from typing import Any, Literal

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from transformers import AutoModel, AutoTokenizer

model: Any = None
tokenizer: Any = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


app = FastAPI(lifespan=lifespan, title="ChatGLM2-6B OpenAI-compatible API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "owner"


class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelCard] = []


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class DeltaMessage(BaseModel):
    role: Literal["user", "assistant", "system"] | None = None
    content: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str = "chatglm2-6b"
    messages: list[ChatMessage]
    temperature: float | None = None
    top_p: float | None = None
    max_length: int | None = None
    stream: bool = False


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length"]


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Literal["stop", "length"] | None = None


class ChatCompletionResponse(BaseModel):
    model: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    choices: list[ChatCompletionResponseChoice | ChatCompletionResponseStreamChoice]
    created: int = Field(default_factory=lambda: int(time.time()))


@app.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(data=[ModelCard(id="chatglm2-6b")])


def request_to_query_history(request: ChatCompletionRequest) -> tuple[str, list[list[str]]]:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must be non-empty")
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="last message must have role user")
    query = request.messages[-1].content
    prev_messages = list(request.messages[:-1])
    if prev_messages and prev_messages[0].role == "system":
        query = prev_messages.pop(0).content + query
    history: list[list[str]] = []
    if len(prev_messages) % 2 == 0:
        for index in range(0, len(prev_messages), 2):
            if prev_messages[index].role == "user" and prev_messages[index + 1].role == "assistant":
                history.append([prev_messages[index].content, prev_messages[index + 1].content])
    return query, history


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    global model, tokenizer
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    query, history = request_to_query_history(request)
    if request.stream:
        return EventSourceResponse(predict(query, history, request.model), media_type="text/event-stream")
    response, _ = model.chat(tokenizer, query, history=history, max_length=request.max_length, top_p=request.top_p, temperature=request.temperature)
    choice = ChatCompletionResponseChoice(index=0, message=ChatMessage(role="assistant", content=response), finish_reason="stop")
    return ChatCompletionResponse(model=request.model, choices=[choice], object="chat.completion")


async def predict(query: str, history: list[list[str]], model_id: str):
    global model, tokenizer
    first = ChatCompletionResponse(model=model_id, choices=[ChatCompletionResponseStreamChoice(index=0, delta=DeltaMessage(role="assistant"))], object="chat.completion.chunk")
    yield first.model_dump_json(exclude_unset=True)
    current_length = 0
    for new_response, _ in model.stream_chat(tokenizer, query, history):
        if len(new_response) == current_length:
            continue
        new_text = new_response[current_length:]
        current_length = len(new_response)
        chunk = ChatCompletionResponse(model=model_id, choices=[ChatCompletionResponseStreamChoice(index=0, delta=DeltaMessage(content=new_text))], object="chat.completion.chunk")
        yield chunk.model_dump_json(exclude_unset=True)
    final = ChatCompletionResponse(model=model_id, choices=[ChatCompletionResponseStreamChoice(index=0, delta=DeltaMessage(), finish_reason="stop")], object="chat.completion.chunk")
    yield final.model_dump_json(exclude_unset=True)
    yield "[DONE]"


def load_runtime(args: argparse.Namespace) -> None:
    global model, tokenizer
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
    parser.add_argument("--quantization-bit", type=int, choices=(4, 8), default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print(f"would load {args.model!r} on {args.device} and serve OpenAI-compatible API at http://{args.host}:{args.port}/v1")
        return 0
    load_runtime(args)
    uvicorn.run(app, host=args.host, port=args.port, workers=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

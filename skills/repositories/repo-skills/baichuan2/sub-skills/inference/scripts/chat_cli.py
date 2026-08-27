#!/usr/bin/env python3
"""Interactive Baichuan2 Chat terminal demo.

This helper adapts the Baichuan2 terminal chat behavior with configurable
model, dtype, streaming, and multiline-editor handling. `--help` and
`--dry-run` do not import Transformers or load model weights.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "baichuan-inc/Baichuan2-13B-Chat"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an interactive Baichuan2 Chat CLI. Use Chat checkpoints, not Base checkpoints.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default=os.environ.get("BAICHUAN2_MODEL", DEFAULT_MODEL), help="Hugging Face model id or local Chat-model directory.")
    parser.add_argument("--dtype", choices=("auto", "float16", "bfloat16", "float32"), default=os.environ.get("BAICHUAN2_DTYPE", "float16"), help="Model weight dtype. 'auto' omits torch_dtype.")
    parser.add_argument("--device-map", default=os.environ.get("BAICHUAN2_DEVICE_MAP", "auto"), help="Transformers device_map value; use 'none' to omit.")
    parser.add_argument("--no-trust-remote-code", action="store_false", dest="trust_remote_code", default=True, help="Disable trust_remote_code. Baichuan2 HF models normally require it.")
    parser.add_argument("--editor", default=os.environ.get("EDITOR", "vim"), help="Editor command for multiline input triggered by 'vim' or 'multiline'.")
    parser.add_argument("--disable-editor", action="store_true", help="Disable the multiline editor command.")
    stream_group = parser.add_mutually_exclusive_group()
    stream_group.add_argument("--stream", dest="stream", action="store_true", default=True, help="Start with streaming generation enabled.")
    stream_group.add_argument("--no-stream", dest="stream", action="store_false", help="Start with streaming generation disabled.")
    parser.add_argument("--prompt", help="Run one prompt and exit instead of entering the interactive loop.")
    parser.add_argument("--max-new-tokens", type=int, help="Optional override for model.generation_config.max_new_tokens.")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved launch configuration and exit before importing model dependencies.")
    return parser


def import_colors():
    try:
        from colorama import Fore, Style, init

        init(autoreset=False)
        return Fore, Style
    except Exception:
        class Plain:
            BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
            BRIGHT = NORMAL = DIM = RESET_ALL = ""

        return Plain(), Plain()


def dtype_from_name(name: str):
    if name == "auto":
        return None
    import torch

    mapping = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    return mapping[name]


def dry_run(args: argparse.Namespace) -> None:
    editor_command = None if args.disable_editor else args.editor
    config = {
        "model": args.model,
        "dtype": args.dtype,
        "device_map": None if args.device_map == "none" else args.device_map,
        "trust_remote_code": args.trust_remote_code,
        "stream_initially_enabled": args.stream,
        "editor_command": editor_command,
        "one_shot_prompt": bool(args.prompt),
        "max_new_tokens": args.max_new_tokens,
        "interactive_commands": ["exit", "quit", "clear", "stream", "vim", "multiline"],
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))
    if editor_command:
        editor_binary = shlex.split(editor_command)[0]
        if shutil.which(editor_binary) is None:
            print(f"WARNING: editor command '{editor_binary}' is not on PATH; use --editor or --disable-editor.")
    if "Base" in os.path.basename(str(args.model)):
        print("WARNING: the CLI expects a Baichuan2 Chat checkpoint, not a Base checkpoint.")


def load_model_and_tokenizer(args: argparse.Namespace):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.generation.utils import GenerationConfig

    print(f"Loading tokenizer: {args.model}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        use_fast=False,
        trust_remote_code=args.trust_remote_code,
    )

    model_kwargs: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    if args.device_map != "none":
        model_kwargs["device_map"] = args.device_map
    dtype = dtype_from_name(args.dtype)
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype

    print(f"Loading model: {args.model}", flush=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)
    try:
        model.generation_config = GenerationConfig.from_pretrained(args.model)
    except Exception as exc:  # pragma: no cover - depends on model artifacts
        print(f"WARNING: could not load GenerationConfig from {args.model}: {exc}", flush=True)
    if args.max_new_tokens is not None:
        model.generation_config.max_new_tokens = args.max_new_tokens
    model.eval()

    if not hasattr(model, "chat"):
        raise RuntimeError("Loaded model does not expose model.chat(...); use a Baichuan2 Chat checkpoint.")

    if torch.cuda.is_available():
        print(f"CUDA devices visible: {torch.cuda.device_count()}", flush=True)
    return model, tokenizer


def maybe_empty_mps_cache() -> None:
    try:
        import torch

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()
    except Exception:
        pass


def clear_screen(Fore: Any, Style: Any) -> list[dict[str, str]]:
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    print(
        Fore.YELLOW
        + Style.BRIGHT
        + "Baichuan2 chat CLI. Type a prompt, 'stream' to toggle streaming, 'clear' to reset history, "
          "'vim'/'multiline' for editor input, and 'exit' to quit."
        + Style.RESET_ALL
    )
    return []


def read_multiline_prompt(editor: str) -> str:
    if not editor:
        raise RuntimeError("Multiline editor is disabled.")
    command = shlex.split(editor)
    if not command:
        raise RuntimeError("Editor command is empty.")
    if shutil.which(command[0]) is None:
        raise RuntimeError(f"Editor executable '{command[0]}' was not found on PATH.")

    handle = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False, suffix=".txt")
    path = Path(handle.name)
    handle.close()
    try:
        exit_code = subprocess.call(command + [str(path)])
        if exit_code != 0:
            raise RuntimeError(f"Editor exited with status {exit_code}.")
        return path.read_text(encoding="utf-8")
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def chat_once(model: Any, tokenizer: Any, messages: list[dict[str, str]], stream: bool, Fore: Any, Style: Any) -> str:
    import torch

    response = ""
    print(Fore.CYAN + Style.BRIGHT + "\nBaichuan 2: " + Style.NORMAL, end="", flush=True)
    with torch.inference_mode():
        if stream:
            position = 0
            try:
                for response in model.chat(tokenizer, messages, stream=True):
                    print(response[position:], end="", flush=True)
                    position = len(response)
                    maybe_empty_mps_cache()
            except KeyboardInterrupt:
                print("\n[interrupted]", flush=True)
            print(flush=True)
        else:
            response = model.chat(tokenizer, messages)
            print(response, flush=True)
            maybe_empty_mps_cache()
    return response


def interactive_loop(args: argparse.Namespace, model: Any, tokenizer: Any) -> None:
    Fore, Style = import_colors()
    messages = clear_screen(Fore, Style)
    stream = args.stream
    editor = "" if args.disable_editor else args.editor

    while True:
        try:
            prompt = input(Fore.GREEN + Style.BRIGHT + "\nUser: " + Style.NORMAL)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        command = prompt.strip().lower()
        if command in {"exit", "quit"}:
            break
        if command == "clear":
            messages = clear_screen(Fore, Style)
            continue
        if command == "stream":
            stream = not stream
            print(Fore.YELLOW + f"({'enabled' if stream else 'disabled'} streaming)" + Style.RESET_ALL)
            continue
        if command in {"vim", "multiline"}:
            try:
                prompt = read_multiline_prompt(editor)
            except Exception as exc:
                print(Fore.RED + f"Multiline input failed: {exc}" + Style.RESET_ALL)
                continue
            print(prompt)
            if not prompt.strip():
                continue

        messages.append({"role": "user", "content": prompt})
        response = chat_once(model, tokenizer, messages, stream, Fore, Style)
        if response:
            messages.append({"role": "assistant", "content": response})

    print(Style.RESET_ALL)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        dry_run(args)
        return 0

    if "Base" in os.path.basename(str(args.model)):
        print("WARNING: this CLI expects a Baichuan2 Chat checkpoint, not a Base checkpoint.", flush=True)

    model, tokenizer = load_model_and_tokenizer(args)
    if args.prompt is not None:
        Fore, Style = import_colors()
        messages = [{"role": "user", "content": args.prompt}]
        response = chat_once(model, tokenizer, messages, args.stream, Fore, Style)
        return 0 if response or not args.stream else 1

    interactive_loop(args, model, tokenizer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

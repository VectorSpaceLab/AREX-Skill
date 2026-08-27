#!/usr/bin/env python3
"""Bundled Gradio ChatGLM2-6B chat demo.

Safe check: `python gradio_chat_demo.py --help`.
Running without --dry-run loads model weights and opens a local Gradio UI.
"""
from __future__ import annotations

import argparse
from typing import Any


def parse_text(text: str) -> str:
    lines = [line for line in text.split("\n") if line != ""]
    count = 0
    for index, line in enumerate(lines):
        if "```" in line:
            count += 1
            items = line.split("`")
            lines[index] = f'<pre><code class="language-{items[-1]}">' if count % 2 else "<br></code></pre>"
        elif index > 0:
            if count % 2 == 1:
                for old, new in [("`", "\\`"), ("<", "&lt;"), (">", "&gt;"), (" ", "&nbsp;"), ("*", "&ast;"), ("_", "&lowbar;"), ("-", "&#45;"), (".", "&#46;"), ("!", "&#33;"), ("(", "&#40;"), (")", "&#41;"), ("$", "&#36;")]:
                    line = line.replace(old, new)
            lines[index] = "<br>" + line
    return "".join(lines)


def load_model(model_id: str, revision: str | None, device: str, quantization_bit: int | None) -> tuple[Any, Any]:
    from transformers import AutoModel, AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, revision=revision)
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True, revision=revision)
    if quantization_bit is not None:
        model = model.quantize(quantization_bit)
    if device == "cuda" or (device == "auto" and torch.cuda.is_available()):
        model = model.cuda()
    elif device == "mps":
        model = model.to("mps")
    else:
        model = model.float()
    return tokenizer, model.eval()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Local model directory or Hub id")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda", "mps"), default="auto")
    parser.add_argument("--quantization-bit", type=int, choices=(4, 8), default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print(f"would load {args.model!r} on {args.device} and launch Gradio")
        return 0

    import gradio as gr
    import mdtex2html

    tokenizer, model = load_model(args.model, args.revision, args.device, args.quantization_bit)

    def postprocess(_self: object, y: list[tuple[str | None, str | None]] | None) -> list[tuple[str | None, str | None]]:
        if y is None:
            return []
        return [(None if q is None else mdtex2html.convert(q), None if r is None else mdtex2html.convert(r)) for q, r in y]

    gr.Chatbot.postprocess = postprocess  # type: ignore[attr-defined]

    def predict(user_input: str, chatbot: list[tuple[str, str]], max_length: int, top_p: float, temperature: float, history: list[list[str]], past_key_values: Any):
        chatbot.append((parse_text(user_input), ""))
        for response, history, past_key_values in model.stream_chat(tokenizer, user_input, history, past_key_values=past_key_values, return_past_key_values=True, max_length=max_length, top_p=top_p, temperature=temperature):
            chatbot[-1] = (parse_text(user_input), parse_text(response))
            yield chatbot, history, past_key_values

    def reset_user_input():
        return gr.update(value="")

    def reset_state():
        return [], [], None

    with gr.Blocks() as demo:
        gr.HTML("""<h1 align="center">ChatGLM2-6B</h1>""")
        chatbot = gr.Chatbot()
        with gr.Row():
            with gr.Column(scale=4):
                user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=10)
                submit = gr.Button("Submit", variant="primary")
            with gr.Column(scale=1):
                clear = gr.Button("Clear History")
                max_length = gr.Slider(0, 32768, value=8192, step=1, label="Maximum length")
                top_p = gr.Slider(0, 1, value=0.8, step=0.01, label="Top P")
                temperature = gr.Slider(0, 1, value=0.95, step=0.01, label="Temperature")
        history = gr.State([])
        past_key_values = gr.State(None)
        submit.click(predict, [user_input, chatbot, max_length, top_p, temperature, history, past_key_values], [chatbot, history, past_key_values], show_progress=True)
        submit.click(reset_user_input, [], [user_input])
        clear.click(reset_state, outputs=[chatbot, history, past_key_values], show_progress=True)
    demo.queue().launch(server_name=args.host, server_port=args.port, share=False, inbrowser=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

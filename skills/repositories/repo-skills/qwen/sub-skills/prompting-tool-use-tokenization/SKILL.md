---
name: prompting-tool-use-tokenization
description: "Route Qwen system prompts, ReAct/tool use, OpenAI-style function
  calling, ChatML, special tokens, tokenizer safety, and BPE merge workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen Prompting, Tool Use, and Tokenization

Use this sub-skill when the user wants Qwen-specific system prompts, ReAct prompting, OpenAI-style function calling, Hugging Face Agent patterns, function-calling fine-tune samples, ChatML behavior, special-token safety, or tokenizer BPE merge extension.

## Safe start

- Use `scripts/validate_function_call_messages.py` before debugging a function-calling request or fine-tune sample.
- Use `scripts/qwen_tokenizer_merge_helper.py` for a safe local BPE-merge helper when extending tokenizer merge files.
- Keep prompt/tool behavior separate from model loading and server launch.

## Routes

| User request | Read |
| --- | --- |
| System prompts, role/language/task/behavior control, or stable assistant behavior across turns | `references/system-prompts.md` |
| ReAct template, function schemas, OpenAI-compatible message conversion, `Observation:` stop words, fine-tune samples for function calling | `references/function-calling-and-react.md` |
| ChatML roles, `<|im_start|>`, `<|im_end|>`, `<|endoftext|>`, pad/eod, special-token injection prevention, BPE merges | `references/tokenization-and-chatml.md` |
| Invalid role order, streaming function calls, tokenizer decode issues, special-token injection, or fine-tune sample mistakes | `references/troubleshooting.md` |

## Boundaries

- For loading a model before calling `chat`, use `../inference-model-loading/SKILL.md`.
- For launching an OpenAI-compatible server, use `../serving-deployment/SKILL.md`.
- For fine-tuning command plans, use `../finetuning-quantization/SKILL.md`.
- For plugin/tool benchmark reproduction, use `../evaluation-reproduction/SKILL.md`.

## Operating rules

- Qwen's OpenAI-style function calling is implemented through ReAct text conversion, not through a separate hidden tool runtime.
- The local API server rejects function calling with streaming; route users to non-streaming requests when `functions` are present.
- Do not allow untrusted text containing special-token surface forms to be treated as control tokens unless the user deliberately wants that behavior.
- Do not add ordinary vocabulary tokens casually; Qwen's tokenizer documentation discourages adding regular tokens and preserves extra special tokens for controlled uses.

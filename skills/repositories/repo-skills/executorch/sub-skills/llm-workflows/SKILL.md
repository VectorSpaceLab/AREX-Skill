---
name: llm-workflows
description: "Plan ExecuTorch LLM export and on-device runner workflows,
  including native export_llm, Optimum ExecuTorch, tokenizer/model assets,
  backend choices, Android/iOS/C++ runners, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# llm-workflows

Use this sub-skill when the user wants to export or run LLMs with ExecuTorch, including Llama/Gemma/Qwen/Whisper-like examples, `export_llm`, Optimum ExecuTorch, C++ LLM runners, Android/iOS deployment, tokenizer handling, or QNN/iOS/CUDA/Metal LLM backend choices.

## First Questions

1. Which model family and source weights/tokenizer are available locally?
2. Is the user using native ExecuTorch LLM export or Optimum ExecuTorch?
3. Which backend/runtime is the target: CPU, CUDA, Metal/MPS, Vulkan, QNN, iOS, Android, or C++ host?
4. Is this only command planning, or are large downloads/builds/device runs authorized?

## Safe Planner

```bash
python scripts/plan_llm_export.py --model llama --backend cpu --method native --output-dir artifacts/llama-cpu
python scripts/plan_llm_export.py --model llama --backend qnn --method optimum --quantization 4bit
```

The planner prints required assets and command shapes; it does not download weights, build runners, or run inference.

## Cross-Links

- Export fundamentals: `../export-runtime/SKILL.md`.
- Backend choice: `../backend-selection/SKILL.md`.
- Qualcomm LLM deployment: `../qualcomm/SKILL.md`.
- Build runners/libraries: `../setup-build/SKILL.md`.
- Performance and ETDump: `../profiling-debugging/SKILL.md`.


---
name: jarvis
description: "Use JARVIS, HuggingGPT, EasyTool, and TaskBench for agent tool
  orchestration, multimodal model routing, concise tool instruction, and
  task-automation evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# JARVIS

Use this repo skill when a task names JARVIS, HuggingGPT, EasyTool, or TaskBench, or when the user is working on task-planning agents, model/tool selection, multimodal expert-model orchestration, concise tool instructions, or task-automation benchmarks from this repository family.

JARVIS is a script-oriented research repository, not one unified installable Python distribution. Start by choosing the subproject route, then use its references and bundled helpers before running credentialed, networked, or heavyweight native commands.

## Environment note

There is no single repo-wide install. Use the chosen sub-skill's instructions for the exact workflow. For a private inspection environment that can read the bundled helpers for all three subprojects, install the EasyTool and TaskBench requirements plus `tiktoken` and then let the sub-skill guidance add any extra packages or external tools it needs:

```bash
pip install -r easytool/requirements.txt
pip install -r taskbench/requirements.txt
pip install tiktoken==0.3.3
```

The HuggingGPT config inspector only needs a YAML parser and the bundled helper script; the heavy local model-server stack remains optional and is documented in the `hugginggpt-chat` sub-skill.

## Route by task

- **HuggingGPT/JARVIS chat orchestration**: use [sub-skills/hugginggpt-chat/SKILL.md](sub-skills/hugginggpt-chat/SKILL.md) for CLI/server mode, `/hugginggpt`, `/tasks`, `/results`, task planning, model selection, response generation, `config.default/lite/gradio/azure` decisions, web UI wiring, Hugging Face endpoint use, and optional local model-server boundaries.
- **EasyTool tool instruction workflows**: use [sub-skills/easytool/SKILL.md](sub-skills/easytool/SKILL.md) for FuncQA, ToolBench, ToolBench retrieval, RestBench, `main.py` options, data preparation, external `toolenv/tools`, progress files, and the known `util` import workaround.
- **TaskBench benchmark workflows**: use [sub-skills/taskbench/SKILL.md](sub-skills/taskbench/SKILL.md) for task-automation datasets, OpenAI-compatible inference, evaluation metrics, graph generation/sampling/visualization, Back-Instruct construction, formatting, and batch evaluation.

## Fast start

1. Identify which subproject owns the user request. Do not mix TaskBench benchmark evaluation with EasyTool's tool-instruction experiments unless the user explicitly asks to compare them.
2. Inspect the working checkout with the safe root helper before running native scripts:

   ```bash
   python scripts/check_jarvis_environment.py --repo-root <jarvis-repo-root>
   ```

   The helper checks files, optional Python packages, config placeholders, and selected toolchain signals without network calls or model downloads.
3. For chat/server tasks, check credentials and inference mode before starting services. Lite remote operation still needs usable OpenAI and Hugging Face credentials.
4. For EasyTool and TaskBench inference/data-generation tasks, treat OpenAI-compatible endpoints, API keys, RapidAPI keys, downloaded datasets, and external tool code as explicit prerequisites.
5. For local HuggingGPT model serving, do not assume this skill verified CUDA, torch, diffusers, ControlNet, ffmpeg, or model weights. Follow the `hugginggpt-chat` local-model references and verify hardware/model artifacts separately.

## References

- [references/repo-overview.md](references/repo-overview.md) summarizes the three subprojects, their workflow boundaries, and shared concepts.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import, credential, network, data, backend, and subproject-routing failures.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence paths for refresh decisions.
- [scripts/check_jarvis_environment.py](scripts/check_jarvis_environment.py) is the shared safe diagnostic helper.

## Avoid

- Do not run dataset downloads, remote LLM calls, RapidAPI calls, local model downloads, local model-server startup, npm installs, or long benchmark jobs unless the user explicitly approves those side effects and supplies required credentials or artifacts.
- Do not claim CPU inspection proves HuggingGPT local CUDA model serving.
- Do not route generic OpenAI, Hugging Face, LangChain, or LLM-evaluation questions here unless the task specifically uses JARVIS, HuggingGPT, EasyTool, TaskBench, or their data/config/output formats.
- Do not depend on the original checkout for runtime guidance. Use this skill's bundled references and helpers; pass a checkout path only when a helper or native command explicitly needs user-provided source files.

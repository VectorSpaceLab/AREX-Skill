---
name: inference
description: "Routes MOSS chat inference tasks for prompt formatting, PyTorch
  and Jittor CLI choices, generation parameters, and checkpoint/device
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MOSS inference

Use this sub-skill when a task asks how to chat with MOSS locally, build a
MOSS-formatted prompt, choose a checkpoint for generation, configure generation
parameters, or prepare safe CLI/API commands without launching a model.

## Read this when

- The user asks for local MOSS chat, one-shot generation, multi-turn history, or
  prompt marker syntax.
- The task mentions `moss_cli_demo.py`, `moss_inference.py`, `Inference`,
  `DEFAULT_PARAS`, `top_p`, `temperature`, `max_iterations`, or `device_map`.
- You need to choose FP16 versus INT4/INT8 checkpoints for a GPU budget.
- You need to validate a model/GPU combination before running a command.
- The task asks about optional Jittor generation or why quantized MOSS fails on
  more than one GPU.

## Route elsewhere

- For low-level `MossConfig`, `MossTokenizer`, `MossForCausalLM`, quantization
  internals, or import smoke checks, read
  [../model-runtime/SKILL.md](../model-runtime/SKILL.md).
- For FastAPI, Gradio, and Streamlit deployment, read
  [../serving/SKILL.md](../serving/SKILL.md).
- For SFT training data and fine-tuning, read
  [../fine-tuning-data/SKILL.md](../fine-tuning-data/SKILL.md).
- For shared model catalog and memory table context, read
  [../../references/model-overview.md](../../references/model-overview.md).

## Operating workflow

1. **Start with the prompt format.** MOSS conversations begin with the canonical
   meta instruction and use `<|Human|>: ...<eoh>` followed by `<|MOSS|>:` for
   generation. Multi-turn history appends previous MOSS responses ending with
   `<eom>`.
2. **Decide whether tools/plugins are in scope.** Plugin SFT data uses extra
   sections such as `<|Inner Thoughts|>:...<eot>`, `<|Commands|>:...<eoc>`, and
   `<|Results|>:...<eor>`. Read
   [references/workflows.md](references/workflows.md) before adding those
   markers to an inference prompt.
3. **Choose the checkpoint/device plan.** FP16 `moss-moon-003-sft` can use
   model parallelism with Accelerate. Quantized INT4/INT8 checkpoints are
   documented as single-GPU only.
4. **Build safe commands before execution.** Use
   [scripts/build_moss_prompt.py](scripts/build_moss_prompt.py) for prompt text
   and command suggestions,
   [scripts/inspect_cli_flags.py](scripts/inspect_cli_flags.py) for flag/model
   validation, and [scripts/run_moss_generation.py](scripts/run_moss_generation.py)
   as a dry-run-first generation template. These helpers do not download model
   weights unless `run_moss_generation.py --execute` is explicitly supplied.
5. **Run real generation only after prerequisites are explicit.** A full run can
   download Hugging Face checkpoints, allocate tens of GB of GPU memory, and
   enter an interactive loop or long generation. Confirm model cache/network,
   GPU memory, and expected runtime before executing.

## Safe helper examples

```bash
python path/to/moss/sub-skills/inference/scripts/build_moss_prompt.py \
  --query "Hello MOSS" --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0

python path/to/moss/sub-skills/inference/scripts/build_moss_prompt.py \
  --query "How did Mark Zuckerberg create Facebook?" --enable-tool web-search --json

python path/to/moss/sub-skills/inference/scripts/inspect_cli_flags.py \
  --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0,1 --json
```

The last command intentionally returns nonzero because quantized checkpoints do
not support model parallelism in the repo demos.

## References

- [references/workflows.md](references/workflows.md) — prompt construction,
  programmatic inference, generation defaults, and checkpoint/device recipes.
- [references/cli-catalog.md](references/cli-catalog.md) — PyTorch and Jittor
  CLI flags, model choices, and safe command composition.
- [references/troubleshooting.md](references/troubleshooting.md) — prompt,
  checkpoint, CUDA/OOM, quantized, Jittor, and stop-token failures.
- [scripts/build_moss_prompt.py](scripts/build_moss_prompt.py) — safe prompt and
  command suggestion helper.
- [scripts/inspect_cli_flags.py](scripts/inspect_cli_flags.py) — safe CLI flag
  validator.
- [scripts/run_moss_generation.py](scripts/run_moss_generation.py) —
  dry-run-first generation template; `--execute` is opt-in and heavyweight.

## Answering checklist

- Include the exact MOSS markers when constructing prompts.
- Name whether the plan is FP16, INT4, or INT8 and whether model parallelism is
  allowed.
- Separate safe dry-run helpers from real generation commands.
- Do not imply that a prompt helper has run the model.
- Keep checkpoint downloads, network access, and GPU allocation explicit.

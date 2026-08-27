---
name: model-runtime
description: "Routes MOSS model-runtime tasks for config, tokenizer, causal
  language model classes, checkpoint families, quantization, and backend
  readiness."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MOSS model runtime

Use this sub-skill when the task is about understanding or validating the MOSS
runtime components rather than chatting, serving, or fine-tuning. It covers the
Hugging Face-style PyTorch implementation in `models/`, the optional quantized
runtime, and the model/checkpoint constraints that determine whether a workflow
can run locally.

## Read this when

- A task names `MossConfig`, `MossTokenizer`, `MossModel`, or `MossForCausalLM`.
- You need to choose between `moss-moon-003-sft`, `moss-moon-003-sft-int8`, and
  `moss-moon-003-sft-int4` for memory, backend, or quantization reasons.
- You need to verify imports or CUDA readiness without downloading a 16B
  checkpoint.
- You are debugging `trust_remote_code`, Triton/GPTQ, model-parallel loading,
  missing tokenizer files, or checkpoint memory failures.
- You need source-backed architecture facts before writing inference, serving,
  or training code.

## Route elsewhere

- For prompt markers, generation defaults, CLI command construction, or Jittor
  chat use, read [../inference/SKILL.md](../inference/SKILL.md).
- For FastAPI, Gradio, and Streamlit services, read
  [../serving/SKILL.md](../serving/SKILL.md).
- For SFT data format, no-loss spans, and DeepSpeed fine-tuning, read
  [../fine-tuning-data/SKILL.md](../fine-tuning-data/SKILL.md).
- For cross-cutting install guidance and model catalog context, read
  [../../references/install-and-dependencies.md](../../references/install-and-dependencies.md)
  and [../../references/model-overview.md](../../references/model-overview.md).

## Operating workflow

1. **Identify the runtime surface.** MOSS exposes a source-checkout runtime, not
   a conventional installable Python distribution. For local checkout work,
   ensure the checkout root is importable so `models.configuration_moss`,
   `models.modeling_moss`, and `models.tokenization_moss` resolve.
2. **Check the configuration before allocating weights.** Read
   [references/model-architecture.md](references/model-architecture.md) for the
   verified defaults: 107008 vocabulary entries, 2048 context length, 4096
   hidden size, 28 layers, 16 heads, rotary dimension 64, `<eom>` EOS id
   106068, and quantization fields `wbits`/`groupsize`.
3. **Select the checkpoint family.** Use FP16 `moss-moon-003-sft` for model
   parallelism; use `*-int4` or `*-int8` only on one GPU. Quantized models use
   GPTQ/Triton support and are documented as not supporting model parallelism.
4. **Verify imports safely.** Run the bundled
   [scripts/check_model_runtime.py](scripts/check_model_runtime.py) with a
   local checkout only when you need runtime evidence. It imports classes,
   instantiates a tiny model from a small config, and optionally checks CUDA
   without calling `from_pretrained`.
5. **Escalate to real checkpoint loading only when required.** Loading actual
   MOSS checkpoints can download large model files and require substantial GPU
   memory. Treat that as a task-specific execution decision, not a default
   diagnostic.

## Safe validation commands

From any working directory with the required dependencies installed:

```bash
python path/to/moss/sub-skills/model-runtime/scripts/check_model_runtime.py --help
python path/to/moss/sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --json
python path/to/moss/sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --cuda --json
```

The helper accepts a user-supplied checkout root. It does not rely on the
checkout used to generate this skill and does not download checkpoints.

## References

- [references/model-architecture.md](references/model-architecture.md) — class
  roles, verified configuration defaults, tokenizer behavior, checkpoint
  families, and quantization notes.
- [references/troubleshooting.md](references/troubleshooting.md) — import,
  dependency, CUDA, quantization, checkpoint, and memory failure recovery.
- [scripts/check_model_runtime.py](scripts/check_model_runtime.py) — safe
  import/signature/CUDA diagnostic helper.

## Quality checks before answering a task

- Do not claim a full MOSS checkpoint works unless it was actually loaded in the
  target environment.
- Do not use a CPU import check as proof of CUDA generation, quantized Triton
  kernels, model parallelism, or fine-tuning.
- Do not recommend multi-GPU model parallelism for `*-int4` or `*-int8`
  checkpoints.
- Do not tell users to run source demo scripts as the only guidance; use this
  skill's bundled references and helpers to construct safe commands first.

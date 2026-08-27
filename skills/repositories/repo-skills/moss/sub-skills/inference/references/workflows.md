# MOSS inference workflows

## Purpose

Read this when constructing MOSS chat prompts, choosing generation parameters,
or preparing PyTorch/Jittor inference commands. The examples here are safe
command templates; running a full model may download checkpoints and allocate
large GPU memory.

## Prompt construction

A basic MOSS prompt is:

```text
<meta instruction lines>
<|Human|>: user text<eoh>
<|MOSS|>:
```

For a multi-turn conversation, append the decoded MOSS response ending in
`<eom>`, then the next human turn:

```text
<meta instruction lines>
<|Human|>: Hi there<eoh>
<|MOSS|>: Hello! How may I assist you today?<eom>
<|Human|>: Recommend five sci-fi films<eoh>
<|MOSS|>:
```

The canonical meta instruction describes MOSS as a helpful, honest, harmless,
bilingual assistant. When plugins are not in scope, the capability switches are
all disabled and inner thoughts are disabled. Plugin-augmented data enables
inner thoughts and one or more tools, then uses additional markers.

## Tool/plugin prompt sections

Plugin SFT records use these sections inside each turn:

| Section | Start | End | Notes |
| --- | --- | --- | --- |
| Human | `<|Human|>:` | `<eoh>` | User text. |
| Inner thoughts | `<|Inner Thoughts|>:` | `<eot>` | Enabled in plugin-style records. |
| Commands | `<|Commands|>:` | `<eoc>` | Can contain `Search(...)`, `Calculate(...)`, `Solve(...)`, or `Text2Image(...)`. |
| Tool responses | `<|Results|>:` | `<eor>` | Tool output or `None`. |
| MOSS | `<|MOSS|>:` | `<eom>` | Assistant response. |

Do not invent external tools at inference time unless the surrounding system
actually provides them. The repo data demonstrates tool command formatting; it
does not bundle live search, calculator, solver, or image generation services.

## Programmatic inference wrapper

The source `Inference` wrapper accepts:

```python
Inference(model=None, model_dir=None, parallelism=True, device_map=None)
Inference.forward(data: str, paras: Optional[Dict[str, float]] = None) -> List[str]
```

Default generation parameters in the wrapper include:

| Parameter | Default | Meaning |
| --- | ---: | --- |
| `temperature` | 0.7 | Sampling temperature. |
| `top_k` | 0 | Top-k filtering disabled by default in the wrapper. |
| `top_p` | 0.8 | Nucleus sampling threshold. |
| `repetition_penalty` | 1.02 | Penalizes repeated tokens. |
| `max_iterations` | 512 | Maximum generation loop iterations. |
| `regulation_start` | 512 | Length-penalty adjustment starts after this step. |
| `length_penalty` | 1 | Stop-token probability adjustment factor. |
| `max_time` | 60 | Generation time limit in seconds. |

The wrapper prepends the meta instruction prefix to input text and samples with
a custom streaming top-k/top-p loop. It moves tensors to CUDA in the generation
path, so a CPU-only import is not enough to prove wrapper generation.

## PyTorch command workflow

Use the bundled dry-run-first template instead of a source-checkout demo when a
task needs an executable command:

```bash
python sub-skills/inference/scripts/run_moss_generation.py \
  --query "Hello MOSS" --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0
```

Available `--model-name` choices are:

- `OpenMOSS-Team/moss-moon-003-sft`
- `OpenMOSS-Team/moss-moon-003-sft-int8`
- `OpenMOSS-Team/moss-moon-003-sft-int4`

`--gpu` is a comma-separated CUDA-visible device list used by the optional
`--execute` path. If more than one device is given with an INT4 or INT8 model,
the helper returns nonzero because quantized models do not support model
parallelism.

## Optional Jittor workflow

Source evidence included an optional Jittor implementation with `sample` and
`greedy` generation, sampling controls, and a boolean GPU mode. The generated
skill does not bundle a Jittor executable because that backend requires a
separately installed Jittor runtime and checkpoint conversion. Use the bundled
PyTorch template unless a task explicitly provides and verifies Jittor.

## Safe preflight helpers

Use bundled helpers before running real generation:

```bash
python sub-skills/inference/scripts/build_moss_prompt.py --query "Hello MOSS" --json
python sub-skills/inference/scripts/inspect_cli_flags.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --json
```

These helpers validate strings and command choices only. They do not prove a
checkpoint is cached, a GPU has enough memory, or generation quality.

## Bundled dry-run generation template

Use `scripts/run_moss_generation.py` when a task needs a self-contained template
rather than the original interactive source demo:

```bash
python sub-skills/inference/scripts/run_moss_generation.py --query "Hello MOSS" --json
python sub-skills/inference/scripts/run_moss_generation.py --query "Hello MOSS" --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --execute
```

The first command is safe and prints the prompt plus execution plan. The second
command is intentionally heavy: it imports Transformers, can download the
checkpoint, and runs generation. Do not use `--execute` as a routine validation
step.

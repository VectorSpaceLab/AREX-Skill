# Inference Pipeline Workflows

## Workflow 1: Choose Pipeline vs AutoClass vs Generation

Use this decision tree before writing code:

1. Is the task a standard Transformers task with normal preprocessing and postprocessing?
   - Yes: start with `pipeline()`.
   - No: use AutoClass or a custom pipeline.
2. Is the main task text/chat generation where decoding control matters?
   - Yes: use the sibling `generation` sub-skill for `generate()`, `GenerationConfig`, streamers, and chat templates.
   - No: `pipeline("text-generation")` is fine for high-level demos and simple app integration.
3. Is the problem processor/tokenizer setup rather than inference?
   - Yes: route to `tokenizers-processors`.
4. Is memory placement or quantization the hard part?
   - Yes: combine this sub-skill with `quantization-integrations`.
5. Is the model custom or requires `trust_remote_code=True`?
   - First review the code and pin the revision; route implementation details to `model-extension`.

## Workflow 2: Minimal Reproducible Pipeline

```python
from transformers import pipeline

pipe = pipeline(
    task="text-classification",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    revision="main",
    dtype="auto",
)
result = pipe("A tiny input proves the shape.")
assert isinstance(result, list)
assert {"label", "score"} <= set(result[0])
```

Production-grade changes:

- Pin `revision` to a commit or immutable tag when reproducibility matters.
- Avoid default models in tests and examples.
- Add `local_files_only=True` for offline CI or air-gapped validation.
- Add task-specific output assertions.
- Add dependency checks for PyTorch and modality packages.

## Workflow 3: Offline Local Model Smoke

Use this when a model is already downloaded or exported into a local directory:

```python
from transformers import AutoConfig, pipeline

model_dir = "./model"
config = AutoConfig.from_pretrained(model_dir, local_files_only=True)
assert config.model_type

pipe = pipeline(
    task="text-classification",
    model=model_dir,
    local_files_only=True,
    device=-1,
    dtype="auto",
)
print(pipe("offline smoke"))
```

Checklist:

- The directory should include `config.json` and the required weight, tokenizer, processor, or image/audio processor files for the task.
- If `AutoConfig` succeeds but `pipeline()` fails, inspect the missing component named in the exception.
- If a model is gated or private, authenticate before download in a separate setup step and still use `local_files_only=True` in offline tests.
- Do not use URLs as input for offline tests; use local sample files or synthetic arrays where the task supports them.

## Workflow 4: Device and Dtype Setup

CPU-first portable code:

```python
pipe = pipeline("text-classification", model=model_id, device=-1, dtype="auto")
```

Single GPU:

```python
pipe = pipeline("text-generation", model=model_id, device=0, dtype="float16")
```

Automatic device placement for large models:

```python
pipe = pipeline("text-generation", model=model_id, device_map="auto", dtype="auto")
```

Rules:

- Use exactly one of `device` or `device_map`.
- Use `device_map="auto"` when model weights need to be sharded or offloaded; this usually depends on Accelerate-compatible loading.
- Prefer `dtype="auto"` until hardware is known.
- `float16` is usually for CUDA inference, not CPU.
- `bfloat16` requires hardware/backend support.
- If dtype loading fails, retry with default dtype before changing task code.

## Workflow 5: Batch Inference Safely

Pipelines can batch lists, datasets, and generators through `batch_size`, but batching is not always faster.

```python
from transformers import pipeline

pipe = pipeline("text-classification", model=model_id, device=0)
texts = ["short sample", "another sample"]
outputs = pipe(texts, batch_size=2, truncation=True)
assert len(outputs) == len(texts)
```

Use batching when:

- throughput matters more than latency;
- a GPU or accelerator is available;
- input sequence lengths or image sizes are regular;
- OOM handling is planned and tested.

Avoid batching when:

- the workflow is latency-sensitive;
- the runtime is CPU-only;
- text lengths vary widely and padding can explode memory;
- output nesting will make application code fragile.

For dataset streaming:

```python
from transformers import pipeline
from transformers.pipelines.pt_utils import KeyDataset

pipe = pipeline("text-classification", model=model_id, device=0)
for output in pipe(KeyDataset(dataset, "text"), batch_size=8, truncation="only_first"):
    consume(output)
```

## Workflow 6: Validate Text, Vision, Audio, Video, and Multimodal Tasks

Text classification:

```python
result = pipeline("text-classification", model=model_id)("good")
assert isinstance(result, list) and {"label", "score"} <= set(result[0])
```

Text generation:

```python
result = pipeline("text-generation", model=model_id)("hello", max_new_tokens=5, return_full_text=False)
assert isinstance(result, list) and "generated_text" in result[0]
```

Image classification:

```python
result = pipeline("image-classification", model=model_id)(images="image.png")
assert isinstance(result, list) and "score" in result[0]
```

ASR:

```python
result = pipeline("automatic-speech-recognition", model=model_id)(audio="audio.flac")
assert isinstance(result, dict) and "text" in result
```

Video classification:

```python
result = pipeline("video-classification", model=model_id)("clip.mp4")
assert isinstance(result, list) and "label" in result[0]
```

Visual question answering:

```python
result = pipeline("visual-question-answering", model=model_id)(image="image.png", question="What is shown?")
assert isinstance(result, list) and "answer" in result[0]
```

Multimodal tasks are more likely to require `processor`, `image_processor`, `video_processor`, or model-specific input names. If construction succeeds but call-time input validation fails, switch to explicit components and inspect the task pipeline's expected keyword names in this reference before changing the model.

## Workflow 7: Handle Hub, Auth, and Offline Constraints

Online public model:

```python
pipe = pipeline("image-classification", model="google/vit-base-patch16-224")
```

Private or gated model:

```python
pipe = pipeline("text-generation", model=model_id, token=True)
```

Offline local model:

```python
pipe = pipeline("text-generation", model="./local-model", local_files_only=True)
```

Guidance:

- Use environment-managed Hugging Face auth; do not hard-code tokens.
- Use `revision` to pin Hub code and weights.
- Combine `local_files_only=True` with local sample inputs for deterministic offline smoke tests.
- If a model requires custom code, set `trust_remote_code=True` only after review and pinning.

## Workflow 8: Tiny Smoke Script Usage

Dry-run advice only, no network by default:

```bash
python sub-skills/inference-pipelines/scripts/pipeline_smoke.py \
  --task text-classification \
  --model ./local-model \
  --local-files-only
```

Run one tiny call when the environment and model are available:

```bash
python sub-skills/inference-pipelines/scripts/pipeline_smoke.py \
  --task text-classification \
  --model ./local-model \
  --text "small smoke" \
  --device -1 \
  --local-files-only \
  --run
```

Expected successful signals:

- `transformers` import succeeds and prints a version.
- `AutoConfig.from_pretrained` succeeds for local/config validation when a model is provided.
- Pipeline construction succeeds only when required model weights and optional dependencies exist.
- A tiny call returns a Python object and the script prints a short output summary.

Expected safe failures:

- Missing optional dependency: install the backend or modality package and rerun.
- Missing local files: provide a complete local model directory or omit `--local-files-only` intentionally.
- Task/model mismatch: choose a model compatible with the task or omit `--task` only if model metadata can infer it.

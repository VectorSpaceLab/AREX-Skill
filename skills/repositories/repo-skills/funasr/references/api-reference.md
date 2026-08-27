# FunASR API reference

This reference covers the public Python surface that appears in the common FunASR workflows. Use the sub-skill references for deeper recipes.

## Top-level import

- `import funasr` exposes the package version and import diagnostics.
- `from funasr import AutoModel` is the main local ASR entry point.
- `from funasr.auto.auto_model_vllm import AutoModelVLLM` is the LLM-ASR acceleration entry point.
- `funasr.get_import_errors()` returns recorded optional import failures so missing extras can be diagnosed without a traceback.

## `AutoModel`

Constructor shape:

```python
from funasr import AutoModel

model = AutoModel(
    model="paraformer-zh",
    device="cpu",
    hub="ms",
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    punc_model="ct-punc",
    spk_model="cam++",
    ncpu=4,
    disable_update=True,
)
```

### Common arguments

| Argument | Meaning | Notes |
|---|---|---|
| `model` | Main ASR or utility model id, or a local path | Common choices are SenseVoice and Paraformer families. |
| `device` | Torch device string | Examples: `cpu`, `cuda:0`, `mps`, `xpu`, `npu`. |
| `hub` | Remote model hub | `ms` or `hf`. |
| `vad_model` | VAD model id | Enables long-audio segmentation. |
| `vad_kwargs` | VAD overrides | Often used for `max_single_segment_time`. |
| `punc_model` | Punctuation model id | Optional. Useful for sentence segmentation and subtitle output. |
| `spk_model` | Speaker model id | Usually requires VAD. |
| `spk_mode` | Speaker routing mode | Common values: `default`, `vad_segment`, `punc_segment`. |
| `ncpu` | CPU thread count | Defaults to 4. |
| `disable_update` | Skip version check | Useful in controlled environments. |

### Input forms

`AutoModel.generate()` accepts:

- local audio file paths
- URLs
- raw audio bytes
- `BytesIO` objects
- `numpy.ndarray`
- `torch.Tensor`
- lists or tuples of the above
- `wav.scp` / aligned list files
- Kaldi archive references for supported loaders

### Primary methods

```python
results = model.generate(input=..., input_len=None, progress_callback=None, **cfg)
```

```python
results = model.inference(input=..., input_len=None, model=None, kwargs=None, key=None, progress_callback=None, **cfg)
```

```python
export_result = model.export(input=None, **cfg)
```

### Common runtime kwargs

- `language`
- `cache`
- `batch_size_s`
- `batch_size_threshold_s`
- `is_final`
- `hotword` / `hotwords`
- `postprocess_hotwords`
- `postprocess_hotword_file`
- `postprocess_hotword_threshold`
- `return_postprocess_hotword_matches`
- `sentence_timestamp`
- `output_timestamp`
- `return_time_stamps`
- `return_raw_text`
- `return_spk_res`
- `use_itn`

### Common result fields

| Field | Meaning |
|---|---|
| `key` | Sample id |
| `text` | Final transcript |
| `timestamp` / `timestamps` | Timing backbone |
| `sentence_info` | Sentence-level segments with optional speaker labels |
| `raw_text` | Pre-cleanup text when requested |
| `postprocess_hotword_matches` | Text-level hotword replacement details |

## `AutoModelVLLM`

Use `AutoModelVLLM` only for applicable LLM-ASR families. Its constructor shape is:

```python
from funasr.auto.auto_model_vllm import AutoModelVLLM

model = AutoModelVLLM(
    model="FunAudioLLM/Fun-ASR-Nano-2512",
    hub="ms",
    device="cuda:0",
    dtype="bf16",
    tensor_parallel_size=1,
    gpu_memory_utilization=0.8,
    max_model_len=4096,
    enforce_eager=False,
)
```

It exposes:

```python
results = model.generate(inputs, **kwargs)
```

Do not use it for Paraformer, SenseVoice, or Qwen3-ASR; those families route elsewhere.

## Helper functions

| Helper | Purpose | Route |
|---|---|---|
| `load_audio_text_image_video()` | Load files, URLs, bytes, arrays, or lists into a model-ready tensor | `python-asr-pipelines` |
| `load_bytes()` | Decode raw PCM or container-formatted audio bytes | `python-asr-pipelines` |
| `apply_postprocess_hotwords_to_results()` | Apply text-level hotword replacements after decoding | `python-asr-pipelines` |
| `rich_transcription_postprocess()` | Cleanup for transcript surface text | `python-asr-pipelines` |

## See also

- [`references/model-overview.md`](model-overview.md) for model-family selection
- [`references/data-formats.md`](data-formats.md) for audio, JSONL, and output shapes
- [`references/troubleshooting.md`](troubleshooting.md) for import and dependency recovery

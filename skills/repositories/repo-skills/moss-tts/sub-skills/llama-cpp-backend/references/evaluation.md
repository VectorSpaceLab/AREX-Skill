# Evaluation and batch inference

The llama.cpp backend can be evaluated by running generation over benchmark cases and saving one `pred.wav` per case. The backend's batch evaluator is a thin loop around `PipelineConfig`, `LlamaCppPipeline.generate()`, and a fixed benchmark directory convention.

## Benchmark case layout

Each case is stored as:

```text
<benchmark-dir>/
  <task>/
    <case-id>/
      prompt.wav       # optional reference audio; missing prompt means no reference
      label.txt        # required synthesis text
```

Generated output is stored as:

```text
<result-dir>/
  run_meta.json
  inference_summary.json
  <task>/
    <case-id>/
      pred.wav
```

`label.txt` is stripped and used as synthesis text. `prompt.wav`, when present, is passed as `reference_audio`. The generated waveform is saved at 24 kHz.

## Supported task names

Seed-TTS-style tasks:

- `seed-tts-zeroshot-zh`
- `seed-tts-zeroshot-en`
- `seed-tts-zeroshot-hard-zh`

CV3-style tasks:

- `cv3-crosslingual-en`
- `cv3-crosslingual-hard-en`
- `cv3-zeroshot-en`
- `cv3-zeroshot-hard-en`
- `cv3-crosslingual-zh`
- `cv3-crosslingual-hard-zh`
- `cv3-zeroshot-zh`
- `cv3-zeroshot-hard-zh`

Demo tasks:

- `demo-zh`
- `demo-en`

Language routing is task-name based: English tasks use `language="en"`, Chinese tasks use `language="zh"`.

## Self-contained batch loop

Use this pattern when a packaged batch command is unavailable or when you need custom filtering:

```python
from dataclasses import asdict, dataclass
from pathlib import Path
import json, time
import soundfile as sf
from moss_tts_delay.llama_cpp import LlamaCppPipeline, PipelineConfig

SAMPLE_RATE = 24000
TASK_LANGUAGE = {
    "seed-tts-zeroshot-zh": "zh",
    "seed-tts-zeroshot-en": "en",
    "seed-tts-zeroshot-hard-zh": "zh",
    "cv3-crosslingual-en": "en",
    "cv3-crosslingual-hard-en": "en",
    "cv3-zeroshot-en": "en",
    "cv3-zeroshot-hard-en": "en",
    "cv3-crosslingual-zh": "zh",
    "cv3-crosslingual-hard-zh": "zh",
    "cv3-zeroshot-zh": "zh",
    "cv3-zeroshot-hard-zh": "zh",
    "demo-zh": "zh",
    "demo-en": "en",
}

@dataclass
class CaseResult:
    task: str
    case_id: str
    success: bool
    audio_duration: float = 0.0
    generation_time: float = 0.0
    error: str = ""

def discover_cases(benchmark_dir: Path, tasks: list[str]):
    for task in tasks:
        task_dir = benchmark_dir / task
        if not task_dir.is_dir():
            continue
        for case_dir in sorted(p for p in task_dir.iterdir() if p.is_dir()):
            label = case_dir / "label.txt"
            prompt = case_dir / "prompt.wav"
            if label.exists():
                yield task, case_dir.name, prompt if prompt.exists() else None, label.read_text().strip()

def run_batch(config_path: str, benchmark_dir: str, result_dir: str, tasks: list[str], max_cases: int = 0):
    cfg = PipelineConfig.from_yaml(config_path)
    result_root = Path(result_dir)
    result_root.mkdir(parents=True, exist_ok=True)
    cases = list(discover_cases(Path(benchmark_dir), tasks))
    if max_cases > 0:
        cases = cases[:max_cases]
    results = []
    with LlamaCppPipeline(cfg) as pipeline:
        for task, case_id, prompt, text in cases:
            out_dir = result_root / task / case_id
            out_wav = out_dir / "pred.wav"
            t0 = time.time()
            try:
                wav = pipeline.generate(text=text, reference_audio=str(prompt) if prompt else None, language=TASK_LANGUAGE.get(task))
                if wav.size == 0:
                    raise RuntimeError("empty waveform")
                out_dir.mkdir(parents=True, exist_ok=True)
                sf.write(out_wav, wav, SAMPLE_RATE)
                elapsed = time.time() - t0
                results.append(CaseResult(task, case_id, True, len(wav) / SAMPLE_RATE, elapsed))
            except Exception as exc:
                results.append(CaseResult(task, case_id, False, generation_time=time.time() - t0, error=str(exc)))
    summary = {
        "total_cases": len(results),
        "succeeded": sum(r.success for r in results),
        "failed": sum(not r.success for r in results),
        "failures": [asdict(r) for r in results if not r.success],
    }
    (result_root / "inference_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary
```

For quick smoke evaluation, run only one or two cases with `max_cases` and force `max_new_tokens` low in the config or API override. For real metric evaluation, do not truncate generation.

## Summary fields

A useful run summary records:

- Config path or config identifier used.
- Benchmark root and task list.
- Sampling values: text temperature/top-p/top-k and audio temperature/top-p/top-k/repetition penalty.
- `max_new_tokens`.
- GGUF path or model identifier.
- `heads_backend` and `audio_backend`.
- Per-case success/failure and error text.
- Per-task success counts and average real-time factor when audio duration is known.

## Quantization-quality context

The released backend documentation reports Seed-TTS zero-shot quality for the llama.cpp backend with TensorRT audio tokenizer. Baseline values come from the original Hugging Face path; GGUF rows use the llama.cpp backend.

| Quantization | EN WER ↓ | EN SIM ↑ | ZH CER ↓ | ZH SIM ↑ |
|---|---:|---:|---:|---:|
| Hugging Face baseline | 1.79 | 71.46 | 1.32 | 77.05 |
| Q8_0 | 3.21 | 68.61 | 1.56 | 76.03 |
| Q6_K | 3.11 | 68.77 | 1.44 | 76.06 |
| Q5_K_M | 2.95 | 68.55 | 1.50 | 75.96 |
| Q4_K_M | 2.83 | 68.15 | 1.58 | 75.71 |

Use these as approximate regression context, not as universal acceptance thresholds: tokenizer backend, TensorRT engine shape, sampling overrides, hardware, and benchmark preprocessing can affect outcomes.

## Batch-eval pitfalls

- Missing `label.txt` means the case is skipped or invalid.
- Missing `prompt.wav` changes the run from voice cloning to no-reference synthesis for that case.
- Unknown task names should fail early; add a language mapping before using custom task names.
- Reusing a result directory can hide failures if existing `pred.wav` files are skipped. Disable skipping when re-running after config changes.
- Empty waveform should count as failure even if no exception was raised.
- TensorRT engine max shape can silently cap supported prompt/reference duration; rebuild engines with larger max shapes for longer audio.

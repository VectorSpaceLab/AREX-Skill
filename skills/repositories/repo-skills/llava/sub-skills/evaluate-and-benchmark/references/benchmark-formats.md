# Benchmark Formats

## When to read

Read this when deciding which benchmark command or converter to use.

## Supported benchmark families

| Benchmark | Input shape | Output shape | Typical command family | Notes |
| --- | --- | --- | --- | --- |
| VQAv2 | JSONL question rows with `question_id`, `image`, `text` | JSONL answers then submission JSON | `model_vqa_loader` + VQAv2 converter | Often chunked across GPUs |
| GQA | JSONL question rows with image references and answer text | JSONL answers | `model_vqa_loader` + GQA-style shell wrapper | May require official GQA assets |
| VizWiz | JSON or JSONL question rows with images | JSONL answers and upload bundle | `model_vqa` + converter/upload folder | Submission and image availability matter |
| ScienceQA | JSON or JSONL with `conversations` and optional image | JSONL answers plus evaluation JSON | `model_vqa_science` + ScienceQA eval | Option-only prompts are common |
| TextVQA | JSON annotation file plus result JSONL | accuracy report | `model_vqa` + TextVQA evaluator | OCR-style question normalization matters |
| POPE | question JSONL and category annotations | JSONL answers then class metrics | `model_vqa` + POPE evaluator | Short yes/no style |
| MME | official evaluation assets | answer files and official eval tool output | `model_vqa` + MME scripts | Needs official benchmark data |
| MMBench / CN | TSV question file | JSONL answers then Excel upload | `model_vqa_mmbench` + Excel converter | Often needs `--single-pred-prompt` |
| SEED | JSONL or benchmark-specific files | answer JSONL and upload artifacts | `model_vqa_loader` + SEED converter | Multi-GPU chunking common |
| LLaVA-Bench-Wild | questions JSONL + context JSONL + image folder | JSONL answers and GPT review files | `model_vqa` + GPT review scripts | Credentialed judge step |
| MM-Vet | JSONL-like question file plus image folder | JSONL answers and manual eval | `model_vqa` | Final scoring may be manual or notebook-based |
| Q-Bench / Q-Bench CN | JSON files and image directories | JSONL answers and upload file | `model_vqa` + Q-Bench converters | Use locale-specific datasets and image folders |

## Command families by output goal

- **Answer JSONL only**: use the base VQA modules.
- **Submission upload**: use the benchmark-specific converter after validating the answers.
- **Metric report**: use the evaluator module or official benchmark tool.
- **GPT judge review**: use the review scripts only if credentials and network access are present.

## Selection guidance

- Pick `model_vqa_loader` when the benchmark shell script splits work across GPUs.
- Pick `model_vqa_mmbench` when the input is TSV multiple-choice data.
- Pick `model_vqa_science` when the dataset is ScienceQA-style and may include image or text-only questions.
- Pick `model_vqa` for most single-GPU JSONL evaluation paths.

## What to verify before a run

- checkpoint path or hub id exists and matches the intended family
- `conv_mode` matches the model family
- image folder exists and contains the images referenced by the question file
- output directory is writable
- benchmark-specific converter dependencies such as `pandas` or `openpyxl` are installed when needed

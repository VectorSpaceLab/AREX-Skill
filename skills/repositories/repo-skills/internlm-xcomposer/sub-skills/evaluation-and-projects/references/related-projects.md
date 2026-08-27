# Related Projects: ShareGPT4V And DualFocus

This reference routes the repository's related project packages without requiring the original checkout. It records install constraints, data layouts, evaluation command families, converter ownership, and non-executing usage plans. Do not launch demos, download models/data, run Captioner inference, or start training from this sub-skill.

## Project Routing Matrix

| Task signal | Route | Notes |
| --- | --- | --- |
| "Evaluate ShareGPT4V on VQAv2/GQA/MMBench/..." | This sub-skill | Use the ShareGPT4V playground layout and converter/result expectations below. |
| "Convert ShareGPT4V/DualFocus predictions for submission" | This sub-skill plus `data-conversion.md` | Validate JSONL ids and output shape before server submission. |
| "Generate captions with ShareCaptioner" | This sub-skill for a safe plan only; execution requires model-inference-style CUDA approval | Batch captioner loads a large checkpoint and writes captions. |
| "Run ShareGPT4V demo" | Plan here, actual service launch outside this sub-skill | The Gradio app loads a model and opens a service port. |
| "Fine-tune ShareGPT4V" | Not owned here | Installation/data facts are preserved here; actual project training is external to this generated repo skill unless a future sub-skill owns it. |
| "Evaluate DualFocus" | This sub-skill | DualFocus released evaluation scripts/checkpoints; training code was not released in the evidence. |
| "Use XComposer model chat or OmniLive memory/service" | Sibling `model-inference` or `omnilive` | This sub-skill should only plan benchmark/project routing. |

## ShareGPT4V Package

### Identity and install constraints

- **Python package:** `share4v`.
- **Purpose:** ShareGPT4V model, evaluation utilities, ShareCaptioner batch caption generation, and demo app.
- **Python/dependency profile:** evidence package uses Python >=3.8; README install example used Python 3.10. Core pinned dependencies include Torch 2.0.1, TorchVision 0.15.2, Transformers 4.31.0, tokenizers <0.14, PEFT, bitsandbytes, xformers, gradio, fastapi/uvicorn, timm, openpyxl, and other VLM utilities. Train extras add deepspeed, ninja, wandb, and tensorboardX. FlashAttention installation was documented separately and requires compatible CUDA/build tooling.
- **License constraints:** code is Apache-2.0; data/model usage is research-oriented and constrained by ShareGPT4V data terms, LLaMA/Vicuna terms, and GPT-4-generated data restrictions. Treat datasets as non-commercial unless the user proves otherwise.

Safe install plan text can mention:

```bash
conda create -n share4v python=3.10 -y
conda activate share4v
pip install --upgrade pip
pip install -e .
pip install -e ".[train]"      # only if training is explicitly approved
pip install flash-attn --no-build-isolation  # only with compatible CUDA/build stack
```

Do not execute the install from this sub-skill.

### Data layout

ShareGPT4V data evidence names three JSON assets:

- `sharegpt4v_instruct_gpt4-vision_cap100k.json` (~134 MB).
- `share-captioner_coco_lcs_sam_1246k_1107.json` (~1.5 GB).
- `sharegpt4v_mix665k_cap23k_coco-ap9k_lcs3k_sam9k_div2k.json` (~1.2 GB).

The training/evaluation image layout is rooted under a project `data` directory with subtrees for LLaVA pretrain images, COCO train2017, SAM images, GQA images, OCR-VQA images, TextVQA train images, Visual Genome folders, ShareGPT4V JSONs, share_textvqa images, web-celebrity, web-landmark, and wikiart images. Web data was marked academic-only in the evidence.

### Model and quick-usage plan

The project exposes `load_pretrained_model`, `get_model_name_from_path`, and an `eval_model` helper for a single image prompt. Actual model loading is long CUDA inference and should be routed to an execution-capable inference workflow after the user supplies checkpoint, GPU, and license acceptance. For planning, collect:

- model path such as a ShareGPT4V 7B/13B checkpoint;
- optional base model path;
- image file(s), prompt, conversation mode, generation temperature/beam/token limits;
- output target and whether streaming/demo service is requested.

### Evaluation playground

Before task-specific data preparation, ShareGPT4V evaluation evidence requires a `playground` archive extracted under the project workspace. It contains custom annotations, scripts, and sample prediction files. Use this layout in plans:

```text
playground/data/eval/
  vqav2/
  gqa/
  vizwiz/
  scienceqa/
  textvqa/
  MME/
  mmbench/
  seed_bench/
  llava-bench-in-the-wild/
  mm-vet/
  qbench/
```

### ShareGPT4V evaluation families

| Benchmark | Data needed | GPU pattern | Local output | External step |
| --- | --- | --- | --- | --- |
| VQAv2 | COCO test2015 under `vqav2` | multi-GPU chunks | merged JSONL and EvalAI upload JSON | EvalAI submission server |
| GQA | official GQA data/eval scripts plus images | multi-GPU chunks | merged JSONL, `testdev_balanced_predictions.json`, official local eval output | no server if local official eval is available |
| VizWiz | test annotations and test images | single GPU in evidence | answers JSONL and upload JSON | EvalAI submission server |
| ScienceQA | images, `pid_splits.json`, `problems.json` | multi-GPU chunks | answer JSONL, output/result JSON | local evaluator; GPT4 variant scripts require judge access |
| TextVQA | TextVQA validation JSON and train images | multi-GPU chunks | merged JSONL and local TextVQA accuracy | no server for val accuracy |
| MME | MME image release and official eval tool | single GPU | answer JSONL, MME-formatted files, calculation output | no GPT judge; needs official tool |
| MMBench EN/CN | official dev TSV files | multi-GPU chunks | merged JSONL and `.xlsx` upload file | OpenCompass/MMBench server for official score |
| SEED image | SEED images and JSON | multi-GPU chunks | merged JSONL, upload JSONL, local accuracy | optional leaderboard submission |
| LLaVA-Bench | questions, images, context, GPT-4 reference answers | single GPU prediction | answer JSONL, review JSONL | GPT/OpenAI judge calls for score |
| MM-Vet | MM-Vet images and JSON | single GPU prediction | answer JSONL and converted result JSON | official/GPT evaluator for final score |
| QBench | LLVisionQA JSON and images | single GPU | answer JSONL, formatted dev evaluation | test split requires submission instructions/server |

### ShareCaptioner batch plan

The batch captioner expects:

- `--images-file`: a JSON list of image paths;
- `--save-path`: output JSON file;
- `--model-name`: captioner checkpoint, defaulting in evidence to a ShareCaptioner model id;
- `--batch-size` and `--num_gpus`.

Output shape is a JSON list of dictionaries, each mapping an input image path to its generated detailed caption. Execution loads `AutoModelForCausalLM`, `AutoTokenizer`, image processors, CUDA, and optionally multi-GPU dispatch. Do not run it from this sub-skill; produce a checklist and route actual generation to an inference-capable workflow.

### ShareGPT4V demo plan

The Gradio app exposes host, port, share flag, model path, and model name arguments, then loads the checkpoint and launches a service. It is a service launch and model inference task. This sub-skill may document requested ports and model path, but actual launch belongs outside this sub-skill after security/port approval.

## DualFocus Package

### Identity and install constraints

- **Python package:** `dualfocus`.
- **Purpose:** released evaluation code and checkpoints for DualFocus variants based on LLaVA/ShareGPT4V-style models.
- **Python/dependency profile:** package metadata mirrors ShareGPT4V's core pinned dependencies: Torch 2.0.1, TorchVision 0.15.2, Transformers 4.31.0, tokenizers <0.14, PEFT, bitsandbytes, xformers, gradio, fastapi/uvicorn, timm, openpyxl, and train extras. README install example used Python 3.9 plus optional FlashAttention.
- **Model-base requirement in eval scripts:** command patterns pass `--model-base lmsys/vicuna-7b-v1.5` even for checkpoints supplied by model id.
- **License constraints:** code Apache-2.0; data/checkpoints are research-oriented and constrained by LLaMA/Vicuna/GPT-4-derived data terms.
- **Training status:** evidence marked training code as not released. Do not promise DualFocus training support.

Safe install plan text can mention:

```bash
conda create -n DualFocus python=3.9 -y
conda activate DualFocus
pip install --upgrade pip
pip install -e .
pip install -e ".[train]"      # only if the user explicitly accepts external training deps
pip install flash-attn --no-build-isolation  # only with compatible CUDA/build stack
```

### DualFocus evaluation families

| Benchmark | Data needed | Command family | Local output | External step |
| --- | --- | --- | --- | --- |
| MMBench EN | `mmbench_dev_20230712.tsv` under `playground/data/eval/mmbench` | `dualfocus.eval.model_vqa_mmbench` sharded by GPU | merged JSONL and converted `.xlsx` | MMBench/OpenCompass submission server |
| SEED image | SEED images and `SEED-Bench.json` | `dualfocus.eval.model_vqa_seed` sharded by GPU | merged JSONL and upload JSONL, local accuracy | optional leaderboard submission |
| TextVQA | TextVQA val JSON and train images | `dualfocus.eval.model_vqa_textvqa` sharded by GPU | merged JSONL and local TextVQA eval | no server for val accuracy |
| GQA MCQ | GQA images/data/eval scripts plus MCQ JSONL | `dualfocus.eval.model_vqa_gqa` sharded by GPU | merged JSONL, converted official prediction JSON, local official eval | dataset and official eval script access |

GQA evidence uses a converted multiple-choice question dataset made with GPT-3.5. Treat that dataset and its source terms as an explicit dependency.

### Slurm versus local DualFocus

Local scripts split by `CUDA_VISIBLE_DEVICES`. Slurm scripts define `PARTITION`, `JOB_NAME`, `QUOTA_TYPE`, `GPUS`, `GPUS_PER_NODE`, and `CPUS_PER_TASK`, then launch one task per GPU. A plan should require the user to provide cluster-specific partition/quota values and should not assume defaults are valid on their cluster.

Known source-era caveat: some Slurm command patterns used `${IDX}` inside the `--answers-file` path while `--chunk-idx -1` lets each task infer rank. If adapting those scripts, confirm the launcher writes one file per chunk before attempting to merge.

## Related-Project Checklist

When answering a project request, include:

1. Package identity (`share4v` or `dualfocus`) and whether installation is only a plan.
2. Required checkpoint and base-model fields.
3. Required data/playground layout and licenses.
4. GPU pattern: single GPU, multi-GPU chunking, or Slurm.
5. Local artifacts: merged JSONL, result JSON, upload JSON, XLSX, score logs, or captions JSON.
6. External gates: EvalAI/OpenCompass/QBench/SEED submissions, GPT/OpenAI judges, or service ports.
7. Sibling route if the request becomes actual inference, service launch, fine-tuning, or reward modeling.

# Model and backend overview

This repository revolves around three user-facing workflow families.

## 1) Local Skywork-R1V3 inference

- Native scripts: `inference/inference_with_transformers.py`, `inference/inference_with_vllm.py`
- Typical model id: `Skywork/Skywork-R1V3-38B`
- Main backends: CUDA + Transformers, or CUDA + vLLM
- Important support code: `inference/utils.py`
- Heavy install recipe clues: `inference/setup.sh`

### Native behavior notes

- Transformers path uses `AutoModel.from_pretrained(..., torch_dtype=torch.bfloat16, use_flash_attn=True, trust_remote_code=True, device_map=split_model(...))`.
- The script loads image patches on CUDA and calls `model.chat(...)`.
- vLLM path uses `LLM(..., trust_remote_code=True, limit_mm_per_prompt={"image": 20}, gpu_memory_utilization=0.7)` and chat-template prompting.
- The command surface is intentionally simple: model path, image paths, question, and a few vLLM sampling knobs.

## 2) R1V4 API batch testing

- Native scripts: `r1v4/batch_nonstream.py`, `r1v4/batch_stream.py`, planner variants.
- Typical model ids: `skywork/r1v4-lite`, `skywork/r1v4-vl-planner-lite`
- Main backend: a Skywork or OpenAI-compatible HTTP endpoint
- Important support code: `r1v4/parse_utils.py`, `r1v4/visual.py`

### Native behavior notes

- Requests use `/api/v1/chat/completions`.
- Messages place image content before text content.
- Streaming mode reads SSE events and concatenates content chunks.
- Result files are JSONL with `image`, `question`, and `response` blocks.
- Tagged responses use `<think>`, `<tool_call>`, `<observation>`, and `<answer>`.

## 3) Evaluation reproduction

- Native scripts: `eval/vlmevalkit/eval_shell/*.sh`, `eval/EMMA/*.py`, `eval/MMK12/*.py`
- Main backends: a vLLM OpenAI-compatible server, benchmark datasets, and judge/API credentials
- Served model name in the stock flow: `r1v3-alpha`

### Native behavior notes

- The VLMEvalKit flow expects `USE_COT=1` for standard benchmark runs and `USE_COT=0` for PhyX.
- The shell recipes assume `LMDEPLOY_API_KEY` and `LMDEPLOY_API_BASE` point at the served model.
- Rule-based post-processing is used for MMMU and LogicVista boxed-answer normalization.
- EMMA-mini and MMK12 rely on dataset access, model access, and output directories that can be inspected without starting a full benchmark run.

## Safe helper environment

For the bundled helper scripts and validation checks, a small Python 3.11 environment with these packages is enough:

- `requests`
- `tqdm`
- `flask`
- `pillow`
- `pyyaml`
- `pandas`
- `openpyxl`

Do not install the heavy CUDA/model stack unless you are explicitly entering the local inference sub-skill.

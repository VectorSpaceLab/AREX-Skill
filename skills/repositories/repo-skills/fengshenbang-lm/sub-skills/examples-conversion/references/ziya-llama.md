# Ziya LLaMA inference, quantization, fine-tuning, and conversion

This reference helps plan Ziya workflows without mutating checkpoints. Use `../scripts/plan_ziya_conversion.py` for a dry-run conversion/fine-tune plan.

## Workflow decision table

| User goal | Preferred starting format | Main steps | Critical gates |
|---|---|---|---|
| HF inference | Full Hugging Face checkpoint | Load tokenizer/model with permitted local path or model ID; choose FP16 or 8-bit/4-bit path | `transformers`, `torch`, `accelerate`; optional `bitsandbytes`; model cache/download approval; VRAM/RAM. |
| HF 8-bit quantized inference | Full HF checkpoint | `device_map="auto"`, `load_in_8bit=True`-style load | `bitsandbytes` and CUDA-compatible stack; CPU-only is not enough for bitsandbytes GPU quantization. |
| llama.cpp inference | llama.cpp converted/quantized artifact | Convert outside this skill, then load through llama.cpp or `llama-cpp-python` | `llama.cpp` toolchain or `llama-cpp-python`; quantized file format; CPU/GPU layer choices. |
| Fengshen full fine-tune without tensor parallel | Fengshen single-shard directory | Convert HF to Fengshen if needed; train with `model_parallel_size=1` | Example path used 8 x 80GB A100 for 13B; requires CUDA, Deepspeed/Lightning, data files, checkpoint output. |
| Fengshen full fine-tune with tensor parallel | Fengshen tensor-parallel shard directory | Convert HF -> Fengshen -> TP shards; train with `model_parallel_size=<tp>` and `--use_mpu` | Example path used TP=8 on 24 x 24GB GPUs for 13B; shard divisibility and rank layout must match. |
| Export back to HF | Fengshen checkpoint or Lightning MP checkpoint | Use appropriate Fengshen-to-HF conversion utility | Large write; exact checkpoint layout matters. |
| Delta merge | Base LLaMA-compatible checkpoint plus delta checkpoint | Apply delta to produce full target HF checkpoint | Requires legal/access approval for base and delta; output path is overwritten by utility behavior if reused. |

## Model/source notes

- Ziya model IDs include 13B v1/v1.1, 13B pretrain, reward, and visual variants under the public `IDEA-CCNL` namespace.
- The fine-tune example for `Ziya-LLaMA-13B-Pretrain-v1` assumes the open checkpoint is provided as delta weights and must first be merged with a compatible base model to obtain a full HF checkpoint.
- Treat model IDs as possible network downloads. Ask for local cache/offline paths when operating in restricted environments.
- Verify license/access terms for base LLaMA-compatible checkpoints before constructing a full model from deltas.

## Data format for Ziya full-parameter fine-tune

The fine-tune dataset example is JSON records with prompt/output lists. A representative single record is:

```json
{
  "prompt": ["介绍一下人工智能。"],
  "output": ["人工智能是研究和构建智能系统的技术领域。"]
}
```

The collator formats each pair approximately as:

```text
<human>:<prompt>
<bot>:<output>
```

Labels mask the human prompt and train on the output tokens. If multiple prompts/outputs are present, the shortest list length determines how many pairs are used. Validate all records before training: both fields must be lists of strings, and prompt/output list lengths should match.

## HF / Fengshen / tensor-parallel flow

Run the dry-run planner first:

```bash
python ../scripts/plan_ziya_conversion.py --source-format hf --target fs-finetune --model-size 13b --gpus 8 --vram-gb 80
python ../scripts/plan_ziya_conversion.py --source-format hf --target fs-finetune --model-size 13b --gpus 24 --vram-gb 24
python ../scripts/plan_ziya_conversion.py --source-format delta --target fs-finetune --model-size 13b --has-base-model --gpus 24 --vram-gb 24
```

### Conversion sequence

1. **Delta to HF full checkpoint** if the source is delta weights.
   - Package module shape: `python -m fengshen.utils.apply_delta --base-model-path <base> --delta-path <delta> --target-model-path <new_hf_output>`.
   - Mutating: writes target model files and may remove an existing target directory. Use a new output directory.
2. **HF to Fengshen format** for Fengshen training.
   - Module shape: `python -m fengshen.utils.llama_convert.hf_to_fs --input_path <hf_model> --output_path <fs_model>`.
   - Mutating: writes Fengshen model/tokenizer/config outputs.
3. **Fengshen to TP shards** if tensor parallelism is needed.
   - Module shape: `python -m fengshen.utils.llama_convert.convert_fs_llama_tp --input_dir <fs_model> --output_dir <fs_tp_model> --model_parallel_size <tp>`.
   - Mutating: creates `part_<rank>` shard directories. Hidden size and attention head counts must be divisible by TP size.
4. **Fine-tune** with `--model_path` pointing to either the single Fengshen model directory or the TP root, `--tokenizer_path` pointing to tokenizer files, `--model_parallel_size` matching the chosen TP size, and `--use_mpu` when using Megatron model parallel utilities.
5. **Generate/evaluate** from the fine-tuned checkpoint only after matching `load_ckpt_path`, model format, tokenizer path, and model-parallel size.

### TP choice heuristics from example evidence

| Hardware shape | Example choice for 13B | Interpretation |
|---|---:|---|
| 8 GPUs with 80GB each | TP=1 | No tensor-parallel conversion needed; still heavy and uses Deepspeed/FP16. |
| 24 GPUs with 24GB each | TP=8 | Convert Fengshen model into 8 tensor-parallel shards; train across multiple nodes. |
| Fewer/smaller GPUs | No safe default | Consider inference/quantization or parameter-efficient methods outside the original full fine-tune example. |

If the user gives an explicit TP size, verify: number of GPUs is a multiple of TP size, checkpoint is sharded for the same TP size, model config dimensions are divisible by TP size, and all ranks can see the same model/data paths.

## Quantized inference choices

| Path | Dependencies | Example-derived notes | Safe recommendation |
|---|---|---|---|
| HF FP16 | `transformers`, `torch`, `accelerate` | 13B FP16 examples report around 26GB total VRAM across multiple 3090s depending distribution | Use when CUDA memory is sufficient and no quantized deps are desired. |
| HF INT8 | `bitsandbytes`, CUDA-compatible `torch`, `accelerate` | Example reports around 13GB for 13B INT8 on one 3090, slower than FP16 | Use when single-GPU VRAM is limited and bitsandbytes is available. |
| HF INT4 | Newer Transformers/bitsandbytes stack | Example notes INT4 support was branch/version dependent | Treat as version-sensitive; verify before promising. |
| llama.cpp Q8/Q5/Q4 | llama.cpp conversion and `llama-cpp-python` optional | Q8/Q5/Q4 trade accuracy/size/speed; CPU or partial GPU deployment possible | Use for edge/CPU-style deployment after separate conversion; not a Fengshen checkpoint format. |

## Fine-tune command planning fields

Do not copy source shell scripts. Construct a fresh command from these fields:

| Field | Meaning |
|---|---|
| `train_file`, `val_file`, `test_file` | JSON data files in prompt/output format. |
| `model_path` | Fengshen model directory or TP root. |
| `tokenizer_path` | Tokenizer directory; may be the single Fengshen/HF tokenizer path even with TP model shards. |
| `model_parallel_size` | TP size; must match converted shards. |
| `max_seq_length` | Controls prompt/output truncation. |
| `save_ckpt_path`, `load_ckpt_path` | Mutating checkpoint paths; require fresh directory/explicit resume. |
| `precision` | Example uses FP16 for full fine-tune. |
| `strategy`, Deepspeed config | Training resource/memory strategy; route details to `../data-training/SKILL.md`. |
| `wandb_project`, `wandb_name`, API keys | Optional logging; never hard-code secrets. |

## Common failure modes

| Symptom | Likely cause | Safe response |
|---|---|---|
| Planner recommends delta merge but user lacks base model | Delta checkpoint is not enough to reconstruct full weights | Ask for a compatible base checkpoint and rights confirmation. |
| `part_0` missing during TP fine-tune | `model_parallel_size>1` but model was not converted to TP shards | Run dry-run planner; convert from Fengshen single-shard to matching TP output before training. |
| Shape mismatch while loading shards | TP size differs from checkpoint shards or config dimensions are not divisible | Use the same TP size used during conversion; inspect config before execution. |
| Tokenizer mismatch | Tokenizer path points to different HF/Fengshen model | Use tokenizer produced with the model conversion or original compatible tokenizer. |
| Checkpoint resume silently ignored | Resume path missing or mismatched | Check existence and format before launch; do not rely on script warnings. |
| CUDA OOM | Model size/sequence length/batch/TP too large | Lower sequence/batch, use TP/ZeRO/offload, or switch to quantized inference. |
| `bitsandbytes` import failure | CPU-only or incompatible CUDA/Python stack | Use FP16/HF or llama.cpp path, or prepare compatible CUDA env. |
| llama.cpp file does not load | Wrong conversion format, old GGML/GGUF mismatch, or quantization mismatch | Recreate llama.cpp artifact with matching tool version; do not feed Fengshen shards directly. |

## Handoff template

For any Ziya task, report:

- source format and target workflow;
- required conversions in order;
- dependencies and backend assumptions;
- TP size decision and rationale;
- all output paths that would be created or overwritten;
- data schema requirements;
- unresolved approvals: downloads, base-model access, overwrite/mutation, and CUDA resource validation.

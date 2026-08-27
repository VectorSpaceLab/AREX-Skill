# Reward Model Troubleshooting

Use this reference when IXC-2.5-Reward scoring, ranking, preference training, or reward benchmark planning is blocked. It records source-era pitfalls and safe fixes without running model code.

## Scoring and ranking issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `rank` seems reversed | The API returns rank labels where lower is better; `0` is best. It is not necessarily a sorted list of candidate ids. | Interpret each returned value as the input candidate's rank. For auditability, also call `get_scores` and compare raw scores. |
| Pairwise result changes after batching | Chat list and image-list nesting are not aligned elementwise. | Ensure `len(chats) == len(images)` and each `images[i]` is a list for the corresponding chat. Use `[image, image]` for two candidates sharing one visual prompt. |
| Text-only benchmark call fails | Passing `None`, omitting images, or using one flat list instead of per-sample empty image lists. | Follow source evaluation shape: `model.get_scores([chat_1, chat_2], [[]] * 2)`. |
| Scores look incomparable across tasks | Reward scores are relative model outputs, not calibrated probabilities. | Compare candidates for the same prompt/image. Record model revision, dtype, `hd_num`, `max_length`, and data preprocessing with every score. |
| CUDA OOM during scoring | Large images, high `hd_num`, long context, or too many candidates in one batch. | Lower `hd_num`, lower `max_length`, reduce batch size, use fp16 autocast, and ensure no unrelated GPU processes are occupying memory. |

## Preference-data issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Many examples disappear during training | `filter_data` drops examples whose final chosen or rejected response is empty, only whitespace, contains `<|im_start|>`/`<|im_end|>`, or is a long response with very long unbroken tokens. | Run `python scripts/validate_reward_data.py data.txt --given-num` and clean failed rows before torchrun. |
| Training loader cannot open images | Relative image paths are resolved from the training process current working directory, not from the JSON file location. | Use absolute paths, or run from a cwd where the JSON `image` paths resolve. Use `--check-images --image-base cwd` to mirror source behavior. |
| Multi-image examples score or train unpredictably | The `image` field is a list, but the prompt lacks ordered `<ImageHere>` placeholders. | Add ordered prompt text such as `Image1 <ImageHere>; Image2 <ImageHere>; ...` in the user message. |
| Pair is not a real preference comparison | `conversations_a` and `conversations_b` have different user prompts or swapped labels. | Keep user/system turns identical and remember: `conversations_a` is chosen, `conversations_b` is rejected. |
| Validator complains about `role`/`content` | Inference API chat schema was copied into training data. | Convert to training schema: `from`/`value`. Reserve `role`/`content` for `get_score`/`get_scores`/`compare`/`rank`. |

## Training launcher issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Model id `internlm/iinternlm-xcomposer2d5-7b-reward` fails | The training README contains an `iinternlm` typo in the parameter explanation. | Use `internlm/internlm-xcomposer2d5-7b-reward` or a valid local model path. The renderer warns when it sees the typo. |
| `ds_config_zero2.json` not found | Command is run from a working directory where the relative DeepSpeed config path is invalid. | Use `entrypoints/ixc25-reward-training/launch_full.sh` / `launch_lora.sh`, which pass the bundled config, or pass an explicit `--deepspeed` path when rendering manually. |
| LoRA adapter cannot find the base model later | Adapter metadata can record a local base path. | Prefer an absolute local `--model-path` when training LoRA from a local checkpoint, then merge/load with that same base path. |
| Full training freezes more than expected | Source shell scripts pass `--fix_vit True --fix_sampler True`, while README text describes different conceptual defaults. | Inspect the rendered command and override `--fix-vit false` or `--fix-sampler false` only when the GPU budget and training objective require it. |
| OOM during training | Long context, image tiling, batch size, or unfrozen vision modules exceed VRAM. | Lower `max_length`, lower `hd_num`, reduce per-device batch size, increase gradient accumulation, keep `fix_vit`/`fix_sampler` true, or move to larger GPUs. |
| `torchrun` rendezvous fails | `MASTER_ADDR`, `MASTER_PORT`, `NNODES`, `NODE_RANK`, or `GPUS_PER_NODE` mismatch across nodes. | Render explicit distributed values instead of relying on stale `MLP_*` environment variables; confirm port availability before execution. |

## Evaluation layout issues

| Benchmark | Common blocker | Fix |
| --- | --- | --- |
| RewardBench | Missing parquet reader (`pandas`/`pyarrow`) or absent `filtered-00000-of-00001.parquet`. | Install benchmark dependencies in the execution env and place the parquet beside `inference.py`. Do not claim a score from only `results.json` fixtures. |
| RM-Bench | `total_dataset.json` missing or response arrays are not length 3. | Acquire the official dataset file and verify each row has three chosen and three rejected responses before running. |
| VL-RewardBench | `combined_data_tagged.jsonl` exists but image files under `images/` do not match `image_path`. | Download/extract the image zip and preserve the expected subdirectories (`povid`, `wildvision-battle`, etc.). |
| Any reward benchmark | Model download/cache unavailable or CUDA absent. | Keep the workflow as a layout plan; run native evaluation only after model, data, and GPU approval. |

## Environment and dependency issues

- `trust_remote_code=True` is required for IXC-2.5-Reward-specific scoring methods.
- Use a CUDA PyTorch build for real inference/training. CPU-only Python can validate data and render commands, but it cannot verify model behavior.
- flash-attn2 may be required for high-resolution or long-context settings; missing `nvcc` only matters if building CUDA extensions from source.
- Benchmark scripts import packages not needed by the bundled helpers: `pandas`, `numpy`, `tqdm`, `torch`, and Transformers. Install them only in an approved execution environment.
- Keep outputs such as `results.json`, training checkpoints, and converted benchmark files outside the runtime skill directory.

## Safe diagnostic order

1. Validate JSON/manifest shape with `validate_reward_data.py`.
2. Render a command with `render_reward_training_command.py` or inspect the runnable wrappers in `entrypoints/ixc25-reward-training/`, then inspect paths/flags.
3. Confirm local model or approved download, CUDA, and dependency versions.
4. For benchmark plans, confirm data file names and image roots before executing inference.
5. Only then hand off to an execution-capable session if the user approved GPU/model/data work.

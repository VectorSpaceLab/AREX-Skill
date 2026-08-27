# Troubleshooting Evaluation And Related Projects

Use this reference to diagnose blocked benchmark plans without running the benchmark. Prefer clear blocker reporting over partial execution.

## Boundary Mistakes

| Symptom | Likely issue | Correct route |
| --- | --- | --- |
| User asks to "run" MME/MMBench/OmniLive/ShareGPT4V now | This sub-skill is non-executing | Produce the plan, list missing data/GPU/judge approvals, then hand off only after approval to an execution-capable workflow. |
| User asks for image/video chat, caption generation, or demo output | Actual model inference | Route to sibling `model-inference`, or to execution planning for ShareCaptioner after CUDA/model approval. |
| User asks to start OmniLive SRS/FastAPI/Gradio services | Service launch plus model inference | Route to sibling `omnilive`. |
| User asks to fine-tune adapters | Training | Route to sibling `finetuning`; ShareGPT4V/DualFocus project training is not owned here. |
| User asks to score/rank responses with IXC-Reward | Reward model | Route to sibling `reward-model`. |

## Missing Data Or License Blocks

Common signs:

- benchmark root exists but expected split files are missing;
- image/video/audio paths in annotation files do not resolve;
- official eval tool is not present;
- user has not accepted dataset/model licenses;
- web/academic-only data is requested for commercial use.

Response pattern:

1. Name the missing benchmark asset and expected layout.
2. State that this sub-skill cannot download data.
3. Ask the user to provide the data root, proof of license/access, or permission for a separate execution step to acquire it.
4. Keep the plan usable with placeholders if the user only wanted a checklist.

## CUDA, Dependency, And Memory Blocks

- **CUDA unavailable:** legacy XComposer scripts and project evals call `.cuda()`, use autocast, or shard by `CUDA_VISIBLE_DEVICES`. CPU-only execution is generally not a faithful substitute for the benchmark.
- **NCCL/distributed issues:** OmniLive audio ASR uses distributed launch and NCCL; it needs one process per GPU and correct `RANK`, `WORLD_SIZE`, and `LOCAL_RANK` environment handling.
- **Missing Decord/PyArrow:** OmniLive video benchmarks need Decord; Video-MME also needs pandas and pyarrow for parquet annotations.
- **Missing Swift/ffmpeg/audio deps:** OmniLive audio and ASR flows need Qwen2-Audio/Swift-style dependencies, ffmpeg audio decoding, editdistance, sacrebleu tokenizer, and language normalization packages.
- **FlashAttention install failures:** ShareGPT4V/DualFocus install notes include FlashAttention; install only in a compatible CUDA/build environment. Do not make it a blanket requirement for a non-executing plan.
- **OOM:** video benchmarks concatenate many sampled frames into large image grids; reduce `--max-frame`, use fewer concurrent chunks, or choose a model/config with lower memory. Do not claim official reproducibility if sampling changes materially.

## Hardcoded Source-Era Paths

Many old scripts/notebooks embedded absolute private paths or placeholders such as `PATH TO MODEL`, `MME_IMG_PATH`, `MME_PATH`, `your_data_path`, or an internal dataset root. In a self-contained plan:

- replace each with user-provided `model_path`, `data_root`, and `output_root` placeholders;
- never expose local machine paths in runtime guidance;
- document whether the path is a model checkpoint, official eval tool, image root, video root, audio root, or output directory;
- warn when a workflow still requires source-era scripts or a separate reimplementation.

## Chunk Merge Problems

Symptoms:

- missing `0_of_N.json` or `${N}_${idx}.jsonl` chunk files;
- duplicate or missing question ids in merged JSONL;
- Slurm run writes all outputs to one file;
- GPU list `2,3` unexpectedly launches on GPUs `0,1`.

Checks:

1. Count chunks from `CUDA_VISIBLE_DEVICES` or Slurm `GPUS`.
2. Confirm each worker writes a unique file.
3. Validate merged line count against annotation count.
4. Inspect whether the script uses the mapped GPU id (`GPULIST[$IDX]`) or the loop index (`IDX`). Adapt plans carefully for nonzero GPU ids.
5. For Slurm scripts using `--chunk-idx -1`, confirm the Python module derives chunk id from rank before relying on merge paths.

## Submission And Judge Blocks

- **MMBench/OpenCompass:** local XLSX does not equal official score. Submission server/account is required.
- **VQAv2/VizWiz:** upload JSONs are for EvalAI-style servers; local creation does not score the benchmark.
- **QBench/SEED:** dev/local metrics and official leaderboard submissions can differ; state which split is being used.
- **MM-Vet/LLaVA-Wild/MathVista extraction:** final scores or answer extraction may require GPT/OpenAI calls. This sub-skill must not make those calls. Ask for explicit judge model, key, cost limit, and approval before any external execution workflow proceeds.

## Converter Format Errors

| Error | Diagnosis | Fix plan |
| --- | --- | --- |
| MMBench XLSX has blank predictions | `question_id` values do not match TSV `index` | Compare id types and split names; verify merged JSONL came from the same TSV. |
| MMBench converter fails on missing columns | Official TSV schema changed | Update drop-column list or preserve unknown columns while inserting `prediction`. |
| SEED accuracy is zero | Predictions are full text instead of option letters | Normalize to A/B/C/D style before conversion; decide exact versus first-character tolerance. |
| GQA eval rejects JSON | Needs array with `questionId`/`prediction` | Convert JSONL rows and lowercase/strip trailing periods if using the evidence convention. |
| VizWiz/VQAv2 server rejects upload | Wrong answer normalization or missing ids | Use EvalAI-style answer processing and verify annotation coverage. |
| QBench Chinese files not found | Non-ASCII filename mismatch or wrong split | Preserve exact filenames and avoid lossy shell/glob transformations. |

## ShareGPT4V Project Issues

- `playground` archive missing: most evaluation scripts depend on it for annotations and expected directory structure.
- Wrong checkpoint path: scripts usually expect `checkpoints/<ckpt>` unless a checkpoint directory argument is supplied.
- GPT review accidentally launched: LLaVA-Bench review scripts call GPT/OpenAI; keep disabled until judge approval.
- ShareCaptioner output unexpectedly slow: it is large model inference; require CUDA/model approval and route out of this non-executing sub-skill.
- Gradio app opens a public share URL by default in evidence arguments. Treat any service launch or public tunnel as a security-sensitive separate approval.

## DualFocus Project Issues

- `--model-base` missing: evaluation scripts pass a Vicuna base model; include this in plans.
- Training request: evidence did not release training code; do not promise training support.
- GQA MCQ confusion: DualFocus evidence uses a multiple-choice converted GQA JSONL, not necessarily the official short-answer GQA format.
- Slurm defaults invalid: partition/quota defaults were cluster-specific examples. Ask for real cluster settings.
- TextVQA evaluator module mismatch: local and Slurm evidence differ between `llava.eval.eval_textvqa` and `dualfocus.eval.eval_textvqa`; verify installed package namespace before execution.

## OmniLive Benchmark Issues

- Missing model subdirectory: video benchmarks default to an OmniLive base checkpoint path; model layout checks belong to sibling `omnilive`.
- StreamingBench working directory: source-era aggregation changed directories before counting outputs. A plan should pin the launch/aggregation working directory.
- Video-MME parquet dependency: annotation parquet needs pyarrow.
- MVBench data sprawl: one root expands to many component datasets. Missing one sub-dataset can invalidate only that task, but official averages require the full set.
- MLVU task folders: folder names must match task ids such as `1_plotQA` and `7_topic_reasoning`.

## Safe Response Template

When a benchmark plan is blocked, respond with:

```text
Workflow: <benchmark/project>
Status: blocked before execution
Blocking evidence: <missing data/GPU/judge/server/license/path>
Safe next step: <provide data root / approve external judge / choose VLMEvalKit / route to sibling skill>
Non-executing plan retained: <command pattern and expected result files>
```

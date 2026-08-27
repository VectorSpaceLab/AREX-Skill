# MiniLLM workflows

MiniLLM is the on-policy distillation family in this sub-skill. Use it for SFT
initialization, KD baselines, SeqKD baselines, MiniLLM training, evaluation,
exposure-bias analysis, data processing, and checkpoint tensor-parallel
conversion.

For shared install, hardware, and credential issues, see the parent skill's
troubleshooting reference when available at `../../references/troubleshooting.md`.

## Scope markers

Use this reference when the request mentions any of the following:

- MiniLLM training, evaluation, or exposure-bias analysis
- SFT, KD, or SeqKD baselines used for MiniLLM-style distillation
- Dolly, Self-Inst, Vicuna, SInST, UInST, OpenWebText, or RoBERTa-corpus data
- `model-parallel` / `model-parallel-size` checkpoint reshaping
- multi-node DeepSpeed launch planning

Route the request away if it is really DPKD-only or Tuna-only.

## Environment expectations

MiniLLM relies on a modified Transformers fork, DeepSpeed, accelerate,
datasets, peft, rouge-score, rich, numerize, and torchtyping. The repository
marks its custom Transformers edits with a MiniLLM-specific begin/end marker;
if those edits are missing, the environment is probably not the expected one.

Important constraints:

- LLaMA-family checkpoints require license access.
- The workflows assume a local or cached checkpoint tree when model-parallel
  conversion is needed.
- Evaluation is not a trivial smoke test; it still needs aligned model, data,
  and launcher settings.

## Data flow

MiniLLM uses two data streams:

1. **Instruction-response data** for SFT and KD style stages.
   - Typical source families: Dolly, Self-Inst, Vicuna, SInST, and UInST.
   - Processing converts instruction-response examples into train/validation
     shards.
2. **Plain-text corpus** for optional on-policy language-model guidance.
   - OpenWebText is the canonical example.
   - The preprocessing step writes one document per line and replaces embedded
     newlines with a placeholder token so the corpus can be parallelized.

The data-processing helpers are family-aware. The requested family must match
what the surrounding scripts expect when they look for `processed_data/<model
family>/...` or `data/<family>/...`.

## Model resources

The documented recipe covers GPT-2, OPT, LLaMA, LLaMA2, Mistral, and Qwen2
style checkpoints. The checkpoints may be local downloads or cached model hub
artifacts, but the generated skill should treat them as explicit inputs rather
than assuming a free download.

MiniLLM training and evaluation save paths usually encode:

- checkpoint name
- batch size
- learning rate
- GPU count
- node count
- tensor-parallel size
- optional LoRA settings
- the stage name such as SFT, KD, SeqKD, or MiniLLM

## Model-parallel conversion

Use the bundled planner before any real conversion. The source conversion code
supports three cases:

- **1 → N**: split a monolithic checkpoint into tensor-parallel shards.
- **N → 1**: merge sharded weights back into a monolithic checkpoint.
- **N → M**: merge, then re-split to a new shard count.

Family-specific model types differ by project:

- MiniLLM conversion: `opt`, `qwen2`, `llama`, `mistral`
- DPKD conversion: `opt`, `gptj`, `llama`, `llama2`, `mistral`, `qwen`

If the selected model type is not compatible with the family, stop before any
write or model load.

## Evaluation stages

MiniLLM exposes two main evaluation entry points:

- `evaluate.py` with the `eval_main` path for generation quality and ROUGE-L.
- `evaluate.py` with the `eval_exposure_bias` path for exposure-bias analysis
  against a teacher model.

The main evaluator writes prediction artifacts and summary logs. The exposure-
bias evaluator writes comparison tensors and summary logs. Neither is a cheap
smoke test: both need the same checkpoint family, tokenizer family, and data
layout as training.

## Training stages

Use the stage order below as the default mental model:

1. **SFT baseline** to initialize the student.
2. **KD baseline** to distill from a teacher model.
3. **SeqKD** to generate teacher responses and fine-tune on the pseudo data.
4. **MiniLLM** to run the on-policy distillation stage with optional LM corpus
   guidance.

Key reminders:

- `PROMPT_DATA_DIR` is required for the instruction-response stream.
- `LM_DATA_DIR` is optional and can be omitted for the no-plain-text variant.
- MiniLLM final checkpoints are selected by validation loss or ROUGE-L,
  depending on the stage.
- Teacher paths may also need teacher PEFT paths when LoRA is involved.

## Multi-node DeepSpeed notes

Multi-node MiniLLM training uses DeepSpeed launcher semantics and a hostfile.
A safe planning checklist is:

- confirm the node count and GPU count
- confirm the hostfile path
- confirm the checkpoint family and tensor-parallel size
- confirm the DeepSpeed config variant
- confirm whether the run is single-node, multi-node, or model-parallel

If these disagree, the failure is a configuration mismatch rather than a model
quality issue.

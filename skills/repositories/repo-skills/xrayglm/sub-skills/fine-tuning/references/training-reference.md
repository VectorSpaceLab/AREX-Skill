# XrayGLM training mechanics and launcher reference

Evidence: `finetune_XrayGLM.py`, `finetune_XrayGLM.sh`, `model/visualglm.py`,
`model/blip2.py`, `model/chat.py`, `README.md`, `checkpoints/README.md`, and
`assets/train_cli.txt`.

## Record to model packing

For each accepted record, `FewShotDataset` uses `BlipImageEvalProcessor(224)`:
RGB conversion, resize to 224 x 224, tensor conversion, and BLIP2 mean/std
normalization. It tokenizes and concatenates:

```text
encode("<img>") + [pad_token_id] * image_length
+ encode("</img>问：" + prompt + "\n答：")
```

The default `image_length` is 32. These are not ordinary padding positions:
`ImageMixin.word_embedding_forward` splits the sequence at `pre_image` and
`pre_image + image_length`, runs the image through EVA ViT -> Q-Former ->
`glm_proj`, and substitutes 32 image embeddings for those placeholder ids.
`pre_image` is the token count before the image pads (normally the encoded
`<img>` prefix). Keep the entire 32-slot block in the source budget. Changing
`image_length`, tokenizer/model configuration, or the placeholder convention
requires a coordinated model/data change and a CUDA smoke test.

The source and target are bounded independently before special tokens are
built:

- `a_ids` (image markers plus prompt text) is truncated to
  `max_source_length - 1`.
- `b_ids` (label) is truncated to `max_target_length - 2`.
- `build_inputs_with_special_tokens(a_ids, b_ids)` supplies the GLM special
  tokens. The packed sequence is padded to
  `max_source_length + max_target_length`.

The shell's documented starting values are source 64 and target 256. The
Python model-specific defaults are not the shell defaults: `image_length=32`
and `pre_seq_len=8`, while the shell asks for `pre_seq_len=4` and
`lora_rank=10`. Record effective values, not just defaults. A source limit that
cuts through the image placeholder block is a hard data/model incompatibility,
not an ordinary truncation warning.

## Labels and loss

`context_length` is the position of the GLM BOS marker. The dataset builds
`labels` as `-100` for every context position, then copies the sequence from
the target-generation boundary onward. The loss shifts logits and labels by
one position and uses `CrossEntropyLoss(ignore_index=-100)`. Consequently:

- `<img>`, the 32 image placeholder positions, `</img>问：`, the prompt, and
  `答：` do not contribute supervised loss;
- target special/response tokens after the context boundary do contribute;
- batch padding is initially `pad_token_id`, then becomes `-100` when
  `ignore_pad_token_for_loss=True` (the source default);
- labels are not a second natural-language copy of the prompt.

This is a parser/packing interpretation from source code. Validate token
counts with the intended tokenizer; a CPU token check does not prove the
6B model forward or image encoder works.

## Model and adapter execution

`FineTuneVisualGLMModel` loads the `visualglm-6b` base through SAT and adds the
VisualGLM image mixin. It adds P-Tuning when `--use_ptuning`; it then adds LoRA
when `--use_lora`, otherwise QLoRA when `--use_qlora`. The branch is `if
use_lora: ... elif use_qlora: ...`, so `use_lora` takes precedence if both
flags are present. See [lora-qlora-reference.md](lora-qlora-reference.md) for
trainable-parameter and checkpoint cautions.

After construction, `disable_untrainable_params()` freezes every parameter
unless its name contains `ptuning`, `matrix_A`, or `matrix_B` as applicable.
The base visual encoder, Q-Former, projection, and ordinary transformer
weights are therefore not expected to update for the adapter configurations.
Print and record the names that remain trainable. A full-parameter update is
not the default and must not happen accidentally.

## Corrected launcher template (documentation only)

The checked-in `finetune_XrayGLM.sh` is an experiment launcher, not a command
to run blindly. It currently specifies four GPUs, `deepspeed`, NCCL, hostfile
`hostfile_single`, ZeRO stage 1, FP16, checkpoint activation, batch/eval batch
8, 300 training iterations, cosine decay, `lr=1e-4`, `warmup=.02`, save every
3000, and eval every 10000. It points train and validation at the same
`./data/Xray/openi-zh.json`, which fails the data contract described above.

It also contains `--lora_rank 10\` without a separating space before the
continuation. The following is a **template to review and adapt**, not an
invocation and not a guarantee that the hostfile or paths exist:

```bash
# Explicit opt-in only; review all values first.
export CUDA_VISIBLE_DEVICES=0,1,2,3
export NCCL_DEBUG=info
export NCCL_IB_DISABLE=0
export NCCL_NET_GDR_LEVEL=2

MODEL_ARGS="--max_source_length 64 \
  --max_target_length 256 \
  --lora_rank 10 \
  --pre_seq_len 4"

TRAIN_DATA="/absolute/path/to/flat-train.json"
VALID_DATA="/absolute/path/to/flat-valid.json"
HOSTFILE="/absolute/path/to/hostfile_single"

# Keep this command displayed and reviewed before explicit execution.
launch_cmd="deepspeed --master_port 16666 --hostfile ${HOSTFILE} \
  finetune_XrayGLM.py \
  --experiment-name finetune-XrayGLM \
  --model-parallel-size 1 --mode finetune --train-iters 300 \
  ${MODEL_ARGS} --train-data ${TRAIN_DATA} --valid-data ${VALID_DATA} \
  --distributed-backend nccl --lr-decay-style cosine --warmup .02 \
  --checkpoint-activations --save-interval 3000 --eval-interval 10000 \
  --save ./checkpoints --split 1 --eval-iters 10 \
  --eval-batch-size 8 --zero-stage 1 --lr 0.0001 --batch-size 8 \
  --skip-init --fp16 --use_lora"
printf '%s\n' "${launch_cmd}"
# Do not eval this template without explicit approval and all gates.
```

The variable `launch_cmd` above is only a displayed command string. A real launch also
needs the correct working directory, a valid hostfile, installed SAT/DeepSpeed,
visible GPUs, and a checkpoint/model cache. `requirements.txt` includes
`bitsandbytes==0.39.0` and the SAT dependency; `requirements_wo_ds.txt`
omits DeepSpeed and is not sufficient for this launcher.

## Distributed/runtime criticality

The supplied inspection facts are Python 3.10, torch 2.1.2+cu121, SAT 0.3.7,
and DeepSpeed 0.10.3 imports, with CUDA smoke passing on 8 A100-SXM4-40GB
GPUs. The host has no `nvcc`; do not infer that custom CUDA extensions can be
compiled. Verify the exact Python environment used by the launcher rather than
trusting the default shell. NCCL, GPU visibility, peer communication,
DeepSpeed hostfile parsing, mixed precision, checkpoint activation, and
memory behavior are required-backend execution concerns. A JSON/Pillow check
or Python import is not evidence that a distributed training step is safe.

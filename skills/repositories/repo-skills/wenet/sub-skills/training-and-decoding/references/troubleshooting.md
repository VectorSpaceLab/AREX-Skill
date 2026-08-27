# Training and Decoding Troubleshooting

## Distributed training hangs or crashes

Symptoms:

- `torchrun` workers hang at startup;
- NCCL errors or timeouts;
- ranks disagree about world size;
- network address binding errors.

Recovery:

1. Confirm `--nnodes`, `--nproc_per_node`, rendezvous id, and endpoint.
2. For CUDA, start with `--ddp.dist_backend nccl`; if debugging CPU or network
   issues, try `gloo` on a tiny job.
3. For Ascend NPU, use the NPU stack and `hccl` only when the vendor runtime is
   installed.
4. Set `CUDA_VISIBLE_DEVICES` intentionally; recipes may auto-detect GPUs but
   cluster schedulers often require explicit allocation.
5. For multi-node jobs, set network interface variables required by the cluster
   rather than relying on defaults.

## DeepSpeed config mismatch

Symptoms:

- assertion failures at training startup;
- batch size or accumulation errors;
- optimizer state conversion failures.

WeNet checks that DeepSpeed JSON values align with YAML config values such as
micro-batch size, gradient accumulation, gradient clipping, and log interval.
Update both files together, or disable DeepSpeed for a smaller `torch_ddp`
reproduction.

## Missing train/cv data or tokenizer resources

Symptoms:

- `--train_data` or `--cv_data` file not found;
- tokenizer initialization fails;
- model output dimension mismatch.

Recovery:

- Validate data with [../../data-preparation/SKILL.md](../../data-preparation/SKILL.md).
- Confirm dictionary/tokenizer resources match the config.
- Ensure `train.yaml` produced after config modification is the one used for
  recognition and export.

## Checkpoint or `train.yaml` missing

Recognition and export need both a config and checkpoint. After training, look
for generated `train.yaml` in the model directory and for checkpoints such as
`N.pt`, `avg_N.pt`, or `final.pt`. If `final.pt` is a symlink in the user's
filesystem, verify it resolves before moving artifacts.

## Recognition output is empty or incomplete

Likely causes:

- test `data.list` has invalid JSON or filtered utterances;
- wrong tokenizer resources;
- checkpoint/config mismatch;
- decoding mode unsupported by the model family;
- beam-search mode run with an incompatible batch size.

Recovery:

1. Run a tiny `data.list` through data-preparation validation.
2. Use one simple mode first, such as `ctc_greedy_search` or a model-family
   greedy mode.
3. Lower `batch_size` to `1` for prefix-beam or attention-rescoring debugging.
4. Confirm `--checkpoint` and `--config` belong to the same experiment.

## WER/CER scores look wrong

- Reference and hypothesis keys must match.
- Choose `--unit char` for character error rate and `--unit word` for word error
  rate.
- Apply the same text normalization used by the recipe before scoring.
- Use `--details` in the bundled scorer to inspect substitutions/insertions/
  deletions for small examples.

## LM, FST, or k2 stages fail

These optional paths need extra graph-building dependencies and language
resources. Stop and verify the toolchain, lexicon, units, word table, and LM
files before debugging `recognize.py`. If the task does not require LM/k2, fall
back to regular CTC/attention decoding first.

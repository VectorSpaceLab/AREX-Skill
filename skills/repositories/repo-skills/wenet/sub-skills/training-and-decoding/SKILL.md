---
name: training-and-decoding
description: "Run and adapt WeNet training recipes, checkpoint averaging,
  offline decoding, recognition modes, scoring, LM or k2 decoding, and training
  failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WeNet Training and Decoding

Use this sub-skill when the user wants to train or fine-tune a WeNet model,
resume an experiment, run offline recognition on a `data.list`, average
checkpoints, compare decoding modes, compute WER/CER, or reason about recipe
stages.

## Start here

1. Ensure data manifests, dictionaries, and tokenizer resources are valid with
   [../data-preparation/SKILL.md](../data-preparation/SKILL.md).
2. Read [references/workflows.md](references/workflows.md) for the staged
   training/decoding recipe pattern and large-job boundaries.
3. Read [references/cli-reference.md](references/cli-reference.md) for the
   installed-module command shapes and important options.
4. Use [scripts/score_text.py](scripts/score_text.py) for small local WER/CER
   checks when the full recipe scorer is unavailable:

   ```bash
   python sub-skills/training-and-decoding/scripts/score_text.py \
     --reference ref.txt --hypothesis hyp.txt --unit word
   ```

5. Read [references/troubleshooting.md](references/troubleshooting.md) when
   distributed training hangs, NCCL/HCCL/gloo fails, DeepSpeed configs disagree
   with WeNet configs, checkpoints are missing, or decoding output is empty.

## Route by task

- Use this sub-skill for `python -m wenet.bin.train`, `recognize`,
  `average_model`, and `alignment` workflows.
- Use [../model-export/SKILL.md](../model-export/SKILL.md) after a trained
  checkpoint and `train.yaml` exist.
- Use [../runtime-deployment/SKILL.md](../runtime-deployment/SKILL.md) after
  export when the user needs C++/mobile/web/server deployment.
- Use [../package-transcription/SKILL.md](../package-transcription/SKILL.md)
  for one-off package CLI transcription of a single audio file.

## Verification boundary

Real training, large decoding, LM graph creation, and k2/LF-MMI workflows can
require large corpora, GPUs, distributed launchers, external toolchains, and
long runtimes. Treat them as documented operational workflows unless the user
explicitly authorizes the data, hardware, and time budget.

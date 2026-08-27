---
name: quark0-darts
description: "Use the original DARTS research code for differentiable
  architecture search, CNN/RNN genotypes, CIFAR/ImageNet/PTB/WT2 workflows, and
  legacy PyTorch troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DARTS

Use this repo skill when a task is about the original **DARTS: Differentiable Architecture Search** codebase: convolutional architecture search/evaluation, recurrent language-modeling search/evaluation, genotype schemas, visualization, dataset/checkpoint layout, or legacy PyTorch/CUDA failures.

This is a source-backed operating skill for a script-style research repository. It does not assume the original checkout is available, does not install a package, and does not claim that paper-scale native runs were executed during skill production.

## Start here

1. Read [legacy runtime](references/legacy-runtime.md) before promising native execution. The original code targets Python 3.5-era PyTorch 0.3.1/torchvision 0.2.0 and CUDA.
2. Read [data and checkpoints](references/data-and-checkpoints.md) when a workflow needs CIFAR-10, ImageNet, PTB, WikiText-2, or pretrained model files.
3. Read [troubleshooting](references/troubleshooting.md) for cross-cutting failures such as `async=True` syntax errors, missing CUDA, dataset assertions, checkpoint-format mismatches, and Graphviz issues.
4. Check [repo provenance](references/repo-provenance.md) before treating this skill as current for a different DARTS checkout.

## Route by task

| User task | Read |
| --- | --- |
| CIFAR-10 DARTS architecture search, CIFAR-10 training/test, ImageNet training/test, CNN model/cell/operation facts, or CNN CUDA/OOM/nondeterminism failures | [cnn-architectures](sub-skills/cnn-architectures/SKILL.md) |
| Penn Treebank or WikiText-2 recurrent DARTS search/training/test, corpus layout, checkpoint behavior, ASGD schedule, perplexity interpretation, or RNN CUDA/hidden-size/data failures | [rnn-language-modeling](sub-skills/rnn-language-modeling/SKILL.md) |
| CNN/RNN genotype schemas, built-in DARTS/NASNet/AmoebaNet/ENAS genotypes, converting search outputs, validating custom genotypes, or DOT visualization | [genotypes-and-visualization](sub-skills/genotypes-and-visualization/SKILL.md) |
| Construct a native command without launching a job | [darts_command_builder.py](scripts/darts_command_builder.py) |
| Inspect a local DARTS-style source tree before running or porting it | [darts_static_inspector.py](scripts/darts_static_inspector.py) |

## Safe helper scripts

- Run `python scripts/darts_command_builder.py list` to see workflow ids.
- Run `python scripts/darts_command_builder.py build cnn-search --smoke --gpu 0` to print a wiring-check command and prerequisites. The helper does **not** run training or download data.
- Run `python scripts/darts_static_inspector.py --repo-root <path>` to statically check an external DARTS source tree. The helper does **not** import the repo.
- Run `python sub-skills/genotypes-and-visualization/scripts/darts_genotype_tools.py list` to inspect bundled genotype catalogs and emit DOT without Graphviz.

## Operating rules

- Distinguish **architecture search** from **final evaluation**. Search validation accuracy/perplexity is not the paper result.
- Treat full native workflows as legacy CUDA jobs. If the user is on modern Python/PyTorch, route to porting guidance instead of implying direct compatibility.
- Never report smoke-mode output as paper accuracy or perplexity.
- Keep CNN and RNN genotype schemas separate; both define `DARTS`, but the tuple fields and valid edges differ.
- Do not tell future agents to open original repo scripts or README pages for routine operation. Use the bundled references and scripts in this skill.
- If a requested dataset, pretrained checkpoint, CUDA runtime, or legacy PyTorch build is missing, report the missing prerequisite clearly and stop before inventing a result.

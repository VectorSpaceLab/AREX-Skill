# DARTS Troubleshooting

## Purpose

Use this reference for cross-cutting failures that can appear in CNN, RNN, genotype, data, or visualization workflows. For workflow-specific detail, read the nearest sub-skill troubleshooting file.

## Quick triage table

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `SyntaxError` pointing at `async=True` | Modern Python reserves `async`; CNN runners target Python 3.5-era syntax. | Use a compatible legacy runtime or port the code. See [legacy runtime](legacy-runtime.md). |
| `no gpu device available` from CNN scripts | CNN native runners require `torch.cuda.is_available()`. | Use a CUDA-capable legacy environment, or treat CPU execution as a porting task. |
| RNN script behaves opposite of expected after passing `--cuda` | RNN argparse uses `--cuda` with `action='store_false'`, so passing the flag disables CUDA. | Omit `--cuda` for default CUDA mode in native scripts; read RNN troubleshooting before attempting CPU mode. |
| `AssertionError` while loading PTB/WT2 | Missing `train.txt`, `valid.txt`, or `test.txt`. | Validate the plain-text corpus layout in [data and checkpoints](data-and-checkpoints.md). |
| ImageNet loader finds zero classes or raises folder errors | `--data` does not contain ImageFolder-style `train/` and `val/` class directories. | Point `--data` to the ImageNet root containing `train/<class>/...` and `val/<class>/...`. |
| Pretrained evaluation fails with missing or unexpected keys | Wrong checkpoint format, wrong `--arch`, wrong `--auxiliary`, or mismatched channels/layers. | Match the file kind and model scale in [data and checkpoints](data-and-checkpoints.md) and the relevant sub-skill workflow. |
| Smoke run succeeds but metric is poor | Smoke commands use tiny epochs/batches and are only wiring checks. | Do not report smoke output as paper accuracy/perplexity. Run full native schedule for comparable metrics. |
| Full CIFAR result differs across runs | README notes cuDNN back-prop nondeterminism and advises multiple independent runs. | Report mean/variance over repeated runs; do not overinterpret one run. |
| `graphviz` import or render failure | Original visualizers require Python Graphviz and system Graphviz. | Use the bundled DOT-only helper under `sub-skills/genotypes-and-visualization/scripts/`; render separately if Graphviz is installed. |

## Before asking for a native run

1. Decide whether the user wants faithful original execution or a modern port.
2. Use [scripts/darts_static_inspector.py](../scripts/darts_static_inspector.py) on any supplied source tree to catch file/layout/syntax problems without importing code.
3. Use [scripts/darts_command_builder.py](../scripts/darts_command_builder.py) to print the command, prerequisites, expected signal, and smoke-mode caveats.
4. Verify data and checkpoint files separately. The helper does not download or validate large datasets.
5. If the user lacks legacy CUDA/PyTorch, stop and present the runtime gap rather than pretending a CPU or modern PyTorch run is equivalent.

## When to route to sub-skills

- CNN CIFAR/ImageNet command, model, checkpoint, auxiliary, cutout, drop-path, and OOM questions: `sub-skills/cnn-architectures/`.
- RNN PTB/WT2 corpus, CUDA flag inversion, hidden-size, ASGD, NaN rollback, and perplexity questions: `sub-skills/rnn-language-modeling/`.
- Genotype schema, custom architecture validation, search-output conversion, and DOT visualization questions: `sub-skills/genotypes-and-visualization/`.

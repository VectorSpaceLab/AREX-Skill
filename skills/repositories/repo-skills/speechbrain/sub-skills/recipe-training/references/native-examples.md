# Native example and verification map

SpeechBrain has multiple tiny examples and recipe catalog entries that are useful as ground-truth evidence. Do not depend on the original source checkout at runtime; use this reference to understand patterns and choose verification cases.

## Tiny integration example patterns

| Example family | Pattern it demonstrates | Verification idea |
| --- | --- | --- |
| ASR CTC | `Brain` subclass, audio/text dynamic items, CTC loss, greedy decode, tiny ASR fixture. | Assert a CPU tiny ASR run overfits/finishes and writes expected logs when budget allows. |
| ASR seq2seq/transducer | Encoder-decoder or transducer training structure. | Use for structural evidence; run only if selected dependencies and budget allow. |
| G2P | Character/phoneme encoders, seq2seq loss, greedy search. | Use for custom text/phoneme pipeline tasks. |
| VAD | Binary frame targets from boundary annotations, binary metrics. | Use when validating VAD recipe adaptation. |
| Speaker ID | X-vector/TDNN classifier with label encoder. | Use when adapting classification/speaker recipes. |
| Augmentation | HyperPyYAML augmentation objects and generated audio comparison. | Use for audio preprocessing validation. |
| Separation/enhancement | Tiny source separation or enhancement model loops. | Use as structural evidence; full metrics may be expensive. |
| Sampling | Dataloader/sampler behavior from YAML. | Use for data loader/sampling debugging. |

## Recipe CSV debug entries

`tests/recipes/*.csv` rows provide tested combinations of:

- Script file.
- Hparams file.
- Data prep file.
- README file.
- Debug flags.
- Expected output files.
- Optional performance checks.

A good verification row has `--skip_prep=True`, local sample annotations, a small `--number_of_epochs`, and file-existence checks. Rows with `test_download`, Hugging Face model downloads, large external datasets, or long performance checks should be marked skip-network/skip-expensive unless approved.

## Verification planning rules

- Use CPU tiny examples for syntax/data-flow validation.
- Use CUDA only when the task is explicitly about GPU behavior or full training performance.
- Keep dataset preparation separate from model training verification.
- Verify output folder contents when recipe CSV provides `file_exists=[...]` checks.
- Do not run all recipe rows as a default; select one row per changed workflow.

## Integrated difficult cases to design later

1. **Recipe-to-inference handoff**: adapt a tiny recipe to save a local pretrained-style folder, then ensure the inference sub-skill explains the local `from_hparams` load and trust boundary.
2. **Data-pipeline plus recipe debug**: build a custom annotation manifest, add a dynamic item, run a CPU debug command, and diagnose missing output keys or placeholder overrides.

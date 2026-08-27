---
name: model-architecture
description: "Use and debug the TimeMixer Model API, PDM/FMM architecture,
  decomposition, downsampling, channel independence, normalization, and
  task-specific forward shapes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TimeMixer Model Architecture

Use this sub-skill when the task is about instantiating or debugging the TimeMixer model class, checking forward-output shapes, choosing decomposition/downsampling/channel settings, or explaining the Past-Decomposable-Mixing and Future-Multipredictor-Mixing internals.

## Route here for

- `Model.forward(x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None)` behavior.
- Forecast, imputation, anomaly-detection, and classification tensor shapes.
- `moving_avg` versus `dft_decomp`, `avg`/`max`/`conv` downsampling, `channel_independence`, `use_norm`, and future temporal features.
- Small CPU smoke tests that instantiate TimeMixer and print deterministic JSON shape evidence.
- Classification shape errors involving multi-feature tensors and the default channel-independent embedding.

## Do not use this sub-skill for

- Benchmark command recipes, training loops, dataset downloads, or shell-script reproduction; route those to forecasting experiment guidance.
- Raw dataset layout, CSV validation, PEMS/Solar/M4/UEA file placement, or time-feature preprocessing beyond tensor-shape context.
- Full imputation, anomaly-detection, or classification CLI workflows beyond model-forward shape diagnostics.

## Operating flow

1. Read `references/api-reference.md` for the model constructor inputs, forward signature, and task output contracts.
2. Read `references/architecture-notes.md` before changing decomposition, downsampling, normalization, future temporal features, or channel independence.
3. Use `references/troubleshooting.md` to map common RuntimeErrors to concrete config or tensor fixes.
4. Run the bundled smoke helper when you need a fast CPU-only shape check. Invoke the helper by its explicit skill path, while pointing `--repo-root` at the source checkout:

   ```bash
   cd /path/to/TimeMixer-checkout
   python /path/to/timemixer-skill/sub-skills/model-architecture/scripts/smoke_timemixer_forward.py --repo-root /path/to/TimeMixer-checkout --task long_term_forecast
   ```

The smoke helper is diagnostic only. It does not train, download data, run benchmark scripts, or read generated test artifacts.

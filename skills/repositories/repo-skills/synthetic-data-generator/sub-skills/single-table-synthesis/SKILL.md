---
name: single-table-synthesis
description: "Fit, save, load, and sample SDGX single-table synthesizers through
  the Python API or sdgx CLI, including CTGAN and GaussianCopula workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SDGX Single-Table Synthesis

Use this sub-skill for `Synthesizer`, CTGAN/GaussianCopula fitting and sampling, model save/load directories, CLI `sdgx fit`/`sdgx sample`, component listing, and small smoke tests.

If the user asks about data connectors, metadata, datetime formats, fixed combinations, PII columns, or custom processors, read [../data-preparation/SKILL.md](../data-preparation/SKILL.md) first. If the model is OpenAI/GPT-backed, read [../llm-synthesis/SKILL.md](../llm-synthesis/SKILL.md).

## Choose an entrypoint

- **Python API:** best for notebooks, programmatic validation, custom metadata, custom processors, and direct model instances.
- **CLI:** best for repeatable shell workflows, external orchestration, JSON output status, and saved synthesizer directories.
- **Bundled smoke helper:** run [scripts/tiny_synthesis_smoke.py](scripts/tiny_synthesis_smoke.py) when you need a tiny assertion-backed test without external data.

## Library workflow sketch

```python
from sdgx.data_connectors.csv_connector import CsvConnector
from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
from sdgx.synthesizer import Synthesizer

connector = CsvConnector(path="input.csv")
synthesizer = Synthesizer(
    model=CTGANSynthesizerModel(epochs=1, batch_size=10, device="cpu"),
    data_connector=connector,
)
synthesizer.fit()
sampled = synthesizer.sample(100)
```

Read [references/synthesizer-workflows.md](references/synthesizer-workflows.md) for full library patterns, save/load, GaussianCopula, chunksize sampling, and data-processor customization.

## CLI workflow sketch

```bash
sdgx fit \
  --save_dir model-dir \
  --model CTGAN \
  --model_kwargs '{"epochs":1,"batch_size":10,"device":"cpu"}' \
  --data_connector csvconnector \
  --data_connector_kwargs '{"path":"input.csv"}' \
  --json_output true

sdgx sample \
  --load_dir model-dir \
  --model CTGAN \
  --count 100 \
  --export_dst synthetic.csv \
  --json_output true
```

Read [references/cli-reference.md](references/cli-reference.md) for all important CLI flags and JSON option formats.

## Model decision points

- Use `CTGANSynthesizerModel` for neural/tabular GAN workflows; set `epochs=1` only for smoke tests.
- Use `GaussianCopulaSynthesizerModel` for fast statistic/correlation-style checks and CPU-friendly smoke tests.
- `ModelManager` registers `ctgan` in this source state; direct import is the reliable route for GaussianCopula.
- For CPU-only or deterministic tests, pass `device="cpu"`. CTGAN defaults to CUDA if PyTorch reports CUDA available.
- Always validate output row count, column order, column types, and domain constraints; sampling can produce extra rows internally before filtering.

Read [references/model-reference.md](references/model-reference.md) for inspected signatures and parameter notes.

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for CTGAN `batch_size`, device, fit/sample, save/load, CLI JSON, processor, and output validation failures.

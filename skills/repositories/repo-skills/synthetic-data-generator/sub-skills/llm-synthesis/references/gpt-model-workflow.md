# SingleTableGPTModel workflow

## Import and settings

```python
from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel

model = SingleTableGPTModel()
model.set_openAI_settings("https://api.openai.com/v1/", "sk-...")
model.gpt_model = "gpt-4o-mini"  # or another OpenAI-compatible chat model
```

Environment variables:

```bash
export OPENAI_KEY="..."
export OPENAI_URL="https://api.openai.com/v1/"
```

Do not print or store the real key in logs. Use the bundled settings inspector to confirm redacted configuration.

## Fitting with raw data

```python
import pandas as pd
from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel

df = pd.read_csv("input.csv").head(100)
model = SingleTableGPTModel()
model.dataset_description = "Customer subscription table with demographics and plan labels."
model.fit(df)
```

Raw-data fitting stores randomized sample-line prompts. This may send real row values to the external endpoint during generation, so confirm user authorization.

## Fitting with metadata only

```python
from sdgx.data_models.metadata import Metadata
from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel

metadata = Metadata.from_dataframe(df)
model = SingleTableGPTModel()
model.dataset_description = "A synthetic customer table; do not copy any real row."
model.fit(metadata)
```

Metadata-only generation avoids sending individual raw rows but still sends schema/type information and any description you add.

## Off-table features

```python
model.off_table_features = ["has_car", "risk_band"]
```

The model will ask the LLM to infer additional columns after the original table columns. Treat off-table features as heuristic and validate them manually.

## Offline response parsing

`SingleTableGPTModel.extract_samples_from_response(response_content)` parses text responses such as:

```text
sample 0: age is 36, workclass is Private, income is <=50K
sample 1: age is 50, workclass is Self-emp, income is >50K
```

Tests show it accepts variants with `is` or `=` separators and optional `Sample N:` prefixes. After parsing, construct a DataFrame with `model.columns + model.off_table_features` and assert the expected shape.

## Check behavior

`model.check()` verifies OpenAI settings and data-access mode. It raises `InitializationError` when the API key is missing or no valid raw-data/metadata access mode has been set.

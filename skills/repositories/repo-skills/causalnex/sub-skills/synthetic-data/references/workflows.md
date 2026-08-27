# Synthetic Data Workflows

## 1. Generate a toy DAG and sample tabular data

```python
from causalnex.structure.data_generators import generate_structure, sem_generator

sm = generate_structure(num_nodes=4, degree=2)
df = sem_generator(sm, schema={0: "binary", 1: "continuous", 2: "categorical:3", 3: "count"}, n_samples=100, seed=0)
```

Use this when you need a repeatable benchmark dataset for another CausalNex workflow.

## 2. Generate feature-specific toy dataframes

```python
from causalnex.structure.data_generators import (
    generate_binary_dataframe,
    generate_categorical_dataframe,
    generate_continuous_dataframe,
    generate_count_dataframe,
)

bin_df = generate_binary_dataframe(sm, n_samples=20, seed=0)
cont_df = generate_continuous_dataframe(sm, n_samples=20, seed=0)
```

These helpers are convenient when you want a dataframe instead of a NumPy array.

## 3. Generate a dynamic DAG and time series

```python
from causalnex.structure.data_generators import generate_structure_dynamic, generate_dataframe_dynamic

sm_dyn = generate_structure_dynamic(num_nodes=3, p=1, degree_intra=1, degree_inter=1)
dyn_df = generate_dataframe_dynamic(sm_dyn, n_samples=50)
```

Use this when you need lagged causal structure or a synthetic dynamic benchmark.

## 4. Expand and transform time-series inputs

```python
import pandas as pd
from causalnex.structure.transformers import DynamicDataTransformer

df = pd.DataFrame({"a": [0.0, 1.0, 0.0, 1.0], "b": [1.0, 0.0, 1.0, 0.0]})
transformed = DynamicDataTransformer(p=1).fit_transform(df)
```

The transformer produces lagged columns that line up with dynamic structure-learning workflows.

## 5. Map categorical variables to features

```python
from causalnex.structure.categorical_variable_mapper import VariableFeatureMapper

mapper = VariableFeatureMapper({"a": "binary", "b": "categorical:3", "c": "continuous"})
print(mapper.get_feature_names("b"))
```

Use this when a downstream algorithm needs one-hot feature indices for categorical variables.

## 6. Stationary dynamic fixtures

`gen_stationary_dyn_net_and_df` is the quickest route to a synthetic dynamic DAG plus a matching dataframe when you need a ready-made fixture for testing or smoke checks.

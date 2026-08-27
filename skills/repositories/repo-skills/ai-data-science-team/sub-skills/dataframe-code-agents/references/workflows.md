# Workflows: single-agent pandas code generation

These workflows assume:

- The data is already loaded in memory.
- `llm` is a caller-supplied LangChain-compatible chat model object.
- The task needs one code-generating pandas agent, not a composed analyst team.

For file loading or EDA-only summaries, route to `../../data-access-and-eda/SKILL.md`. For composed analyst/team flows, route to `../../multiagent-and-app-workflows/SKILL.md`.

## Shared setup

```python
import pandas as pd

from ai_data_science_team.agents import (
    DataCleaningAgent,
    DataWranglingAgent,
    DataVisualizationAgent,
    FeatureEngineeringAgent,
)

# Example in-memory data; replace with the caller's already-loaded DataFrame.
df = pd.DataFrame(
    {
        "customer_id": [1, 2, 2, 3],
        "segment": ["A", "B", "B", None],
        "amount": [10.0, None, None, 40.0],
        "event_date": ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-04"],
        "churned": [False, True, True, False],
    }
)
```

Choose one agent per task. If the user asks for a sequence such as load → clean → visualize, route loading elsewhere, then run the relevant single agents in explicit order or use a multiagent workflow when composition is the real requirement.

## Data cleaning

Use `DataCleaningAgent` when the user wants missing-value handling, duplicate removal, type cleanup, or generic outlier handling for one DataFrame.

```python
cleaner = DataCleaningAgent(
    model=llm,
    n_samples=20,
    log=False,
)

cleaner.invoke_agent(
    data_raw=df,
    user_instructions=(
        "Clean the data for analysis. Preserve customer_id and do not remove outliers "
        "unless they are clearly impossible values."
    ),
    max_retries=2,
    retry_count=0,
)

cleaned_df = cleaner.get_data_cleaned()
cleaning_code = cleaner.get_data_cleaner_function(markdown=False)
cleaning_steps = cleaner.get_recommended_cleaning_steps(markdown=False)
cleaning_response = cleaner.get_response()
```

Operational notes:

- Default cleaning recommendations include dropping columns with more than 40% missing values, simple mean/mode imputation, type conversion, duplicate removal, optional remaining-missing-row removal, and extreme IQR outlier removal.
- Add user instructions when a business rule must override generic cleaning, such as preserving an ID column or avoiding outlier removal.
- Inspect `data_cleaner_error` and `data_cleaning_summary` in the response before trusting the output.

## Data wrangling

Use `DataWranglingAgent` when the user wants joins, merges, reshaping, aggregation, computed columns, category cleanup, or one output table from multiple input tables.

### Single DataFrame wrangling

```python
wrangler = DataWranglingAgent(
    model=llm,
    n_samples=20,
    log=False,
)

wrangler.invoke_agent(
    data_raw=df,
    user_instructions=(
        "Group by segment and calculate row count plus mean amount. "
        "Return one row per segment."
    ),
    max_retries=2,
    retry_count=0,
)

summary_df = wrangler.get_data_wrangled()
wrangling_code = wrangler.get_data_wrangler_function(markdown=False)
```

### Multiple DataFrame wrangling

```python
customers = pd.DataFrame(
    {"customer_id": [1, 2, 3], "segment": ["A", "B", "A"]}
)
orders = pd.DataFrame(
    {"customer_id": [1, 1, 2, 3], "amount": [10, 15, 20, 30]}
)

wrangler = DataWranglingAgent(model=llm, n_samples=10, log=False)

wrangler.invoke_agent(
    data_raw=[customers, orders],
    user_instructions=(
        "Join customers to orders on customer_id, then return total amount "
        "and order count per customer. Avoid Cartesian products."
    ),
    max_retries=2,
    retry_count=0,
)

customer_order_features = wrangler.get_data_wrangled()
```

Operational notes:

- `DataWranglingAgent` converts a single DataFrame to a dict and a list of DataFrames to a list of dicts before graph execution.
- Inside the sandbox, generated wrangling functions receive a list of pandas DataFrames.
- Always state join keys and desired output grain for multi-table tasks.
- Do not use this agent for plotting; route charts to `DataVisualizationAgent`.

## Data visualization

Use `DataVisualizationAgent` when the user wants a Plotly visualization from one DataFrame.

```python
viz = DataVisualizationAgent(
    model=llm,
    n_samples=20,
    log=False,
)

viz.invoke_agent(
    data_raw=df,
    user_instructions=(
        "Create a bar chart of average amount by segment. Use clear axis labels "
        "and a descriptive title."
    ),
    max_retries=2,
    retry_count=0,
)

fig = viz.get_plotly_graph()
fig_dict = viz.get_response().get("plotly_graph")
viz_code = viz.get_data_visualization_function(markdown=False)
warnings = viz.get_response().get("data_visualization_warning")
```

Operational notes:

- Generated visualization code must return a JSON-serializable Plotly figure dict, not display or save a chart.
- The package profiles numeric, categorical, datetime, boolean, low-cardinality, high-cardinality, alias, and unit hints to help the model choose columns.
- Validation reconstructs the Plotly figure and may warn if the chart type does not match explicit user instructions.
- On reconstruction failure, the package attempts a simple fallback chart from detected column types.
- Use `run_smoke_tests(data_raw=..., prompts=...)` only when model calls are acceptable; it invokes the visualization agent repeatedly.

## Feature engineering

Use `FeatureEngineeringAgent` when the user wants a model-ready table from one DataFrame with generic, deterministic feature transforms.

```python
features = FeatureEngineeringAgent(
    model=llm,
    n_samples=20,
    log=False,
)

features.invoke_agent(
    data_raw=df,
    target_variable="churned",
    user_instructions=(
        "Prepare features for a binary classifier. Preserve the target column, "
        "one-hot encode categoricals, and create date-derived columns from event_date."
    ),
    max_retries=2,
    retry_count=0,
)

feature_df = features.get_data_engineered()
feature_code = features.get_feature_engineer_function(markdown=False)
feature_steps = features.get_recommended_feature_engineering_steps(markdown=False)
```

Operational notes:

- Default feature steps include type conversion, constant/unique feature removal, high-cardinality bucketing, one-hot encoding, boolean conversion, datetime feature extraction, and target handling.
- If `target_variable` is supplied, validation requires the returned DataFrame to include that column.
- The prompt discourages domain-specific invented features unless the user explicitly requests them.
- Use feature engineering here; route actual training, H2O, or MLflow requests to `../../modeling-and-mlflow/SKILL.md`.

## Lower-level graph factory pattern

Use factories only when the caller needs a compiled graph instead of the wrapper methods.

```python
from ai_data_science_team.agents import make_data_cleaning_agent

cleaning_graph = make_data_cleaning_agent(
    model=llm,
    n_samples=10,
    log=False,
)

response = cleaning_graph.invoke(
    {
        "user_instructions": "Fill numeric missing values and remove duplicate rows.",
        "data_raw": df.to_dict(),
        "max_retries": 1,
        "retry_count": 0,
    }
)
```

Factory responses are graph state dicts. They do not provide the class wrapper getters unless wrapped separately.

## Inspection and recovery pattern

After any run:

```python
response = agent.get_response()

# Check the relevant error key first.
error_keys = [key for key in response if key.endswith("_error")]
errors = {key: response[key] for key in error_keys if response.get(key)}

if errors:
    print(errors)
else:
    generated_code = next(
        (response[key] for key in response if key.endswith("_function") and response.get(key)),
        None,
    )
    print(generated_code[:500] if generated_code else "No function recorded")
```

If there is an error:

1. Read the relevant generated function with the agent getter.
2. Read the specific error key and error log path if logging was enabled.
3. Rerun with clearer user instructions, a lower `n_samples`, fewer columns, or a smaller row sample.
4. Increase `max_retries` only within a bounded range; repeated identical failures usually mean the prompt/data contract needs to change.

## Choosing `bypass_*` options

| Option | Use when | Avoid when |
|---|---|---|
| `bypass_recommended_steps=True` | The user gives a precise recipe and wants to skip the recommendation node. | Human review is needed, because the package forces recommendations back on for review. |
| `bypass_explain_code=True` | The caller only needs output state and wants to skip the final deterministic report message. | The user wants a structured summary in `messages`. |
| `human_in_the_loop=True` | The user wants to review or edit generated steps/code before accepting the result. | Non-interactive or unattended runs. |
| `log=True` | The user wants generated code and errors persisted for audit/debugging. | The user wants no generated-code files. |

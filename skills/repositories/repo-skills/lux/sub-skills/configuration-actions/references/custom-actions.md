# Custom recommendation actions

Lux actions are the recommendation tabs shown for a dataframe. The global action manager lives at `lux.config.actions`. It contains both built-in actions and any user-registered custom actions for the current Python process.

## API contract

```python
lux.config.register_action(
    name: str = "",
    action: Callable[[Any], Any] = None,
    display_condition: Callable[[Any], Any] | None = None,
    *args,
) -> None

lux.config.remove_action(name: str = "") -> None
```

Behavior verified for Lux API 0.5.1:

- `name` is the action-manager key. The tab label shown in `df.recommendation` is taken from the dictionary returned by the action function under the key `"action"`; keep both strings aligned to avoid confusion.
- `action` must be callable. If it is not callable, `register_action` raises `ValueError("Action must be a callable")`.
- `display_condition`, when provided, must be callable. If it is not callable, `register_action` raises `ValueError("Display condition must be a callable")`.
- If `display_condition` is omitted, Lux tries the action for every non-empty dataframe where recommendations are generated.
- If `display_condition(ldf)` returns false, the action is skipped and no tab is added.
- Extra `*args` are stored as one tuple and passed to the action as `action(ldf, args)`, not expanded. Prefer closures or keyword-only factories unless you specifically want that tuple behavior.
- `remove_action(name)` deletes the global action. Removing an unknown name raises `ValueError("Option '<name>' has not been registered")`.
- Registering or removing an action marks the action manager as changed. If a dataframe has already displayed recommendations, still call `df.expire_recs()` before redisplay when you need deterministic refresh behavior.

## Action return shape

A custom action should return a dictionary with at least:

```python
{
    "action": "Action tab label",
    "description": "Short sentence explaining the recommendation set",
    "collection": vis_list,
}
```

`collection` should be a `lux.vis.VisList.VisList` with zero or more valid visualizations. Empty collections are ignored by the dataframe recommendation dictionary. A typical action creates a `VisList`, assigns scores when needed, sorts it, then calls `showK()` to respect `lux.config.topk`.

## Self-contained custom action recipe

This example registers a local/offline action that appears only when a dataframe has an `enabled` column whose values are all true.

```python
import lux
import pandas as pd
from lux.vis.VisList import VisList

ACTION_NAME = "Enabled quantitative by group"

# Keep custom action names unique. Remove an old copy before re-registering.
if ACTION_NAME in lux.config.actions:
    lux.config.remove_action(ACTION_NAME)


def enabled_quantitative_by_group(ldf):
    intent = [lux.Clause("?", data_type="quantitative"), lux.Clause("group")]
    collection = VisList(intent, ldf)
    for vis in collection:
        vis.score = 1.0
    collection.sort()
    return {
        "action": ACTION_NAME,
        "description": "Quantitative columns broken down by group for enabled dataframes.",
        "collection": collection.showK(),
    }


def only_when_enabled(ldf):
    try:
        return "enabled" in ldf.columns and bool(ldf["enabled"].all())
    except Exception:
        return False

lux.config.register_action(ACTION_NAME, enabled_quantitative_by_group, only_when_enabled)

failing = pd.DataFrame({
    "group": ["A", "A", "B", "B", "C", "C"],
    "x": [1, 2, 3, 4, 5, 6],
    "y": [2, 3, 5, 7, 11, 13],
    "enabled": [False, False, False, False, False, False],
})
failing.maintain_recs()
assert ACTION_NAME not in failing.recommendation

passing = failing.copy()
passing["enabled"] = True
passing.expire_recs()
passing.maintain_recs()
assert ACTION_NAME in passing.recommendation
assert len(passing.recommendation[ACTION_NAME]) > 0

lux.config.remove_action(ACTION_NAME)
```

## Design rules for reliable actions

- Import `lux` before creating the dataframe so the dataframe is a `LuxDataFrame`.
- Use at least five rows for local smoke data; very small dataframes produce Lux messages instead of normal recommendations.
- Keep validators fast, side-effect free, and defensive about missing columns or unexpected dtypes.
- Avoid network reads, external files, and mutable global state inside actions.
- Return a Lux `VisList`, not raw chart dictionaries or backend-specific chart objects.
- Use `lux.config.pandas_fallback = False` temporarily when debugging action failures that are otherwise hidden by Pandas fallback display.
- Remove experimental actions when done, especially in long-lived notebooks, because actions are global for the Python process.

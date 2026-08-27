# Discrete and count workflows

## Binary Logit with marginal effects

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

df = pd.DataFrame({"y": [0, 0, 0, 1, 1, 1, 1, 0], "x": [-3, -2, -1, 0, 1, 2, 3, -0.5]})
res = smf.logit("y ~ x", data=df).fit(disp=False)
print(res.params)
print(res.get_margeff().summary())
```

Use `disp=False` in automation when optimizer progress text is not useful. Still inspect convergence metadata and warnings.

## Count model escalation

Start with Poisson when the response is a nonnegative count:

```python
exog = sm.add_constant(df[["x"]])
poisson = sm.Poisson(df["count"], exog, exposure=df.get("exposure")).fit(disp=False)
```

Escalate when evidence supports it:

- Overdispersion: compare Poisson residuals/variance and consider `NegativeBinomial` or `NegativeBinomialP`.
- Many structural zeros: consider a zero-inflated model with a separate inflation design.
- Counts observed only after a threshold: consider truncated or hurdle models.
- Group-specific nuisance intercepts: consider conditional count models.

## Ordered and multinomial outcomes

For ordered categories, use `OrderedModel` and avoid adding a separate constant if the model handles thresholds/intercepts internally. For unordered categories, use `MNLogit`; set a baseline/reference category deliberately and inspect category coding.

## Prediction and classification

Predicted probabilities are not decisions. State the threshold or decision rule separately:

```python
prob = res.predict(new_df)
label = (prob >= 0.5).astype(int)
```

For count models, `predict` usually returns an expected count or a model-specific distribution quantity. Read the result/model docstring before requesting probabilities for exact count values.

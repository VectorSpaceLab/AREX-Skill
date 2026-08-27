# Discrete/count API reference

## Binary and multinomial choice

Common classes available from `statsmodels.api` or direct modules:

| Class/wrapper | Use |
| --- | --- |
| `sm.Logit(endog, exog, offset=None, check_rank=True, **kwargs)` / `smf.logit` | Binary logit. |
| `sm.Probit(endog, exog, ...)` / `smf.probit` | Binary probit. |
| `sm.MNLogit(endog, exog, ...)` / `smf.mnlogit` | Unordered multinomial outcomes. |
| `OrderedModel(endog, exog, distr="logit"|"probit")` | Ordered categorical outcomes; imported from `statsmodels.miscmodels.ordinal_model`. |
| `ConditionalLogit`, `ConditionalMNLogit`, `ConditionalPoisson` | Grouped/conditional likelihood models. |

## Count models

| Class/wrapper | Use |
| --- | --- |
| `sm.Poisson(endog, exog, offset=None, exposure=None, missing='none', check_rank=True, **kwargs)` / `smf.poisson` | Baseline count model. |
| `sm.NegativeBinomial`, `sm.NegativeBinomialP`, `smf.negativebinomial` | Overdispersed count outcomes. |
| `GeneralizedPoisson` | Flexible count variance. |
| `ZeroInflatedPoisson`, `ZeroInflatedNegativeBinomialP`, `ZeroInflatedGeneralizedPoisson` | Count models with an inflation component. |
| `HurdleCountModel`, `TruncatedLFPoisson`, `TruncatedLFNegativeBinomialP` | Hurdle/truncated count surfaces. |

## Result surfaces

Discrete-model results commonly support:

- `params`, `bse`, `pvalues`, `conf_int()`, `summary()`.
- `predict(...)`, often returning probabilities or expected counts depending on model/options.
- `get_margeff(...)` for marginal effects on supported discrete models.
- `prsquared`, likelihood values, information criteria, and convergence metadata such as `mle_retvals` for many maximum-likelihood fits.

Check the exact result class before promising a method: not every count, zero-inflated, or conditional model exposes identical post-estimation helpers.

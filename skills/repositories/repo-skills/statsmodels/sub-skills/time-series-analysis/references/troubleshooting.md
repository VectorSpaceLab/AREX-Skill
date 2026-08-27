# Time-series troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Forecast index is integer or warning says no frequency | Date index lacks a fixed frequency | Set or infer frequency, use a `PeriodIndex`, or pass `dates`/`freq` where supported. |
| Forecast with `exog` fails | Future exogenous values missing or wrong shape | Pass future `exog` for every forecast step with same columns/order as training. |
| ARIMA/SARIMAX convergence warning | Poor order choice, scaling, nonstationarity, boundary parameters | Start simpler, difference or transform data, relax/enforce stationarity deliberately, scale exog, inspect residuals. |
| Non-invertible or non-stationary starting parameters | Order choice conflicts with data | Try lower orders, set enforcement flags intentionally, or use information-criterion order search. |
| STL period error or odd seasonal output | Missing/wrong seasonal period | Provide a domain-appropriate `period`; verify enough cycles exist. |
| VAR lag selection fails | Too few observations for requested lags | Reduce `maxlags`, increase data, or use a simpler univariate model. |
| X-13/X-12 error | External executable missing or path not configured | Treat as optional; install/configure binary or use STL/SARIMAX alternatives. |

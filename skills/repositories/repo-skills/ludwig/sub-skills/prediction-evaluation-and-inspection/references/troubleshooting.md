# Prediction/Evaluation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `model` or metadata missing | Directory is not a complete saved Ludwig model | Use the model subdirectory produced by training and avoid skip-save flags for reusable models. |
| Dataset feature column missing | Prediction/evaluation data does not match training config | Generate a fixture or inspect config feature names before prediction. |
| Evaluation metrics absent | Dataset lacks output labels or split is wrong | Include output columns and choose the correct split. |
| Forecast raises a timeseries error | Model was not configured for timeseries forecasting | Train a timeseries model or route to normal prediction. |
| Generation config ignored or fails | Non-LLM model or invalid generation parameters | Use generation only with `model_type: llm` models. |
| Collect activations consumes memory | Large model/dataset | Use a small sample and collect only named layers. |

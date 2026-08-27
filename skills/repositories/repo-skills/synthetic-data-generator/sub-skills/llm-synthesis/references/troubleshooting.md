# LLM synthesis troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `InitializationError: openai_API_key NOT found.` | `OPENAI_KEY` is missing and `set_openAI_settings` was not called. | Set `OPENAI_KEY` or call `model.set_openAI_settings(API_url, API_key)`. |
| Request hits wrong endpoint | `OPENAI_URL` or API URL is wrong. | Confirm the base URL includes the correct `/v1/`-style path for the provider. |
| No data access type specified | `fit` was not called with a DataFrame/DataLoader/Metadata. | Call `fit(df)`, `fit(dataloader)`, `fit(metadata)`, or `fit(metadata=metadata)` before `check()`/generation. |
| Response parser returns fewer rows than expected | LLM output format deviated from `column is value` per line. | Lower temperature, reduce `query_batch`, add stronger format instructions, or parse/repair line-by-line. |
| Off-table columns missing | LLM ignored `off_table_features` or parser columns do not match. | Add explicit feature names to prompt, reduce generation count, and validate parsed DataFrame columns. |
| Token timeout or truncation | `query_batch`, `max_tokens`, or table width is too large. | Reduce `query_batch`, fit with metadata instead of raw rows, or choose a model with a larger context window. |

Privacy reminder: raw-data fitting can embed real row values in prompts. Prefer metadata-only fitting when the user cannot send real data to an external provider.

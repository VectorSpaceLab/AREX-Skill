# Client Inference Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Unsupported model type | model architecture not registered by Petals | choose a supported BLOOM/Llama/Falcon/Mixtral-compatible model or run ordinary Transformers locally |
| Gated model/tokenizer error | missing accepted terms or token | authenticate and verify model access before retrying |
| Missing blocks/no route | swarm does not host all required DHT keys | verify `initial_peers`, `dht_prefix`, model id, and server block ranges |
| Hanging retries | remote peer failures or unbounded retry | set `PETALS_MAX_RETRIES` while debugging and inspect route logs |
| `max_length` / `max_new_tokens` assertion | no active session and ambiguous cache budget | pass exactly one of those arguments |
| `Maximum length exceeded` | session cache budget too small | recreate the session with a larger `max_length` |
| custom attention/position assertion | Petals remote forwards do not support that mask/position pattern | omit masks or use all-ones masks; keep consecutive positions |
| poor batched generation | tokenizer lacks padding config | set `pad_token_id` and `padding_side` intentionally before batching |
| resumed beam warning | session has lost intermediate beam state | use greedy/sampling continuation or start a fresh session for beam search |

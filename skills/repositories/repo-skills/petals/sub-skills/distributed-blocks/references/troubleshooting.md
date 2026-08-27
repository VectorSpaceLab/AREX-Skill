# Distributed Blocks Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| hidden-state shape assertion | token IDs passed to `RemoteSequential` | embed tokens first or use the high-level model route |
| no remote route | DHT prefix/block range mismatch | compare config prefix and server announcements |
| `Maximum length exceeded` | session budget too small | recreate session with larger `max_length` |
| deep prompt shape error | prompt tensor count/shape mismatches slice | use `[num_blocks, batch_or_1, prefix_len, hidden]` |
| dtype mismatch | `torch_dtype` resolved differently than expected | inspect config dtype and dtype resolution behavior |
| tensor parallel warning | non-BLOOM or uneven GPUs | use BLOOM-supported TP path or run without TP |
| quantization import error | bitsandbytes backend mismatch | use `QuantType.NONE` / `--quant_type none` until repaired |
| local block load hangs | model weights/cache/network not approved | stop and get cache/download approval |

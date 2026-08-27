# Audio Analysis Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `vector score` input error | Score item does not contain exactly two audio paths. | Use `build_vector_job.py --pair id:enroll.wav:test.wav`. |
| KWS always false or true | Threshold not matched to model/data. | Adjust `--threshold`; inspect score before deciding. |
| CLS top-k assertion | `--topk` larger than available label count. | Use a smaller `--topk` or provide the correct label file. |
| Sample-rate failure | Vector/KWS expect 16 kHz; CLS resources are 32 kHz. | Validate or resample intentionally; use `--yes` where supported. |
| Model download failure | First inference run fetches model archive. | Set writable `PPSPEECH_HOME`, confirm network/cache, retry transient CDN errors. |
| Audio search demo fails | Milvus/MySQL/Docker/config/data prerequisites missing. | Treat as external-service deployment; plan services before running app code. |
| `stats --task kws` fails | Registry display caveat. | Use `paddlespeech kws --help` and direct KWS references. |

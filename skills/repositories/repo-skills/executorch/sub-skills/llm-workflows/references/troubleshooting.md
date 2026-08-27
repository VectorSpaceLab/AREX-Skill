# LLM Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Export script wants to download weights | Model assets not local | Ask for approved download/cache path or local checkpoint; do not download by default. |
| Token outputs differ before backend execution | Tokenizer/template mismatch | Compare token ids and prompt templates before debugging backend. |
| Export fails on generation loop | Autoregressive control flow not exportable as one dynamic loop | Export prefill/decode/body methods and handle loop logic in the runner/app. |
| Runtime OOM | KV cache/sequence length/model too large | Reduce max sequence/batch, quantize, use program-data separation, or choose a larger target. |
| QNN LLM compile/run fails | SDK/device/compile spec or unsupported op issue | Route to `qualcomm`; separate export, compile, and device execution failures. |


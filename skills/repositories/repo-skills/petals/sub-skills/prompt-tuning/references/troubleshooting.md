# Prompt-Tuning Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `pre_seq_len` assertion | tuning mode set with no prefix tokens | set `pre_seq_len > 0` |
| unsupported tuning mode | mode other than `ptune`/`deep_ptune` | choose a supported mode |
| prompt shape failure | deep prompts do not match layer count/batch/prefix/hidden | keep `[num_layers, batch_or_1, prefix_len, hidden]` semantics |
| no trainable params | prompts not initialized or all params frozen | pass tuning args to constructor and print `requires_grad` params |
| unexpected full-model training | optimizer includes frozen or unintended params | filter to `requires_grad` and expected prompt/head names |
| attention mask assertion | padded zero mask passed to remote blocks | omit the mask or use all-ones paths |
| dataset/W&B/network failure | notebook-style dependency made implicit | make dataset/model/logging access explicit and optional |
| AMP/CUDA failure | CUDA unavailable or wrong dtype | gate AMP on `torch.cuda.is_available()` and use CPU-safe dtype for smoke |
| adapter rejected | missing safetensors artifact | use a safe adapter repository or do not preload adapter |
| bitsandbytes import failure | incompatible optional backend stack | disable quant/adapters until Torch/CUDA/Triton/bitsandbytes are matched |

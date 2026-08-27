# Benchmark troubleshooting

- **Wrong PNG count**: the sample folder must contain exactly `numgen` PNG files.
- **Missing prompt stem**: every sample filename stem needs a matching `prompts.json` key.
- **Prompt key mismatch**: the prompt map should describe the concrete prompt used for that file, not a template.
- **Bad target-path syntax**: split the target paths on `+` and make sure no segment is empty.
- **CUDA missing**: the evaluator is CUDA-backed; do not expect the full metric run to work on CPU.
- **CLIP or DINO weights download fails**: cache the weights or retry in a network-enabled environment.
- **Pickle update surprises**: `outpkl` is updated or extended using the sample-root key.
- **Image layout is wrong**: keep the sample directory PNG-only so the evaluator and the validator count the same files.

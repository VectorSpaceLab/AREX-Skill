# Performance reference

For an inference benchmark, control:

- exact model/revision, prompt or dataset, seed, dimensions, frame count, FPS,
  inference steps, guidance, precision, and backend;
- GPU count and parallelism, offload settings, quantization, and compile flags;
- whether timing includes model load, first-run compilation, decoding, and file
  encoding.

For `torch.compile`, discard the first generation because graph construction can
be tens of seconds or minutes. Reuse exact shapes to measure steady state. For
attention comparisons, reinstantiate the generator after changing the backend.
Report median/p95 or repeated samples rather than one noisy number.

Memory results should identify peak allocation source and whether frame/latent
return buffers, VAE decode, or model load dominate. A faster denoising loop may
not improve end-to-end latency if decode or encoding dominates.

`fastvideo bench` targets a running server and supports dataset/task, host/port,
concurrency, request rate, dimensions, frames, FPS, and output-file controls.
Read its installed `--help` output before constructing a benchmark command.

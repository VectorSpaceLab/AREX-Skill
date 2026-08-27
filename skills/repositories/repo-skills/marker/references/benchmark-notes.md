# Benchmark Notes

Marker's README documents benchmark context for conversion quality, table extraction, and throughput. Treat those benchmark scripts and datasets as evidence for performance expectations, not as runtime dependencies for this skill.

## Public Claims To Preserve Carefully

- Marker emphasizes high-speed document conversion with support for markdown, JSON, chunks, and HTML.
- Throughput scales with batching/workers and available VRAM; long PDFs and many workers can be memory-heavy.
- LLM-assisted mode can improve table, form, equation, and complex layout quality, but requires provider configuration and may add latency/cost.
- Benchmark scripts can require dataset downloads, cloud service comparisons, GPUs, and scoring dependencies, so they are not safe default smoke tests.

## Safe Use In Agent Work

- Use benchmark facts only for qualitative guidance unless the user asks to reproduce benchmarks.
- Do not run benchmark scripts by default.
- For user performance questions, first ask whether they want local throughput measurement, quality scoring, or deployment sizing.
- Prefer small user-provided sample documents for profiling over repository benchmark datasets.

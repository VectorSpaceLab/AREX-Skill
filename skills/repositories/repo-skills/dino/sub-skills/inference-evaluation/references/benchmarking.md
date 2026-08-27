# Safe GFLOPS and FPS inspection

`tools/benchmark.py` is a source-provided architecture benchmark, not a
checkpoint evaluator. Use it only after a short import/model-build preflight
and only when a CUDA measurement is explicitly needed.

## Invocation

From the DINO project root:

```bash
python tools/benchmark.py \
  --output_dir /tmp/dino-flops \
  -c config/DINO/DINO_4scale.py \
  --options batch_size=1 \
  --coco_path /path/to/COCODIR
```

The parser is inherited from `main.get_args_parser`, so `-c/--config_file` is
required. `--output_dir` is operationally required even though the shared
parser defaults it to an empty string: the benchmark writes
`output_dir/flops/log.txt`. Pass a real writable directory. Use the 5-scale
config explicitly when measuring that architecture.

The script builds the configured model, moves it to CUDA, builds the COCO
validation dataset, takes 20 transformed validation images, traces each input
for a flop count, and measures forward time with CUDA synchronization. It warms
up each timing call for 10 iterations and times 10 iterations; the final timing
summary excludes the first five image slots, leaving 15 reported timing
samples. It does not load `--resume` or any checkpoint, so GFLOPS/FPS are
architecture/config measurements with randomly initialized weights, not proof
that a particular pretrained checkpoint is accurate or faster.

## Output

The JSON-like record appended to `flops/log.txt` contains:

- `nparam`: number of trainable parameters;
- `detailed_flops`: per-operation GFLOP counts from the JIT trace for the last
  traced image;
- `flops`: mean/std/min/max of total GFLOPS across the 20 images;
- `time`: mean/std/min/max seconds across the 15 post-warmup samples; and
- `fps`: reciprocal of the mean time.

The command text is written before the record. Preserve the config, input
resolution/transform settings, Torch/CUDA versions, GPU model, and exact
command when comparing runs.

## Limitations and safe interpretation

- **CUDA only.** The code calls `model.cuda()` and `torch.cuda.synchronize()`;
  `--device cpu` is not supported by this script. Missing CUDA or an unusable
  extension is a setup blocker, not a zero-FPS result.
- **COCO data is still required.** The benchmark uses `build_dataset('val',
  args)`, so the normal `val2017` and `instances_val2017.json` paths must exist.
  Its validation transform is the standard max-size-1333 path unless the
  config/overrides change it.
- **No checkpoint loading.** A benchmark result cannot certify a checkpoint,
  AP, or output quality. For that, use `main.py --eval`.
- **JIT trace coverage is partial.** Unsupported operations are skipped and
  the script logs a warning such as `Skipped operation ...`. GFLOPS may be an
  undercount, especially around custom deformable attention. Treat the number
  as a repeatable estimate for this script, not a hardware-independent FLOP
  definition.
- **Timing is not end-to-end service latency.** Dataset decode, host-to-device
  copy, postprocessing, visualization, distributed coordination, and startup
  are outside the measured model forward. GPU clocks, warmup, AMP, and other
  processes affect the result.
- **Workload controls matter.** `--options batch_size=1` is useful to make the
  intent explicit, but this tool appends one image at a time to the model input.
  A debug environment flag, `GFLOPS_DEBUG_SHILONG=INFO`, selects a fixed
  `1280x800` resize for flop inspection; record that override because it changes
  the workload.
- **No long default hidden in the bundled smoke tool.** Use
  `scripts/inference_smoke.py` for one-image output; do not add a dataset loop
  to it when a bounded check is wanted.

If the only goal is to compare predicted boxes or labels, do not run this
benchmark. If the goal is an official AP number, do not replace COCO evaluation
with it.

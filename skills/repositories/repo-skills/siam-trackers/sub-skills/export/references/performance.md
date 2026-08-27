# NanoTrack Profiling and Throughput Reference

## What the Source Workflows Establish

NanoTrack contains two performance-oriented workflows:

- `cal_macs_params.py` calls `thop.profile`, caches a `1x3x127x127` template,
  profiles one `1x3x255x255` full-model call, and formats MAC and parameter
  counts;
- `cal_speed.py` sets one PyTorch CPU thread, caches a template once, warms
  100 `model.track` calls, then wall-times 1000 `model.track` calls.

Those are methodology facts, not reproduced measurements. The speed loop loads
a snapshot, automatically selects CUDA when available, uses random batch-one
inputs, omits preprocessing and postprocessing, and does not synchronize CUDA
around wall-clock timing. Its long loop can occupy a GPU and is not a safe
construction-time smoke test. Start with one or two bounded shape forwards, then
run a benchmark only with explicit resource approval. Neither source script is
copied as a runtime script because `cal_macs_params.py` assumes a fixed config
and `cal_speed.py` assumes a snapshot, hard-coded defaults, and a long loop.

## Historical Project-Reported Table

The project documentation reports the following figures. Preserve the label
"project-reported" when citing them; the exact tool versions, FLOP convention,
export settings, hardware, and parity status are not supplied here.

| Variant | Backbone ONNX size | Head ONNX size | Reported FLOPs | Reported parameters |
| --- | ---: | ---: | ---: | ---: |
| NanoTrackV1 | 752K | 384K | 75.6M | 287.9K |
| NanoTrackV2 | 1.0M | 712K | 84.6M | 334.1K |
| NanoTrackV3 | 1.4M | 1.1M | 115.6M | 541.4K |

The same documentation says V1 and V2 can exceed 200 FPS on an Apple M1 CPU,
but provides no complete timing protocol. Do not present that as a reproduced
result or compare it directly with CUDA, NCNN, full-pipeline, or thermally
sustained measurements.

## MACs, FLOPs, Parameters, and File Size

These quantities are different:

- **Parameters** count learned scalar values. Shared/tied parameters and buffers
  need explicit conventions.
- **MACs** count multiply-accumulate operations according to a profiler's
  operator rules. `thop.profile` reports MACs and parameters.
- **FLOPs** may count one MAC as one operation or as two floating-point
  operations. Tools also differ on activation, normalization, correlation, and
  unsupported custom operators.
- **Serialized size** depends on dtype, graph constants, compression, metadata,
  simplification, and file format. It is not a compute metric.
- **Latency/FPS** depends on backend, hardware, threads, shape, batch, warmup,
  synchronization, preprocessing, postprocessing, and thermal state.

Always report the tool and convention. If a THOP value is labeled "FLOPs",
state the conversion rule rather than silently renaming MACs.

## Structural Profile Protocol

For a full NanoTrackV3 track-step profile:

1. confirm the V3 backbone/head/checkpoint tuple;
2. load trusted weights and use evaluation mode;
3. create batch-one NCHW tensors `template=[1,3,127,127]` and
   `search=[1,3,255,255]`;
4. call template initialization once, outside the profiled track call;
5. profile the search/track call with `thop`, recording unsupported-operator
   warnings and custom counting hooks;
6. separately report total parameters and, if useful, split backbone/head
   parameters;
7. record package versions, dtype, device, and whether the profile includes
   template work.

Do not use random-initialized parameter counts as evidence that checkpoint
loading succeeded. Parameter count may be structurally valid without weights,
but any weight-dependent claim is not.

## Reproducible Throughput Protocol

Define the measurement boundary before collecting a number:

- **Core track step:** cached template plus search backbone/head only.
- **Model pair:** template once plus a documented number of searches.
- **End-to-end tracker:** preprocessing, model, decoding, state update, and data
  transfer.
- **Application:** capture/decode/render in addition to tracker work.

For core track-step comparability:

1. use batch one and fixed input shapes;
2. load trusted weights, call `eval()`, and disable gradients;
3. record CPU/GPU model, backend, dtype, thread counts, power/clock policy, and
   software versions;
4. warm up enough to stabilize compilation, caches, and allocator behavior;
5. time multiple independent repeats, not only one aggregate interval;
6. synchronize before and after each CUDA timed region, or use correctly
   synchronized CUDA events;
7. report median and a spread such as min/max or percentiles;
8. divide the number of timed **search** calls by elapsed seconds; do not count
   warmup or template initialization unless the boundary includes them;
9. measure end-to-end latency separately from model-only throughput;
10. monitor memory and thermal throttling for mobile or sustained runs.

The source values of 100 warmups and 1000 timed calls are reasonable historical
starting points, not mandatory constants. Reduce them for bounded probes and
increase or repeat only after observing stable, resource-safe behavior.

## Use the No-Run Plan Checker

From the sub-skill directory:

```bash
python scripts/profile_shape_check.py \
  --device cpu --timer wall --warmup 100 --iterations 1000 --repeats 5
```

For CUDA wall timing:

```bash
python scripts/profile_shape_check.py \
  --device cuda --timer wall --synchronize \
  --warmup 100 --iterations 1000 --repeats 5
```

To summarize completed repeat durations without executing a model:

```bash
python scripts/profile_shape_check.py \
  --device cpu --iterations 1000 --repeats 3 \
  --elapsed-seconds 4.9 5.1 5.0
```

The checker validates shapes and methodology arguments, then emits JSON. It does
not import PyTorch, load weights, allocate a GPU, run THOP, or make a performance
claim.

## Reporting Template

Report at least:

```text
variant: NanoTrackV3
boundary: cached-template core track step
input: NCHW batch=1, template 127x127, search 255x255
weights: caller-verified digest <digest>
backend/device/dtype: <values>
threads: <intra-op/inter-op/backend values>
warmup/timed/repeats: <values>
timer and synchronization: <values>
latency: median <value> ms, spread <value>
throughput: <value> search calls/s
preprocess/postprocess/transfers included: <yes/no per item>
MACs/parameters: <value>, tool/version/convention <value>
known unsupported profiler operators: <list>
```

Avoid the bare label "FPS" if a timed iteration is not a complete processed
frame.

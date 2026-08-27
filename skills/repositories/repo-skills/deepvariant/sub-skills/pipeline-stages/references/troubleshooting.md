# Pipeline-stage Troubleshooting

Use this matrix for DeepVariant failures below the high-level wrapper layer. Treat full stage reruns, Docker pulls, GPU runs, native tests, and large genomics IO as conditional and unsafe unless the user explicitly confirms their environment and data.

## Invalid Sharded Specs

Symptoms:

- Error text says a file is not a sharded file specification.
- A path like `examples@0.gz` or `examples@foo.gz` appears in commands, or a suspicious suffixless spec such as `examples.gz@32` hides the intended TFRecord extension.
- Downstream tools cannot find files even though `@N` was used.

Checks:

```bash
python ../scripts/sharded_path_helper.py --spec examples.tfrecord@32.gz
```

Recovery:

- Use `prefix@N.suffix`, for example `examples.tfrecord@32.gz`; avoid forms like `examples.gz@32` for DeepVariant TFRecord outputs unless you have confirmed the target stage accepts the resulting concrete filenames.
- Ensure `N` is a positive integer.
- Remember that `@N` is a logical spec; actual files are `prefix-00000-of-000NN.suffix` through `prefix-000NN-of-000NN.suffix`.
- When pairing `--examples` with `--gvcf`, use identical shard counts.

## Missing `--task` With Sharded Output

Symptoms:

- Only one shard exists after a supposed multi-shard `make_examples` run.
- A user has `examples@32.gz` but ran one command without a task loop.
- `call_variants` or `postprocess_variants` reports missing shards.

Checks:

- Expand `--examples` with the helper and confirm all expected concrete files exist in the user's runtime environment.
- Review the wrapper dry-run command for `seq 0 N-1 | parallel ... --task {}` or equivalent orchestration.
- Confirm task values are integers from `0` through `N-1`.

Recovery:

- Run `make_examples` once per task for all shard numbers.
- If using a workflow engine, ensure it substitutes the task value rather than passing literal `{}`.
- For a small single-process debug run, use an unsharded output path and `--task 0`.
- Do not feed a partial shard set to `postprocess_variants` as if it were a complete sample.

## Glob vs `@N` Confusion

Symptoms:

- User tries to open `examples@32.gz` in a shell or editor.
- User passes `examples-*` to a writer command.
- `postprocess_variants` sees multiple unrelated CVO patterns in the same filename space.

Checks:

- Distinguish logical spec, concrete shard filenames, and shell glob patterns.
- For `call_variants --examples`, `@N`, comma lists, and wildcards can be acceptable reader inputs.
- For `make_examples` writers, prefer `@N` plus `--task`; for `call_variants --outfile`, prefer a `.tfrecord.gz` logical output or a concrete shard filename.

Recovery:

- Use `@N` when telling DeepVariant how many shards a logical collection has.
- Use `prefix-?????-of-000NN.suffix` or `prefix-*` only for reader-style discovery or manual checks.
- Keep CVO output basenames isolated because r1.10 `postprocess_variants` discovers dynamic `call_variants` shards from the input basename and rejects mixed patterns.

## Training vs Calling Mode Confusion

Symptoms:

- `truth_variants is required when in training mode`.
- `gvcf is not allowed in training mode`.
- `Do not specify --truth_variants in calling mode`.
- User asks why a final VCF was not produced from `make_examples --mode training`.

Checks:

- Confirm the intended goal: inference/calling, labeled example creation, or advanced candidate sweep.
- Inspect `--mode`, `--truth_variants`, `--confident_regions`, `--gvcf`, `--candidate_positions`, and `--proposed_variants`.

Recovery:

- For inference, use `--mode calling` and do not pass `--truth_variants`.
- For gVCF inference, keep `--mode calling` and pair `make_examples --gvcf` with postprocess gVCF flags.
- For training examples, use `--mode training`, provide truth/confident data, and route complete training workflow decisions to `../training-custom-models/SKILL.md`.
- For candidate sweep, require `--candidate_positions`, avoid `--proposed_variants`, and follow with a normal calling-mode `make_examples` run.

## gVCF Pairing Errors

Symptoms:

- `gVCF creation requires both nonvariant_site_tfrecord_path and gvcf_outfile flags to be set`.
- `gvcf is not allowed in training mode`.
- Final VCF exists but final gVCF is missing.
- gVCF postprocessing is unexpectedly slow or memory-heavy.

Checks:

- Verify `make_examples` used `--mode calling --gvcf nonvariant.tfrecord@N.gz`.
- Verify `postprocess_variants` includes both `--nonvariant_site_tfrecord_path nonvariant.tfrecord@N.gz` and `--gvcf_outfile output.g.vcf.gz`.
- Confirm `--examples` and `--gvcf` shard counts match.
- Check whether low-depth data or fine `--gvcf_gq_binsize` creates many non-variant blocks.

Recovery:

- Add both postprocess flags or remove both if VCF-only output is intended.
- Re-run `make_examples` in calling mode when non-variant TFRecords were never produced.
- Increase `--gvcf_gq_binsize` only when the user accepts coarser GQ bins.
- Tune `--cpus` and `--num_partitions` for memory pressure rather than blindly increasing CPU count.

## Contig and Index Mismatch

Symptoms:

- No examples are produced for expected regions.
- Errors reference missing contigs, invalid regions, unsorted reads, failed indexing, or FASTA/BAM incompatibility.
- Only shared contigs are processed, surprising the user.

Checks:

- Confirm FASTA `.fai` exists and is visible inside the runtime or container.
- Confirm BAM/CRAM exists, is coordinate-sorted, and has a visible index.
- Compare read-alignment contig names with FASTA contig names, especially `chr20` vs `20`, decoy contigs, alternate contigs, and GRCh37/b37/GRCh38 mismatches.
- Ensure `--regions`, BED, truth VCF, confident regions, and proposed variants use the same reference naming.

Recovery:

- Use the reference that matches the alignment and truth/confident resources.
- Regenerate missing indexes with user approval and appropriate tools.
- Fix region spelling rather than forcing DeepVariant to process absent contigs.
- For CRAM, ensure `--ref` is container-visible and matches CRAM expectations.

## Shape, Channel, or Model Metadata Mismatch

Symptoms:

- Errors or warnings mention input shape vs model shape mismatch.
- Errors or warnings mention input channels vs model channels mismatch.
- `model.example_info.json` or `example_info.json` is missing.
- Custom model inference works through one wrapper but not through manually assembled low-level commands.

Checks:

- Confirm `call_variants --checkpoint` points to the intended checkpoint file or SavedModel directory.
- Confirm the model directory contains `model.example_info.json` or legacy `example_info.json`.
- Confirm examples were generated with the same model type, channel list, alt-aligned pileup setting, and custom model metadata.
- For wrapper-to-low-level conversion, include `--checkpoint_json` when the dry-run used customized model metadata for make_examples or postprocess flags.

Recovery:

- Regenerate examples with the channel list/model metadata expected by the checkpoint.
- Pair custom checkpoints with their matching metadata file.
- Avoid manually editing `--channel_list` unless the model was trained for that exact channel set.
- Route custom training and fine-tuning design to `../training-custom-models/SKILL.md`.

## Memory and CPU Pressure

Symptoms:

- `make_examples` tasks are killed or extremely slow in high-depth or large-region runs.
- `call_variants` OOMs during TensorFlow inference.
- `postprocess_variants` OOMs, especially with gVCF enabled or high `--cpus`.
- GPU runs do not speed up because CPU input stages bottleneck.

Checks:

- Check shard count, per-task region size, coverage, model type, and whether small model or fast pipeline is enabled.
- For `call_variants`, check `--batch_size`, `--writer_threads`, GPU availability, and TensorFlow execution mode.
- For `postprocess_variants`, check `--cpus`, `--num_partitions`, variant density, and gVCF enabled state.
- For fast pipeline, verify `--num_shards`, shared-memory buffer size, `--shm-size`, and CPU cores left for input pipeline.

Recovery:

- Increase shard count for `make_examples` parallelism only when enough CPU and I/O are available.
- Reduce `call_variants --batch_size` or force `--execution_hardware=cpu` when GPU setup is broken.
- Lower `postprocess_variants --cpus` or increase `--num_partitions` to reduce peak memory.
- For GPU fast-pipeline use, reserve CPU cores for input feeding and ensure shared memory exceeds `buffer_size * num_shards` with headroom.

## TensorFlow or Compiled-extension Import Failures

Symptoms:

- Import errors mention TensorFlow, Nucleus, pybind modules, `examples_from_stream`, `make_examples_native`, htslib, pysam, or protobuf implementations.
- Lightweight package import succeeds but running a stage binary fails.
- Errors mention fast C++ protos or compiled proto requirements.

Checks:

- Determine whether the user is running official Docker/Bazel binaries or a lightweight inspection environment.
- Confirm the container tag matches the intended DeepVariant version and CPU/GPU choice.
- Confirm native binaries and shared libraries are in the runtime image, not just Python source files.

Recovery:

- Prefer official DeepVariant Docker/Singularity/Bazel-built binaries for production stages.
- Do not promise that pip-installed or source-only Python imports can execute full stages.
- If the user must build from source, route them to shared install/runtime guidance in `../../references/install-and-runtime.md` and require explicit approval before host mutation.

## Extra-args Misrouting

Symptoms:

- A wrapper accepts an extra arg but the low-level binary rejects it.
- An extra arg silently changes a wrapper default.
- Boolean flags appear in a form the wrapper parser does not translate as intended.

Checks:

- Identify which wrapper extra-args flag was used and which low-level binary owns the option.
- Split comma-separated `flag=value` values carefully; quoted values can contain commas.
- Review wrapper warnings about previously set flags being overwritten.

Recovery:

- Move each flag to the correct wrapper bucket: make_examples, call_variants, or postprocess_variants.
- Use `flag=true` or `flag=false` for wrapper extra args so generated low-level commands become the intended boolean setting.
- Avoid overriding core wrapper-set paths such as `examples`, `gvcf`, `infile`, `outfile`, `ref`, or `checkpoint` unless the user intentionally wants a custom low-level command plan.

# Inference workflows

## Single prompt

1. Confirm the base model and delta checkpoint.
2. Check the delta layout before sampling.
3. Use a single prompt when you only need one montage.
4. Keep the freeze mode and compression flag aligned with the checkpoint you are loading.
5. Expect one horizontal montage plus a `samples/` folder of individual images.

## Prompt file

1. Put one prompt per line in the prompt file.
2. Keep blank lines out of the file.
3. The sampler reads the file line by line and reuses each prompt for the requested batch size.
4. Each prompt line becomes a separate montage and sample set.
5. The montage file name is derived from the first 50 characters of the prompt.

## Compressed delta

1. Check whether the delta layout contains `u` / `v` factors.
2. Use the compression flag only when the checkpoint is compressed.
3. If the layout checker reports an uncompressed file, do not pass the compression flag.

## SDXL sampling

1. Use the XL sampling path when the checkpoint came from the SDXL training route.
2. Keep the dual-tokenizer / dual-text-encoder behavior in mind.
3. Treat the larger model footprint as a VRAM-sensitive run.

## Handoff from checkpoint-tools

After extraction or compression, use the layout checker and then route to inference. The layout checker is the fastest way to catch a compressed/uncompressed mismatch before a long generation run.

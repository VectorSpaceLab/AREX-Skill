# Evaluation Workflows

## OpenFlamingo EvalModel contract

The evaluation wrapper expects these methods:

- `get_outputs(batch_text, batch_images, min_generation_length, max_generation_length, num_beams, length_penalty)`
- `get_rank_classifications(batch_text, batch_images, all_class_names, use_cache, normalize_length)`

Prompt templates used by the OpenFlamingo evaluation wrapper:

- VQA question: `<image>Question:{question} Short answer:{answer}`
- VQA generation: `<image>Question:{question} Short answer:`
- Caption training/eval prompt: `<image>Output:{caption}`
- ImageNet prompt: `<image>Output:{label}`
- Hateful Memes prompt: `<image>is an image with: '{text}' written on it. Is it hateful? Answer:{label}`

When an answer or label is present, the prompt closes with `<|endofchunk|>`.

## Few-shot evaluation

1. Pick the dataset selector flags and the matching path bundle.
2. Set `--shots`, `--num_trials`, and `--trial_seeds` together.
3. Set `--num_samples` for a smaller test subset if needed.
4. Set `--query_set_size` when using random demonstrations.
5. Use `--rices` when you want retrieval-based exemplar selection.

Important detail: OpenFlamingo treats `0` shots as two text-only in-context shots through `compute_effective_num_shots`, so zero-shot commands are not literally empty-context commands.

## Captioning path

- Use `--eval_coco` or `--eval_flickr30`.
- Generation goes through `get_outputs`.
- Output postprocessing removes trailing prompt text before CIDEr scoring.
- Metric: CIDEr, returned as `CIDEr * 100`.

## VQA path

- Use `--eval_vqav2`, `--eval_ok_vqa`, `--eval_textvqa`, or `--eval_vizwiz`.
- Generation goes through `get_outputs`.
- VQA answers are postprocessed with the dataset-specific normalizer before scoring.
- Metric: VQA accuracy.
- If local annotations are missing for VQAv2 or VizWiz submission-style runs, the fill workflow pads the JSON to the full question set.

## Classification path

- Use `--eval_imagenet` or `--eval_hateful_memes`.
- Classification uses `get_rank_classifications` and class-name logprobs.
- `--classification_prompt_ensembling` averages up to 6 permutations of the in-context examples.
- `--no_caching_for_classification` disables KV caching inside the classification scorer.
- Metric: top-1 accuracy for ImageNet, ROC AUC for Hateful Memes.

## RICES workflow

1. Run the cache script once for each dataset family you want to support.
2. Save the resulting feature pickle files in a dedicated directory.
3. Pass that directory back through `--cached_demonstration_features`.
4. Set `--rices_vision_encoder_path` and `--rices_vision_encoder_pretrained` to the same CLIP backbone used during caching unless you have a specific reason to change it.

Expected cache filenames:

- `coco.pkl`
- `flickr30.pkl`
- `vqav2.pkl`
- `ok_vqa.pkl`
- `vizwiz.pkl`
- `textvqa.pkl`
- `imagenet.pkl`
- `hateful_memes.pkl`

If `--cached_demonstration_features` is omitted, RICES recomputes features on the fly.

## Results and submission files

- `--results_file` stores a JSON summary of the datasets that were evaluated.
- The summary is written only by rank 0.
- Each dataset entry stores `shots`, `trials`, `mean`, and `stddev`.
- Captioning and VQA scoring functions create temporary per-run JSON files and remove them after scoring.
- VQAv2 and VizWiz test-dev style runs create a final submission JSON whose name includes the LM name, shot count, retrieval mode, and seed.

Example summary shape:

```json
{
  "coco": [
    {"shots": 4, "trials": [60.1], "mean": 60.1, "stddev": 0.0}
  ],
  "vqav2": [
    {"shots": 4, "trials": [42.7], "mean": 42.7, "stddev": 0.0}
  ]
}
```

## Precision and distributed launch

- Prefer `--precision amp_bf16` for the common eval path.
- `amp` uses standard autocast.
- `amp_bf16` and `amp_bfloat16` use bfloat16 autocast.
- `bf16` and `fp16` change the tensor cast dtype.
- Use `torchrun` or set `MASTER_ADDR` and `MASTER_PORT` before launching a DDP run.
- `--dist-backend` defaults to `nccl` and `--no-set-device-rank` is useful when device pinning is already handled externally.

## Practical command shape

Use the bundled command builder when you want a validated command line without hand-assembling all flags. It prints commands targeting this sub-skill's wrappers:

```bash
python scripts/build_eval_command.py evaluate ...
python scripts/build_eval_command.py cache-rices ...
```

The wrappers locate the installed OpenFlamingo package and fix the evaluation import path before handing arguments to the packaged evaluation or RICES-cache entrypoint.

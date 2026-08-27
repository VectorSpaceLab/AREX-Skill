# Multimodal Generation Troubleshooting

Use this reference when a UniLM multimodal workflow fails during planning, setup, input validation, or a native run. Prefer targeted fixes and isolated environments because the umbrella repo spans incompatible fairseq, diffusers, CUDA, FlashAttention, xformers, and legacy Torch stacks.

## Fast Triage

| Symptom | Likely cause | Narrow fix path | Avoid |
|---|---|---|---|
| `No module named fairseq` | Kosmos, Kosmos-2.5, SpeechT5, or SpeechLM native stack missing fairseq/forked fairseq | Use the subproject's documented environment and user-dir; verify `fairseq-generate` or fairseq imports before running | Installing latest fairseq into an old fork-dependent stack without testing |
| `No module named kosmos2_5` or task setup fails | Kosmos-2.5 forked packages/user modules not installed | Recreate the Kosmos-2.5 requirements stack in an isolated environment; include forked fairseq/infinibatch/torchscale/transformers packages | Running Kosmos-2.5 from a generic Transformers env |
| FlashAttention or xformers build/import error | Torch/CUDA/GPU architecture mismatch | Check GPU family, CUDA, Torch, Python, and package version; disable xformers only if the script supports a fallback | Blindly upgrading Torch or CUDA in a shared environment |
| CUDA OOM during diffusion generation | `vis_num`, resolution, sample steps, full checkpoint, or xformers disabled exceed memory | Lower `--vis_num`, reduce resolution/sample steps, use LoRA or fp16, enable compatible xformers, or use a larger GPU | Retrying with the same batch and clearing no outputs |
| Hugging Face download/auth error | Model/dataset requires network, cache, or credentials | Ask for network approval, pre-download assets, set an approved cache, or switch to local paths | Embedding tokens or private cache paths in skill content |
| `checkpoint does not exist` or unexpected key errors | Wrong checkpoint path, checkpoint family, or model size | Verify file/directory exists and aligns with Kosmos/TextDiffuser/WavLM/BEATs/SpeechT5/LatentLM family | Reusing a checkpoint from a sibling model family |
| Output directory unexpectedly mutated | Native script writes generated images, cached latents, results, or demo assets in fixed locations | Use a scratch output/checkpoint copy; inspect native defaults before running | Running FID or demos in a valuable checkpoint directory |

## Kosmos-2 And Kosmos-2.5

| Symptom | Likely cause | Fix |
|---|---|---|
| Kosmos-2 `generate.py` only shows fairseq errors | The script delegates directly to `fairseq_cli.generate.cli_main` | Diagnose as a fairseq generation command: check data root, task/user-dir, dictionary, checkpoint, split, and generation flags |
| `A task must be selected` in Kosmos-2.5 | Both `--do_ocr` and `--do_md` were missing or both were passed | Select exactly one native mode: OCR or markdown |
| Image assertion fails | `--image` missing, typoed, or unreadable | Validate local image with the bundled checker; use PNG/JPEG/WebP/BMP/TIFF and avoid remote URLs |
| Checkpoint assertion message mentions image | Source code has a typo but `--ckpt` is still required | Validate the checkpoint file separately before running |
| `AutoProcessor.from_pretrained("google/pix2struct-large")` fails | Hugging Face network/cache unavailable | Pre-download processor files or approve network access; document cache path privately only in run notes |
| FlashAttention2 error on older GPU | Kosmos-2.5 requires Ampere/Ada/Hopper class support for its documented stack | Move to compatible hardware or build a non-FlashAttention adaptation outside the standard workflow |
| OCR boxes misaligned after resizing | Aspect-ratio preprocessing or output scaling does not match original image | Record raw image width/height; verify `--hw_ratio_adj_*` spans; use `draw_bbox.py` only with matching OCR JSON and original image |
| Markdown/OCR hallucinated or omitted critical text | Kosmos-2.5 README warns generative OCR may hallucinate | Cross-check critical fields against the image or a deterministic OCR system; do not treat output as guaranteed ground truth |

## TextDiffuser And TextDiffuser-2

| Symptom | Likely cause | Fix |
|---|---|---|
| Text in prompt is not rendered | v1 prompt missing quoted target text or layout planner missed text | For v1, enclose rendered words in single quotes; for v2, verify layout planner output and prompt length |
| `--mode` parser error in v1 | Mode not one of `text-to-image`, `text-to-image-with-template`, `text-inpainting` | Use the exact mode string and required image/mask inputs for template/inpainting |
| Template or mask path error | Required image input missing for selected mode | Validate `--template_image`, `--original_image`, and `--text_mask` locally before running |
| `Arial.ttf` or font error | Layout visualization font missing | Provide a local `.ttf` via `--font_path`; do not assume repo assets exist in a packaged skill |
| xformers import or attention processor failure | xformers version incompatible with Torch/CUDA | Remove the xformers flag for a slower run if supported, or install a matching xformers build in an isolated env |
| v2 full checkpoint loaded into LoRA script or reverse | Wrong inference script/checkpoint variant | Use `inference_textdiffuser2_t2i_full.py` with full checkpoint and `inference_textdiffuser2_t2i_lora.py` with LoRA checkpoint |
| `coord_mode` or tokenizer token shape mismatch | Layout coordinate settings differ from checkpoint expectations | Match README examples: `--granularity=128`, `--coord_mode=ltrb`, and `--max_length=77` for released general checkpoints |
| Inpainting demo downloads files or launches UI unexpectedly | `demo_textdiffuser2_inpainting_full.py` has side effects and Gradio UI behavior | Treat it as reference-only; ask before downloads/UI launch and prefer a scripted adaptation in a scratch checkout |
| MARIO-Eval metrics fail | Evaluation assets/OCR dependencies missing or remote API unavailable | Separate generation sampling from OCR metric computation; confirm evaluation files and any credentialed services first |

## Audio And Speech

| Symptom | Likely cause | Fix |
|---|---|---|
| Features look wrong but code runs | Audio not mono 16 kHz or normalization missed | Resample to 16 kHz mono; apply WavLM/SpeechLM normalization only when checkpoint config says so |
| WavLM/BEATs key errors | Checkpoint missing `cfg` or `model`, or using wrong checkpoint type | Inspect checkpoint keys safely with CPU `torch.load(..., map_location="cpu")`; choose tokenizer vs model vs fine-tuned classifier path correctly |
| BEATs classification has no labels | Checkpoint lacks `label_dict` | Use a fine-tuned AudioSet classifier checkpoint for top-k labels; pretrained checkpoints only provide features |
| SpeechT5 `--path required for generation` | Missing checkpoint path in `generate_speech.py` or fairseq generation | Provide `--path <CHECKPOINT_PATH>` and verify file exists |
| SpeechT5 generation fails with batch > 1 | TTS/VC generation supports batch size 1 only in evidence | Set `--batch-size 1` and reduce max tokens if memory is tight |
| fairseq manifest loading fails | Data root lacks expected `.tsv`, labels, dictionaries, BPE, or subset names | Validate data root contents, `--gen-subset`, `--hubert-label-dir`, `--bpe-tokenizer`, and dictionaries before running |
| SpeechLM KenLM/fairseq-LM decoding fails | External LM/lexicon assets absent or wrong casing | Put language model, vocabulary, and lexicon files in the expected data subdirectories; capitalize dictionary when required by source notes |
| VALL-E local script missing | UniLM VALL-E directory has only notes/demo link | Do not fabricate a native command; ask for an implementation or treat as paper-level planning |

## LatentLM

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not find model checkpoint` | Checkpoint dir lacks `model.safetensors` and DeepSpeed `pytorch_model/mp_rank_00_model_states.pt` | Point `--checkpoint` at a real LatentLM checkpoint directory or export weights into a supported layout |
| `other_state.pth` missing | Sampling/evaluation expects scaling/bias/EMA metadata | Use a checkpoint saved by `train_hf.py` or disable EMA only if the script path permits it |
| EMA loading fails | `--use_ema` passed without EMA shadow params | Remove `--use_ema` or use a checkpoint with `other_state['ema']['shadow_params']` |
| ImageFolder has zero classes | `--train_data_dir` is not class-subdirectory layout | Restructure as `root/class_name/*.jpg` or use a Hugging Face dataset name |
| FID `.npz` error | Missing or incompatible reference stat file | Provide a local `.npz` matching target distribution/resolution; do not use unrelated FID stats for claims |
| Evaluation changes checkpoint directory | Script caches latents and writes result/images files under checkpoint | Run on a copy or pre-approved scratch checkpoint directory |
| `evaluate_fid_gpt2.py` requested | File was not present in inspected source evidence | Use `evaluate_fid.py` or ask the user for the missing script/evidence |

## Command Construction Mistakes

| Mistake | Signal | Correction |
|---|---|---|
| Running packaged skill paths as native source paths | `No such file` or missing model modules | Run native commands in a user-provided UniLM working checkout; this skill only bundles references and validation helpers |
| Mixing document OCR routes | LayoutLM/TrOCR questions end up in Kosmos-2.5 plan | Use Kosmos-2.5 only when specifically requested; otherwise route document AI/OCR families to `vision-document-ai` |
| Passing remote image URL to local scripts | Path assertions fail | Download explicitly with approval, then pass a local path |
| Using training defaults for smoke tests | Huge distributed jobs start | Reduce GPUs/batch/epochs only where native script supports it, or run validation without launching training |
| Leaving placeholder paths in commands | Immediate file-not-found errors | Replace every placeholder with a verified local path before execution |
| Enabling optional acceleration by default | Import/build failures | Treat xformers, FlashAttention, Apex, and Deepspeed as opt-in after compatibility checks |

## Native Script Status

- Safe bundled helper: `scripts/check_multimodal_inputs.py` validates local arguments and prints checklists only.
- Reference-only: Kosmos/Kosmos-2.5 inference/evaluation, TextDiffuser inference/training/eval, audio/speech fairseq scripts, VALL-E notes, and LatentLM scripts because they depend on heavy runtime stacks, checkpoints, datasets, downloads, GPUs, or side effects.
- Missing evidence: `LatentLM/evaluate_fid_gpt2.py` was not present in the inspected checkout; do not cite or require it.

## Safe Escalation Pattern

1. Capture the exact native command, selected family, current working directory, environment name privately, Python/Torch/CUDA versions, GPU model, and first project stack frame.
2. Classify the failure as input path, checkpoint layout, data schema, optional dependency, compiled extension, remote download/auth, GPU memory, or command misuse.
3. Apply the smallest fix: correct a path, add a required flag, align checkpoint/script variant, lower memory settings, or use a matching isolated environment.
4. Re-run the bundled checker or a native `--help`/single-sample validation before attempting the full job.
5. Ask before installing heavy packages, downloading assets, launching distributed jobs, using credentials, or mutating checkpoint/output directories.

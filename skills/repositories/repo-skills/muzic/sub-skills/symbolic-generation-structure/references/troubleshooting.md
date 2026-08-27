# Troubleshooting

This page collects the common failures that show up across GETMusic, MuseCoco, Museformer, MeloForm, and EmoGen.

## Fast triage order

1. Check that the requested route belongs to this sub-skill and not a lyric or retrieval family.
2. Check the required artifact set: checkpoint, data bin, token dictionary, or stage-1 output.
3. Check whether the script is interactive and waiting for prompt input.
4. Check the backend requirement: CUDA, Triton, Fairseq, Java, jSymbolic, or the right old package stack.
5. Only then change model code or regenerate data.

## GETMusic problems

| Symptom | Likely cause | Fix |
|---|---|---|
| The prompt accepts no valid track letters | track letters were typed outside the supported set | use only the documented track letters, then rerun the request |
| Generation skips the song | no content track was selected | choose at least one content track |
| Conditioned output behaves strangely when every track is selected | the script falls back to an unconditional branch when all tracks are marked condition | remove one or more condition tracks |
| Output quality is poor on non-pop MIDI | domain gap between the input MIDI and the training distribution | use a more in-domain example or make the conditioning track resemble the training role |
| The training config does not load | `vocab_path`, `vocab_size`, or `tracks_start` / `tracks_end` no longer match the generated dictionary | rebuild the vocabulary, then update the config values to match the new dictionary |
| Chord guidance looks wrong | chord guidance is inferred from the input MIDI rather than typed manually | seed the run with a MIDI that already contains the intended harmonic pattern |

## MuseCoco problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Stage 2 cannot run from the stage-1 output | `infer_test.bin` was not copied into the stage-2 input folder | copy the binary bundle into `2-attribute2music_model/data/infer_input/` before inference |
| The attribute bundle has the wrong shape | `stage2_pre.py` did not see the expected `predict_attributes.json`, `softmax_probs.json`, or `att_key.json` | rerun stage 1 prediction and then rerun the stage-1 postprocessor |
| Evaluation output file name looks inconsistent | the code writes `acc_result.json` while the README text mentions `acc_results.json` | trust the script output name and use the generated file name when scripting follow-up checks |
| Text-to-attribute training fails on dependency mismatch | the repo uses an older Transformers stack and old tokenization dependencies | keep the stage-1 environment separate from other old Torch / Fairseq stacks |
| Attribute-to-music training fails to binarize | the packed `RID.bin` / `TOKEN.bin` files were not moved into the stage-2 data folder | move the packed files first, then rerun the split and binarization steps |
| Subjective attributes remain blank | the extraction script leaves artist, genre, and emotion placeholders for manual fill-in | edit the stage-2 extraction script or provide those values in your own wrapper |

## Museformer problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Token generation cannot be decoded back to MIDI | the extraction log does not match the expected `D-<id>` pattern | rerun generation with the published log format, then extract tokens again |
| `fairseq-train` fails immediately | the old Fairseq / Triton stack is missing or incompatible | verify the old environment before blaming the model code |
| The model runs only on one batch item | this recipe expects batch size 1 per GPU | keep batch size 1 and use `update-freq` for the effective batch size |
| General-use data fails on uncommon time signatures or instruments | the default dictionary is the 6-track / 4/4 recipe | switch to the general-use dictionary and the general-use encoding settings |
| MIDI decoding fails after log extraction | the token files were not written with the expected encoding method | decode with the same encoding method used to build the tokens, usually `REMIGEN2` |

## MeloForm problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Refinement cannot find the phrase template | `template.json` is missing from the expert-system directory | ensure the expert-system export was copied before running `process_es.py` |
| Refinement writes no phrase output | the song id or phrase id does not match the template structure | check the `phrase structure` in the template before choosing the phrase ids |
| Fairseq training fails on the MeloForm task | the custom user-dir or criterion is missing | keep the MeloForm user directory and criterion together |
| Porting the refinement scripts to another OS breaks paths | the source scripts assume the original repository layout and phrase export structure | use the generated runtime helper notes instead of copying the raw source scripts unchanged |

## EmoGen problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Feature extraction fails | Java or jSymbolic is missing | install Java and place `jSymbolic_2_2_user` in the expected library folder |
| The emotion generator cannot load its commands | `data/infer_input/inference_command.npy` is missing or the wrong shape | rebuild the dataset commands and confirm the four quadrant command vectors exist |
| Training fails on the control model | the linear-decoder / Fairseq stack is incomplete | verify the dataset and old Fairseq dependencies before rerunning |
| Inference returns no music | the target emotion index is missing or outside 1-4 | pass a valid quadrant number |

## Safety notes

- Keep GPU, Triton, Java, and jSymbolic workflows optional unless the task explicitly asks for them.
- Keep checkpoints and external datasets out of the runtime skill tree; document where they should go instead.
- Use the bundled helper scripts for validation before any long-running generation job.

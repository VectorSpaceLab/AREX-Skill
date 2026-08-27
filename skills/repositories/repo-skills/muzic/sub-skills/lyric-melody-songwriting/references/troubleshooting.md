# Cross-cutting troubleshooting

This page collects the most common failures shared by DeepRapper, SongMASS, TeleMelody, ReLyMe, and ROC.

| Symptom | Likely cause | Suggested fix | Affected workflows |
|---|---|---|---|
| `ModuleNotFoundError` for fairseq, MASS, or old Transformer packages | The runtime uses the wrong Python environment or the old-stack dependencies were not installed | Switch to the workflow's expected environment and keep the old-stack dependencies isolated | SongMASS, TeleMelody, ReLyMe, ROC |
| Checkpoint load fails or the model prints an empty generation | The checkpoint path and the command flags do not match the saved model family | Point at the exact checkpoint directory and reuse the flags that were used during training | DeepRapper, SongMASS, TeleMelody, ROC |
| Output quality collapses after toggling a control flag | The inference flags differ from the training flags | Reuse the same control family: reverse vs non-reverse, beat-aware vs beat-free, and the same tokenizer family | DeepRapper, TeleMelody |
| `fairseq-preprocess` or `fairseq-generate` cannot find dictionaries | `data-bin`, `checkpoints`, or `--user-dir` point at mismatched prefixes | Make the model prefix, dictionary prefix, and checkpoint prefix identical | SongMASS, TeleMelody |
| Chinese TeleMelody MIDI export breaks | The local `miditoolkit` package was not patched for the Chinese lyric path | Apply the parser patch before running the Chinese inference branch | TeleMelody, ReLyMe via TeleMelody |
| ReLyMe output looks unchanged from the baseline | The copied TeleMelody config still uses `GEN_MODE = "BASE"` | Switch the copied config to `GEN_MODE = "ReLyMe"` and use the patched fairseq helpers | ReLyMe |
| ReLyMe score module fails while creating temporary files | The current directory is not writable | Run the score code in a writable workspace so `strct_temp/` can be created | ReLyMe |
| ROC says the language tag is invalid | The first token on a chord line is not `zh` or `en` | Prefix each chord line with the correct language tag | ROC |
| ROC lyric and chord lines drift out of sync | The files were edited independently | Keep one lyric line paired with one chord line for every song | ROC |
| ROC retrieval returns poor or repetitive melodies | The database is too small or too sparse | Regenerate the database with more pieces and verify the LM checkpoint | ROC |
| DeepRapper sampling degenerates into repeated fragments | The checkpoint, reverse flag, or rhyme controls are inconsistent | Recheck `--reverse`, `--pattern`, `--dynamic_rhyme`, and the tokenizer family | DeepRapper |
| SongMASS evaluation numbers look impossible | The hypothesis and ground-truth files were mixed up | Verify the fairseq output files and the song-id alignment before scoring | SongMASS |

## Workflow-specific reminders

- DeepRapper training writes `final_model` under a path derived from `root_path`, `raw_data_dir`, and `model_sign`; the generator must point at that directory, not the raw training folder.
- SongMASS inference expects the same prefix in both the checkpoint path and the `data-bin` directory.
- TeleMelody English inference needs `syllable.txt`; Chinese inference does not, but both need the chord file.
- ROC inference is sensitive to the `lyrics.txt`/`chord.txt` line count and the language prefix.
- ReLyMe's SongMASS branch is available in code, but the top-level README does not fully document it; treat it as a code-verified path with extra manual care.

## Safe helper-script policy

The bundled scripts in this sub-skill only print plans, validate layouts, or write starter templates. They do not train models, download checkpoints, or modify source repositories.

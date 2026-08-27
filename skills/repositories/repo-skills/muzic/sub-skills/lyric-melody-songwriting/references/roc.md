# ROC reference

ROC (Re-creation of Creations) is the retrieval-driven lyric-to-melody system in this subtree. It combines a melody language model, a melody database, lyric/chord input files, and objective retrieval heuristics.

## Required runtime assets

| Asset | Expected layout | Purpose |
|---|---|---|
| Melody LM checkpoint | `music-ckps/` | Stores the trained melody language model |
| Melody database | `database/ROC.db` | SQLite database used during retrieval and selection |
| Lyric input | `lyrics.txt` | One line per song |
| Chord input | `chord.txt` | One line per song, aligned to `lyrics.txt` |

## Inference rules

| Rule | Meaning |
|---|---|
| One lyric line per song | Each line in `lyrics.txt` is treated as one generation request |
| One chord line per song | The corresponding line in `chord.txt` must describe the chord progression for that lyric line |
| Language prefix | Each chord line starts with `zh` or `en` |
| No trailing spaces | The README explicitly warns not to leave spaces at the end of lines |
| Line count match | `lyrics.txt` and `chord.txt` must have the same number of lines |

### Lyric format
- Chinese examples are space-separated sentence or phrase chunks.
- English examples use `[sep]` between lyric sentences.
- ROC's parser branches on the language prefix in `chord.txt`, so the lyric format should match the chosen language branch.

### Command outline

```bash
python lyrics_to_melody.py \
  --lyrics_path lyrics.txt \
  --chord_path chord.txt \
  --db_path database/ROC.db \
  --debug \
  --sentiment
```

- `--debug` prints composition details.
- `--sentiment` optionally infers tonality from lyric sentiment instead of defaulting to major.

## Melody language-model training

| Step | Command family | Inputs | Outputs |
|---|---|---|---|
| Prepare LMD MIDI | dataset download/extraction | `lmd_matched` | Raw MIDI dataset |
| Convert to note strings | `gen.py` | LMD dataset root and output directory | `lib-maj.notes` and `lib-min.notes` |
| Train the LM | `meldoy_lm.sh` wrapper | Melody note strings | `music-ckps/` checkpoint |

The melody LM wrapper name is spelled `meldoy_lm.sh` in the repository. Treat that as the canonical launcher name when reproducing the documented flow.

## Database construction

| Step | Script | Output |
|---|---|---|
| Format correction | `utils/format_correct.py` | `maj.notes` and `min.notes` |
| Generate short pieces | `utils/lm_generate_piece.py` | `maj_chorus.notes`, `maj_verse.notes`, `min_chorus.notes`, `min_verse.notes` |
| Store in SQLite | `utils/piece_to_database.py` | `database/ROC.db` |

Supporting utilities:
- `utils/find_chorus.py` finds repeating chorus-like segments.
- `utils/lyrics_match.py` detects repeated lyric structure and chorus boundaries.
- `utils/magenta_chord_recognition.py` infers chords for database pieces.

### Database expectations
- `piece_to_database.py` creates the `MELOLIB` table when the database does not exist.
- The table stores melody length, chords, tonality, chorus flag, and note strings.
- `lyrics_to_melody.py` queries `MELOLIB` by length, chorus flag, and tonality before reranking candidates.

## Input template guide

Use the bundled template script to create starter `lyrics.txt` and `chord.txt` files.

| Language | Example lyric placeholder | Example chord line |
|---|---|---|
| Chinese | `中文歌词第一句 中文歌词第二句` | `zh C: G: A:m F:` |
| English | `english lyric sentence one [sep] english lyric sentence two` | `en A:m F: C: G:` |

The first token on each chord line must be the language tag. The remaining chord tokens should follow the ROC chord style used by the retrieval code.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Database connected` never appears or `ROC.db` is missing | The database directory was not created or the database was not built | Create `database/` and build the SQLite database before running inference |
| Melody LM load fails | `music-ckps/` is absent or the checkpoint files are missing | Train or restore the melody language model into `music-ckps/` |
| `assert lang in ['zh', 'en']` fails | The chord file does not start each line with a valid language tag | Prefix every chord line with `zh` or `en` |
| Lyric and chord line counts do not match | Template files were edited independently | Keep both files aligned line-for-line |
| Generated piece ranking returns nothing useful | The database is sparse or the retrieval filters are too strict | Rebuild the database or widen the candidate pool |
| Sentiment mode behaves unexpectedly | Lyrics language and sentiment analyzer do not match | Leave `--sentiment` off unless you want the tonality heuristic |
| Melody generation seems stuck on one pattern | The database contains too few contrasting candidates | Expand the training corpus or regenerate database pieces |

## Notes for future agents
- ROC is retrieval-driven; `music-ckps/` and `database/ROC.db` are the two critical external assets.
- The helper script in this subtree only writes starter input files and does not build checkpoints or databases.
- Keep the `lyrics.txt` and `chord.txt` files in the same working directory as the ROC command unless you pass explicit paths.

# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Back translation returns nothing | No translation APIs were configured or the live APIs failed | Configure real API wrappers and verify network / credentials first.
| Back translation is slow | The wrapper uses multiprocessing and calls several APIs | Reduce the API list or keep it out of tight loops.
| `HomophoneSubstitution` is empty or unstable | The packaged word-frequency / pinyin data did not yield a valid candidate | Lower `homo_ratio`, keep the input text longer, or accept that tiny inputs may not augment.
| `RandomAddDelete` corrupts important tokens | The augmenter is intentionally noisy | Disable it for text that contains critical time, money, or entity spans.
| `ReplaceEntity` offsets look wrong | Offsets must shift when the replacement length changes | Keep entity spans sorted and use the returned adjusted entity list.
| `SwapCharPosition` barely changes the text | The input has too few Chinese spans or the swap ratio is too low | Raise `swap_ratio` slightly or provide longer Chinese text.

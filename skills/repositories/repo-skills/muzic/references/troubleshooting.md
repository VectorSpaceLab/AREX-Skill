# Muzic Cross-Cutting Troubleshooting

Use this before changing model code. Most Muzic failures are missing assets, wrong dependency family, stale old-framework pins, unexpected working directory, or unverified backend assumptions.

## Quick diagnosis order

1. Identify the subproject from [project-map.md](project-map.md).
2. Confirm the dependency family in [setup-and-environments.md](setup-and-environments.md).
3. Check whether the command needs external data, checkpoints, databases, Java, system audio tools, network downloads, or credentials.
4. Run the nearest bundled validator/planner if one exists.
5. Only then run the original model command in a prepared workspace.

## Common symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: fairseq`, `ImportError` from old Fairseq modules, or user-dir task not found | Running MusicBERT/SongMASS/TeleMelody/MeloForm/Museformer in a modern or incomplete environment | Use a dedicated old-stack environment and include the project's user module path as documented by its sub-skill. Do not install modern Fairseq into an unrelated environment without checking compatibility. |
| Torch/CUDA wheel installs but CUDA is unavailable | CPU-only wheel, driver/wheel mismatch, no container GPU passthrough, or unsupported old CUDA pin | Probe `nvidia-smi`, check `torch.version.cuda`, and run a tiny CUDA allocation before full generation/training. If CUDA is optional for planning, stop at validation. |
| First CLaMP run hangs or downloads unexpectedly | Hugging Face checkpoint is not cached | Ask before network download; use the CLaMP validator to ensure query/key inputs are correct before model load. |
| MusicBERT preprocessing prompts for paths or creates empty output | Missing LMD zip, wrong PiRhDy/TOPMAGD/MASD layout, or wrong output prefix | Follow the MusicBERT reference's dataset section; ensure zip/file lists exist before binarization. |
| PDAugment produces no augmented files | Missing alignment/phoneme metadata, wrong MIDI preprocessing output, wrong positional argument order, or output dirs not writable | Use `validate_pdaugment_layout.py`; verify metadata columns, WAV files, MIDI directory, frequency JSON, and thread count. |
| DeepRapper generation cannot find tokenizer/config/model files | Pretrained zip not unpacked into expected model/tokenization layout or wrong `--model_dir`/`--model_config` | Use `plan_deeprapper_command.py` to build a command and inspect all paths before generation. |
| SongMASS or TeleMelody inference cannot find dictionaries/data-bin/checkpoints | Prefixes are wrong or checkpoint/dictionary files are missing | Use `check_songmass_telemelody_assets.py`; ensure model, data, user-dir, dictionary, and output prefixes match the command. |
| ReLyMe instructions require editing installed Fairseq files | ReLyMe README integration path is invasive and environment-specific | Warn the user before mutating site-packages. Prefer non-invasive scoring/reranking planning unless the user explicitly accepts the ReLyMe integration changes. |
| ROC inference errors on database or chord/lyrics | Missing `ROC.db`, missing melody-LM checkpoint, malformed chord/lyrics lines | Use `make_roc_input_template.py`; verify database/checkpoint placement before running inference. |
| GETMusic asks confusing interactive questions or emits invalid tracks | Invalid track letters, condition/content overlap, malformed position grammar, or input MIDI track mismatch | Use `validate_getmusic_request.py`; confirm track letters (`l`, `b`, `d`, `g`, `p`, `s`, `c`) and position ranges. |
| MuseCoco stage 2 cannot find `infer_test.bin` | Stage-1 predicted attributes were not converted with `stage2_pre.py` or file was not copied to the stage-2 input directory | Use `plan_musecoco_pipeline.py` and confirm all stage artifacts. |
| Museformer generation outputs token logs but no MIDI | Log extraction/generation conversion step skipped or MidiProcessor dependency missing | Follow the structure generation reference: extract token sequences, then run batch MIDI generation with the selected encoding method. |
| EmoGen feature extraction fails | Java or jSymbolic zip is missing/misplaced | Install Java and place the jSymbolic package as described by the EmoGen reference before running feature extraction. |
| MusicAgent starts but no tool handles the request | Tool is disabled, model assets are missing, credentials absent, or the plugin mapping lacks that task | Validate `config.yaml`, check `disabled_tools`, model folders, API keys, and the tool map. |

## Privacy and safety

- Never paste API keys, `.env` contents, OAuth credentials, or private dataset paths into generated guidance.
- Do not run download scripts or install system packages without user approval.
- Do not run long training, benchmark, or corpus preprocessing commands unless the user has confirmed data, budget, output location, and backend.
- Keep model checkpoints and datasets out of this skill tree; they are user-provided runtime assets.

# Setup and Environment Strategy

Muzic is a research monorepo with multiple unrelated dependency families. Do not create one broad environment unless the user explicitly wants to reproduce the full repository and accepts resolver conflicts, old CUDA pins, and long installs.

## General rules

1. Identify the target subproject first; use [project-map.md](project-map.md) and the owning sub-skill.
2. Prefer a fresh private environment per dependency family or per paper workflow.
3. Treat root `requirements.txt` as a historical aggregate, not a universal install command.
4. Install only the requirements needed for the selected workflow.
5. Confirm checkpoints, datasets, and system packages before running scripts.
6. Keep credentials out of command history, committed configs, and generated files.

## Dependency families

| Family | Projects | Evidence-backed install direction | Notes |
|---|---|---|---|
| Root historical stack | MusicBERT, SongMASS, TeleMelody, ReLyMe, ROC, MeloForm, PDAugment pieces | Python 3.6-era packages from root `requirements.txt` only when reproducing these older workflows | Pins include `fairseq==0.10.0`, `torch==1.7.1`, old `transformers`, `scipy`, `tensorboard`; this can conflict with modern Python. |
| CLaMP | CLaMP retrieval/classification | `clamp/requirements.txt` with `transformers==4.18.0`, Torch/TorchVision CUDA 11.1 wheels | First model run downloads Hugging Face checkpoints unless cached. CPU may work slowly for small retrieval checks. |
| GETMusic | any-track generation and preprocessing | README lists Torch 1.12.1+cu113, TensorBoard, PyYAML, tqdm, Transformers, einops, miditoolkit, scipy | Generation and training are checkpoint/CUDA dependent; preprocessing can be CPU but still writes data. |
| MuseCoco | text-to-attribute and attribute-to-music | `musecoco/requirements.txt` plus PyTorch 1.11.0 from README | Mixes Transformers/Datasets and Fairseq/MIDI packages; use a dedicated environment. |
| Museformer | long-structure modeling | Fairseq/Torch stack plus Triton installed outside the Museformer root | Training in README uses 4 GPUs and batch size 1; generation requires checkpoint. |
| EmoGen | emotion-controlled generation | Python 3.8 plus `setup.sh`, Java, jSymbolic zip | Attribute extraction depends on Java/jSymbolic; generation depends on checkpoints. |
| MusicAgent | LLM music agent | README's system packages plus `musicagent/requirements.txt`, `semantic-kernel`, NumPy/protobuf pins | Tool runs may need model downloads, API keys, audio system packages, and GPU. |

## Environment selection examples

### CLaMP retrieval planning

Use when the user has text/MusicXML inputs and wants CLaMP rankings.

```bash
# in a dedicated environment compatible with the CLaMP README
pip install -r clamp/requirements.txt
python clamp.py -clamp_model_name sander-wood/clamp-small-512 -query_modal text -key_modal music -top_n 5
```

Before the model run, validate the input layout from this skill:

```bash
python sub-skills/music-understanding-retrieval/scripts/validate_clamp_inputs.py --inference-dir inference --query-modal text --key-modal music --top-n 5
```

### GETMusic generation planning

Use a CUDA-capable environment matching the README pins and a checkpoint path. Validate the track request first:

```bash
python sub-skills/symbolic-generation-structure/scripts/validate_getmusic_request.py --condition lc --content dgp
```

Then run the original GETMusic command in an appropriate GETMusic workspace only after the checkpoint and MIDI inputs are present.

### MusicAgent startup planning

Install the README system packages and Python dependencies in a dedicated environment. Validate configuration before launch:

```bash
python sub-skills/music-agent-workflows/scripts/validate_musicagent_config.py --config config.yaml --models-dir models
python agent.py --config config.yaml
```

## Backend and artifact checks

For any full model run, record:

- Python version and dependency family.
- GPU/CPU choice and whether the model supports CPU fallback.
- Checkpoint path and expected files.
- Dataset or input file layout.
- Output directory and whether the command overwrites existing files.
- Network downloads required on first run.
- Credentials or system packages required.

If one of those fields is unknown, stop at a plan or validation step rather than launching training or inference.

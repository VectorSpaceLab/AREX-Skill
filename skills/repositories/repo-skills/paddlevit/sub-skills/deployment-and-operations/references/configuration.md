# Configuration and source-root conventions

## What is shared, what is not

PaddleViT is a shallow collection of standalone model projects. There is no
single package installation contract at the repository root. A model directory
usually has its own `config.py`, `datasets.py`, model implementation, and
`main_*` entry point. The same filename in two directories is not necessarily
the same API. Start by locating the named model directory, then inspect its
parser and `update_config` function rather than assuming the ViT example is
universal.

For scripts using imports such as `from config import get_config` or
`from beit import build_beit`, run from the corresponding project directory or
set a deliberate, temporary Python module path. Never solve an import collision
by putting several model directories on a persistent global `PYTHONPATH`.
Record:

- repository commit and model subdirectory;
- entry script and its parser;
- YAML path, including any relative `BASE` files;
- data, pretrained, resume, and output paths;
- selected `CUDA_VISIBLE_DEVICES` and requested backend.

Relative paths in repository examples are interpreted from the process working
directory. Use absolute user-owned paths for data, checkpoints, and output when
moving beyond a smoke test. Do not place generated exports inside the source
model or checkpoint directory unless explicitly intended.

## Precedence

The common yacs pattern is:

```text
config.py defaults
  -> YAML passed with -cfg (and recursively merged BASE files)
  -> explicit command-line overrides
  -> control-flow flags (-eval, -amp, -resume, -pretrained, ...)
```

`docs/paddlevit-config.md` states that YAML overrides the Python defaults and
that command-line arguments are applied after YAML, so command-line values are
the current values. In the representative ViT implementation,
`get_config()` clones defaults, `_update_config_from_file()` follows the YAML
`BASE` list relative to the YAML file, then `update_config()` applies options
such as `-dataset`, `-batch_size`, `-image_size`, `-data_path`, `-output`,
`-pretrained`, `-resume`, `-last_epoch`, `-eval`, and `-amp`.

A practical precedence table:

| Layer | Examples | Operational check |
|---|---|---|
| Python defaults | image size, dataset, save path, AMP false | Read the selected `config.py`; do not infer from another model. |
| YAML | `DATA.IMAGE_SIZE`, `MODEL.NUM_CLASSES`, optimizer/model fields | Confirm the file exists and inspect `BASE` relative to that file. |
| CLI | `-cfg`, `-data_path`, `-batch_size`, `-image_size`, `-pretrained`, `-resume`, `-eval`, `-amp` | Reconstruct the effective command; CLI wins where the parser exposes a field. |
| Environment | `CUDA_VISIBLE_DEVICES`, loader/runtime variables | Environment selects visibility/runtime; it does not replace config values. |

The old parsers commonly use truthiness checks (`if args.batch_size:`).
Therefore zero, an empty string, or another false-like value may not override a
YAML/default value. Treat this as source behavior, not as a reason to silently
rewrite the parser. Use a valid positive batch size and explicit paths, and
inspect the printed effective config. `-amp` is special in the representative
ViT config: it enables AMP only when not in evaluation mode.

Do not confuse:

- `-pretrained`: load model weights for evaluation or fine-tuning;
- `-resume`: may restore model plus optimizer, scheduler, epoch, and AMP scaler;
- `-eval`: select validation/evaluation control flow;
- `-output`: choose logs/checkpoint output, often with a timestamp appended by
  the main script;
- a static export prefix: a separate artifact namespace, not a training output
  directory or a `.pdparams` path.

## Minimal preflight record

Before a costly command, write down the intended effective values:

```text
model_dir      = image_classification/<family>
entry          = main_single_gpu.py | main_multi_gpu.py | export script
config         = <yaml and BASE chain>
data           = <absolute path or explicitly synthetic input>
checkpoint     = <pretrained/resume, or absent>
output         = <new path/prefix>
device         = cpu | gpu:<visible ordinal>
amp            = false unless approved and supported
world_size     = 1 unless distributed prerequisites are proven
```

If a value cannot be obtained from the parser/config or is ambiguous, stop and
ask rather than inventing a repository-wide default. Configuration parsing can
be checked without importing a model, but a successful parse does not prove
model shape compatibility or checkpoint compatibility.

## Safe diagnosis

1. `pwd` and list the target model directory; verify the expected `config.py`
   and entry script belong to the same family.
2. Check the YAML and every `BASE` path as regular files. Do not fetch missing
   YAMLs from the network.
3. Compare requested CLI fields with that parser. An accepted-looking option
   may be ignored if this model's parser does not define it.
4. Run the bundled environment and artifact probes. They are read-only.
5. Only then construct an approved single-process command. Preserve the
   effective config and artifact manifest in the experiment record.

## Evidence boundary

Primary evidence: `docs/paddlevit-config.md`, representative
`image_classification/ViT/config.py` and `main_multi_gpu.py`, plus the repository
source-root conventions observed across model directories. Exact field names
vary by family; route model-specific fields to that family skill.

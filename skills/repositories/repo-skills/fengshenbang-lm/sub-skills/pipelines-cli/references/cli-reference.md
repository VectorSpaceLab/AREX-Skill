# `fengshen-pipeline` CLI Reference

## Console contract

The installed package exposes one console script:

```bash
fengshen-pipeline <pipeline_name> predict|train [common args] [pipeline-specific args]
```

The console entry point performs these steps:

1. Import `fengshen.pipelines.<pipeline_name>`.
2. Read a module attribute named `Pipeline`.
3. Add common args `--model`, `--datasets`, and `--text`.
4. Call `Pipeline.add_pipeline_specific_args(parser)`.
5. Parse arguments after `<pipeline_name> predict|train`.
6. Instantiate `Pipeline(args=args, model=args.model)`.
7. For `predict`, call `pipeline(args.text)` and print the result.
8. For `train`, call `datasets.load_dataset(args.datasets)` and then `pipeline.train(datasets)`.

Only `predict` and `train` are implemented. There is no console subcommand for evaluation, export, conversion, listing available pipelines, or checkpoint inspection.

## Console route table

| Route | Console status | Main class | Notes |
|---|---|---|---|
| `text_classification` | Best supported console route | `TextClassificationPipeline` | Has `Pipeline` alias and `add_pipeline_specific_args`. `predict` follows the README command shape. `train` loads a Hugging Face dataset name from `--datasets`; use the Python route for local JSONL files. |
| `sequence_tagging` | Help/parser route; use Python for real work | `SequenceTaggingPipeline` | Has `Pipeline` alias and parser method, so help inspection is useful. The class initializer expects `model_path`, while the generic CLI passes `model`; console `train` also passes an extra dataset object to a no-argument `train()` method. Prefer programmatic use. |
| `multiplechoice` | Programmatic only | `UniMCPipelines` | Defines `pipelines_args`, not the console-required `add_pipeline_specific_args`, and has no `Pipeline` alias. |
| `information_extraction` | Programmatic only | `UniEXPipelines` | Defines `pipelines_args`, not the console-required method, and initializes from `args.pretrained_model_path`. |
| `tcbert` | Programmatic only | `TCBertPipelines` | The parser helper is misspelled as `piplines_args`; initialization needs `model_path` and `nlabels`. |
| Ubert | Programmatic only | `UbertPipelines` | Import with `from fengshen import UbertPipelines`; it lives under the model package, not `fengshen.pipelines.<name>` for the console route. |

Use [../scripts/inspect_pipeline_cli.py](../scripts/inspect_pipeline_cli.py) to inspect installed-package parser availability before relying on a route.

## Common arguments

| Argument | Used by | Meaning |
|---|---|---|
| `--model` | Console instantiation | Model id or local model directory passed to `Pipeline(..., model=args.model)`. May trigger model/config/tokenizer downloads during real prediction or training. |
| `--datasets` | Console `train` only | Dataset name passed to `datasets.load_dataset(args.datasets)`. This is convenient for public datasets such as `IDEA-CCNL/AFQMC`; it is not a full local-file `data_files` interface. |
| `--text` | Console `predict` only | Prediction input string. The README pair-classification example places `[SEP]` between two texts in this single string. |

## Text classification parser additions

`TextClassificationPipeline.add_pipeline_specific_args` adds these task flags directly:

- `--texta_name` (default `sentence`)
- `--textb_name` (default `sentence2`)
- `--label_name` (default `label`)
- `--max_length` (default `512`)
- `--device` (default `-1`, CPU)

It also adds `UniversalDataModule`, `UniversalCheckpoint`, PyTorch Lightning Trainer, and optimizer/scheduler/model utility flags. Route detailed Trainer/checkpoint/optimizer interpretation to `data-training`.

## Sequence tagging parser additions

`SequenceTaggingPipeline.add_pipeline_specific_args` adds:

- `--max_seq_length` (default `512`)
- `--data_dir` (directory containing `labels.txt` and `*.all.bmes` files)
- `--model_type` (default `bert`)
- `--decode_type` (`linear`, `crf`, `biaffine`, or `span`; default `linear`)
- `--loss_type` (default `ce`)

It also adds the same data/checkpoint/Trainer/model utility flag families. Use [sequence-tagging.md](sequence-tagging.md) for the data layout.

## Safe help checks

The intended help check is:

```bash
fengshen-pipeline text_classification predict --help
```

This should parse arguments without instantiating a model because argparse exits on `--help` after module import and parser construction. If it fails before printing help, the failure is usually an import/dependency problem, not a model download problem.

For sequence tagging, prefer:

```bash
python scripts/inspect_pipeline_cli.py --pipeline sequence_tagging
```

because that surfaces parser details and class-route caveats without suggesting the generic console command is fully safe for training.

## Programmatic parser shapes

Use these parser helpers outside the console command:

```python
import argparse
from fengshen.pipelines.multiplechoice import UniMCPipelines
from fengshen.pipelines.information_extraction import UniEXPipelines
from fengshen.pipelines.tcbert import TCBertPipelines
from fengshen import UbertPipelines

parser = argparse.ArgumentParser()
parser = UniMCPipelines.pipelines_args(parser)
parser = UniEXPipelines.pipelines_args(parser)
parser = TCBertPipelines.piplines_args(parser)   # misspelled in the package
parser = UbertPipelines.pipelines_args(parser)
```

Do not pass these classes through `fengshen-pipeline` unless the installed package has been changed to provide a compatible `Pipeline` alias and `add_pipeline_specific_args` method.

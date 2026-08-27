#!/usr/bin/env python3
"""Safe-by-default NER fine-tuning helper for public pip-installed Flair.

The --help path does not import Flair. --list-datasets uses a bundled allowlist
and does not import Flair. --dry-run prints a plan and can inspect local corpora
without constructing transformer embeddings or training.
"""

from __future__ import annotations

import argparse
import contextlib
import inspect
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


NER_DATASET_PREFIXES = ("NER", "CONLL", "WNUT")
NER_DATASET_NAMES = (
    "CONLL_03",
    "CONLL_03_DUTCH",
    "CONLL_03_GERMAN",
    "CONLL_03_SPANISH",
    "CONLL_2000",
    "WNUT_17",
    "NER_ARABIC_ANER",
    "NER_ARABIC_AQMAR",
    "NER_BASQUE",
    "NER_BAVARIAN_WIKI",
    "NER_CHINESE_WEIBO",
    "NER_DANISH_DANE",
    "NER_DANISH_DANSK",
    "NER_ESTONIAN_NOISY",
    "NER_FINNISH",
    "NER_GERMAN_BIOFID",
    "NER_GERMAN_EUROPARL",
    "NER_GERMAN_GERMEVAL",
    "NER_GERMAN_LEGAL",
    "NER_GERMAN_MOBIE",
    "NER_GERMAN_POLITICS",
    "NER_HIPE_2022",
    "NER_HUNGARIAN",
    "NER_ICDAR_EUROPEANA",
    "NER_ICELANDIC",
    "NER_JAPANESE",
    "NER_MASAKHANE",
    "NER_MULTI_CONER",
    "NER_MULTI_CONER_V2",
    "NER_MULTI_WIKIANN",
    "NER_MULTI_WIKINER",
    "NER_MULTI_XTREME",
    "NER_NERMUD",
    "NER_NOISEBENCH",
    "NER_ENGLISH_MOVIE_COMPLEX",
    "NER_ENGLISH_MOVIE_SIMPLE",
    "NER_ENGLISH_PERSON",
    "NER_ENGLISH_RESTAURANT",
    "NER_ENGLISH_SEC_FILLINGS",
    "NER_ENGLISH_STACKOVERFLOW",
    "NER_ENGLISH_TWITTER",
    "NER_ENGLISH_WEBPAGES",
    "NER_ENGLISH_WIKIGOLD",
    "NER_ENGLISH_WNUT_2020",
    "NER_SWEDISH",
    "NER_TURKU",
    "NER_UKRAINIAN",
)


def parse_json_object(text: str, *, name: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError(f"{name} must decode to a JSON object")
    return value


def parse_column_format(text: str) -> dict[int, str]:
    raw = parse_json_object(text, name="--column-format")
    parsed: dict[int, str] = {}
    for key, value in raw.items():
        try:
            parsed[int(key)] = str(value)
        except (TypeError, ValueError) as exc:
            raise argparse.ArgumentTypeError("--column-format keys must be integer-like column indexes") from exc
    if "text" not in parsed.values():
        raise argparse.ArgumentTypeError('--column-format must map one column to "text"')
    return parsed


def str_to_bool(text: str) -> bool:
    lowered = text.lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def optional_fraction(text: str) -> float:
    value = float(text)
    if not (0.0 < value <= 1.0):
        raise argparse.ArgumentTypeError("value must be in (0, 1]")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fine-tune a Flair SequenceTagger for NER from local data or an approved public Flair dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    data = parser.add_argument_group("data")
    data.add_argument("--data-folder", type=Path, help="Local folder containing split files. Optional when --train-files/--dev-files/--test-files use explicit paths.")
    data.add_argument("--dataset-name", help="Public Flair NER dataset class name, for example CONLL_03 or WNUT_17. May download when instantiated.")
    data.add_argument("--data-format", choices=["column", "jsonl"], default="column", help="Local data reader to use.")
    data.add_argument("--train-file", default="train.txt", help="Train split file name for local folder readers. Pass an empty string for None.")
    data.add_argument("--dev-file", default="dev.txt", help="Dev split file name for local folder readers. Pass an empty string for None.")
    data.add_argument("--test-file", default="test.txt", help="Test split file name for local folder readers. Pass an empty string for None.")
    data.add_argument("--train-files", nargs="+", help="Explicit train split files for MultiFileColumnCorpus or MultiFileJsonlCorpus.")
    data.add_argument("--dev-files", nargs="+", help="Explicit dev split files for MultiFileColumnCorpus or MultiFileJsonlCorpus.")
    data.add_argument("--test-files", nargs="+", help="Explicit test split files for MultiFileColumnCorpus or MultiFileJsonlCorpus.")
    data.add_argument("--column-format", type=parse_column_format, default=parse_column_format('{"0":"text","1":"ner"}'), help="JSON map from column index to Flair layer name for column data.")
    data.add_argument("--column-delimiter", default=r"\s+", help="Column delimiter regex; use '\\t' for TSV.")
    data.add_argument("--comment-symbol", default="# ", help="Column comment prefix; pass an empty string to disable.")
    data.add_argument("--no-autofind-splits", action="store_true", help="Do not let folder readers infer split file names.")
    data.add_argument("--sample-missing-splits", type=str_to_bool, default=False, help="Allow Flair to sample missing dev/test splits where supported.")
    data.add_argument("--disk", action="store_true", help="Use lower-memory disk/raw-line corpus modes where supported.")
    data.add_argument("--jsonl-text-column", default="data", help="JSONL text field name.")
    data.add_argument("--jsonl-label-column", default="label", help="JSONL label field containing [start,end,label] spans.")
    data.add_argument("--jsonl-metadata-column", default="metadata", help="JSONL metadata field name.")
    data.add_argument("--jsonl-use-tokenizer", type=str_to_bool, default=True, help="Use Flair tokenization for JSONL text.")
    data.add_argument("--dataset-args", default="{}", help="JSON object passed to the public Flair dataset constructor.")
    data.add_argument("--label-type", default="ner", help="Flair label layer to train and predict.")
    data.add_argument("--add-unk", action="store_true", help="Add <unk> to the label dictionary. Closed NER usually leaves this off.")
    data.add_argument("--downsample", type=optional_fraction, help="Optional corpus downsample percentage for smoke training or dry-run inspection.")

    model = parser.add_argument_group("model")
    model.add_argument("--model-name-or-path", default="distilbert-base-uncased", help="Transformer model ID or local path.")
    model.add_argument("--layers", default="-1", help="Transformer layers string.")
    model.add_argument("--subtoken-pooling", default="first", choices=["first", "last", "first_last", "mean"], help="Subtoken pooling strategy.")
    model.add_argument("--hidden-size", type=int, default=256, help="SequenceTagger hidden size.")
    model.add_argument("--use-crf", action="store_true", help="Enable CRF decoding.")
    model.add_argument("--use-rnn", action="store_true", help="Enable SequenceTagger RNN layer.")
    model.add_argument("--reproject-embeddings", action="store_true", help="Enable embedding reprojection.")
    model.add_argument("--context-size", type=int, default=0, help="FLERT context size; 0 disables context.")
    model.add_argument("--respect-document-boundaries", action="store_true", help="Respect document boundaries for contextual embeddings.")

    train = parser.add_argument_group("training")
    train.add_argument("--output-dir", type=Path, default=None, help="Training output directory. Required for training; choose a user-owned path.")
    train.add_argument("--epochs", type=int, default=10, help="Maximum fine-tuning epochs.")
    train.add_argument("--batch-size", type=int, default=4, help="Training mini-batch size.")
    train.add_argument("--eval-batch-size", type=int, default=16, help="Evaluation mini-batch size.")
    train.add_argument("--mini-batch-chunk-size", type=int, default=1, help="Chunk size for memory-constrained batches; set 0 for None.")
    train.add_argument("--learning-rate", type=float, default=5e-5, help="Fine-tuning learning rate.")
    train.add_argument("--warmup-fraction", type=float, default=0.1, help="Linear warmup fraction.")
    train.add_argument("--weight-decay", type=float, default=0.0, help="AdamW weight decay passed through trainer kwargs.")
    train.add_argument("--seed", type=int, default=42, help="Random seed.")
    train.add_argument("--device", default="cpu", help="Device string; CPU is the verified baseline. Ignored inside distributed workers.")
    train.add_argument("--embeddings-storage-mode", choices=["none", "cpu", "gpu"], default="none", help="Trainer embedding storage mode.")
    train.add_argument("--save-model-each-k-epochs", type=int, default=0, help="Save periodic model snapshots; 0 disables.")
    train.add_argument("--save-optimizer-state", action="store_true", help="Include optimizer state in saved models.")
    train.add_argument("--no-save-final-model", dest="save_final_model", action="store_false", default=True, help="Do not save final-model.pt.")
    train.add_argument("--no-file-logs", dest="create_file_logs", action="store_false", default=True, help="Do not write training.log.")
    train.add_argument("--no-loss-file", dest="create_loss_file", action="store_false", default=True, help="Do not write loss.tsv.")
    train.add_argument("--multi-gpu", action="store_true", help="Pass multi_gpu=True to ModelTrainer. Requires --distributed-launch and verified CUDA/2+ GPUs.")
    train.add_argument("--distributed-launch", action="store_true", help="Wrap training with flair.distributed_utils.launch_distributed. Only valid with --multi-gpu.")
    train.add_argument("--allow-downloads", action="store_true", help="Allow public dataset/model downloads if resources are not cached.")

    safe = parser.add_argument_group("safe inspection")
    safe.add_argument("--list-datasets", action="store_true", help="List public Flair NER-style dataset class names and exit.")
    safe.add_argument("--dry-run", action="store_true", help="Print plan and inspect local corpus if provided; do not build embeddings or train.")
    safe.add_argument("--report-json", action="store_true", help="Emit machine-readable JSON for list or dry-run output.")
    return parser


def import_flair(device: str, *, set_device: bool = True):
    os.environ.setdefault("FLAIR_DEVICE", device)
    import torch
    import flair

    if set_device:
        flair.device = torch.device(device)
    return flair, torch


def candidate_dataset_classes(_flair_module) -> dict[str, type]:
    import flair.datasets as datasets

    modules = [datasets]
    try:
        import flair.datasets.sequence_labeling as sequence_labeling

        modules.append(sequence_labeling)
    except Exception:
        pass

    classes: dict[str, type] = {}
    for module in modules:
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and name.startswith(NER_DATASET_PREFIXES):
                classes[name] = obj
    return dict(sorted(classes.items()))


def load_dataset_args(text: str) -> dict[str, Any]:
    return parse_json_object(text, name="--dataset-args")


def empty_to_none(text: str | None) -> str | None:
    return None if text == "" else text


def explicit_file_lists(args: argparse.Namespace) -> bool:
    return bool(args.train_files or args.dev_files or args.test_files)


def resolve_files(files: Iterable[str] | None, base: Path | None) -> list[Path] | None:
    if files is None:
        return None
    resolved: list[Path] = []
    for item in files:
        path = Path(item)
        if not path.is_absolute() and base is not None:
            path = base / path
        resolved.append(path)
    return resolved


def load_local_corpus(args: argparse.Namespace, _flair_module):
    base = args.data_folder
    if base is not None and not base.exists():
        raise SystemExit(f"local data folder does not exist: {base}")

    comment_symbol = None if args.comment_symbol == "" else args.comment_symbol

    if explicit_file_lists(args):
        train_files = resolve_files(args.train_files, base)
        dev_files = resolve_files(args.dev_files, base)
        test_files = resolve_files(args.test_files, base)
        if args.data_format == "column":
            from flair.datasets.sequence_labeling import MultiFileColumnCorpus

            return MultiFileColumnCorpus(
                column_format=args.column_format,
                train_files=train_files,
                dev_files=dev_files,
                test_files=test_files,
                column_delimiter=args.column_delimiter,
                comment_symbol=comment_symbol,
                in_memory=not args.disk,
                sample_missing_splits=args.sample_missing_splits,
            )

        try:
            from flair.datasets import MultiFileJsonlCorpus
        except ImportError:
            from flair.datasets.sequence_labeling import MultiFileJsonlCorpus

        return MultiFileJsonlCorpus(
            train_files=train_files,
            dev_files=dev_files,
            test_files=test_files,
            text_column_name=args.jsonl_text_column,
            label_column_name=args.jsonl_label_column,
            metadata_column_name=args.jsonl_metadata_column,
            label_type=args.label_type,
            use_tokenizer=args.jsonl_use_tokenizer,
            sample_missing_splits=args.sample_missing_splits,
        )

    if base is None:
        raise SystemExit("local corpus loading requires --data-folder or explicit --train-files/--dev-files/--test-files")

    train_file = empty_to_none(args.train_file)
    dev_file = empty_to_none(args.dev_file)
    test_file = empty_to_none(args.test_file)

    if args.data_format == "column":
        from flair.datasets import ColumnCorpus

        return ColumnCorpus(
            data_folder=base,
            column_format=args.column_format,
            train_file=train_file,
            dev_file=dev_file,
            test_file=test_file,
            autofind_splits=not args.no_autofind_splits,
            column_delimiter=args.column_delimiter,
            comment_symbol=comment_symbol,
            in_memory=not args.disk,
            sample_missing_splits=args.sample_missing_splits,
        )

    try:
        from flair.datasets import JsonlCorpus
    except ImportError:
        from flair.datasets.sequence_labeling import JsonlCorpus

    return JsonlCorpus(
        data_folder=base,
        train_file=train_file,
        dev_file=dev_file,
        test_file=test_file,
        text_column_name=args.jsonl_text_column,
        label_column_name=args.jsonl_label_column,
        metadata_column_name=args.jsonl_metadata_column,
        label_type=args.label_type,
        autofind_splits=not args.no_autofind_splits,
        use_tokenizer=args.jsonl_use_tokenizer,
        sample_missing_splits=args.sample_missing_splits,
    )


def load_public_dataset(args: argparse.Namespace, flair_module):
    if not args.allow_downloads:
        raise SystemExit("public Flair dataset constructors may download; pass --allow-downloads to instantiate one")
    classes = candidate_dataset_classes(flair_module)
    if args.dataset_name not in classes:
        available = ", ".join(classes) or "none found"
        raise SystemExit(f"unknown NER dataset {args.dataset_name!r}; available: {available}")
    return classes[args.dataset_name](**load_dataset_args(args.dataset_args))


def load_corpus(args: argparse.Namespace, flair_module):
    if args.dataset_name:
        return load_public_dataset(args, flair_module)
    return load_local_corpus(args, flair_module)


def maybe_downsample(corpus, args: argparse.Namespace):
    if args.downsample is None:
        return corpus
    return corpus.downsample(percentage=args.downsample, random_seed=args.seed)


def split_lengths(corpus) -> dict[str, int | None]:
    return {
        "train": len(corpus.train) if corpus.train is not None else None,
        "dev": len(corpus.dev) if corpus.dev is not None else None,
        "test": len(corpus.test) if corpus.test is not None else None,
    }


def localish_model_reference(model_name_or_path: str) -> bool:
    path = Path(model_name_or_path).expanduser()
    if path.exists() or path.is_absolute():
        return True
    if model_name_or_path.startswith(("./", "../", "~")):
        return True
    return model_name_or_path.endswith((".pt", ".bin", ".safetensors"))


def dictionary_items(label_dictionary, limit: int = 25) -> list[str]:
    if hasattr(label_dictionary, "get_items"):
        return list(label_dictionary.get_items())[:limit]
    return [str(label_dictionary.get_item_for_index(i)) for i in range(min(len(label_dictionary), limit))]


def print_payload(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print(f"{key}: {json.dumps(value, default=str)}")
        else:
            print(f"{key}: {value}")


@contextlib.contextmanager
def quiet_if(enabled: bool):
    if not enabled:
        yield
        return
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def run_list_datasets(args: argparse.Namespace) -> int:
    names = list(NER_DATASET_NAMES)
    if args.report_json:
        print(json.dumps({"datasets": names, "count": len(names)}, indent=2))
    else:
        for name in names:
            print(name)
    return 0


def run_dry_run(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "mode": "dry-run",
        "will_train": False,
        "will_build_embeddings": False,
        "output_dir": str(args.output_dir) if args.output_dir else None,
        "label_type": args.label_type,
        "model_name_or_path": args.model_name_or_path,
        "downloads_allowed": args.allow_downloads,
        "data_format": args.data_format,
        "downsample": args.downsample,
        "device": args.device,
    }

    if args.dataset_name:
        payload["dataset_name"] = args.dataset_name
        payload["dataset_known"] = args.dataset_name in NER_DATASET_NAMES
        payload["dataset_instantiated"] = False
        payload["dataset_note"] = "Dry-run does not instantiate public datasets because they may download."
    elif args.data_folder is not None or explicit_file_lists(args):
        try:
            with quiet_if(args.report_json):
                flair_module, torch = import_flair(args.device)
                corpus = maybe_downsample(load_local_corpus(args, flair_module), args)
                label_dictionary = corpus.make_label_dictionary(label_type=args.label_type, add_unk=args.add_unk)
        except ModuleNotFoundError as exc:
            payload["flair_import_error"] = str(exc)
        else:
            payload["flair_version"] = getattr(flair_module, "__version__", "unknown")
            payload["device"] = str(flair_module.device)
            payload["corpus"] = str(corpus)
            payload["splits"] = split_lengths(corpus)
            payload["label_dictionary_size"] = len(label_dictionary)
            payload["label_dictionary_items"] = dictionary_items(label_dictionary)
            payload["uses_multifile_reader"] = explicit_file_lists(args)
            payload["torch_cuda_available"] = bool(torch.cuda.is_available())
            payload["torch_cuda_device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
    else:
        payload["corpus_note"] = "No corpus selected; pass --data-folder for local inspection or --dataset-name with --allow-downloads for training."

    if "torch_cuda_available" not in payload:
        payload["torch_cuda_available"] = False
        payload["torch_cuda_device_count"] = 0
    if args.multi_gpu:
        payload["multi_gpu_note"] = "Requested in plan only; training requires --distributed-launch plus verified CUDA and at least two GPUs."

    print_payload(payload, as_json=args.report_json)
    return 0


def run_training(args: argparse.Namespace, *, distributed_worker: bool = False) -> int:
    if args.output_dir is None:
        raise SystemExit("training requires --output-dir; choose a user-owned run directory")
    output_dir = args.output_dir.expanduser()
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite_output_dir:
        raise SystemExit(f"output directory {output_dir} exists and is not empty; choose a fresh path or pass --overwrite-output-dir")
    if args.dataset_name is None and args.data_folder is None and not explicit_file_lists(args):
        raise SystemExit("training requires --data-folder, explicit split files, or --dataset-name")
    if not args.allow_downloads and not localish_model_reference(args.model_name_or_path):
        raise SystemExit("model names can download from public model hubs; pass --allow-downloads or provide an existing local model path")

    flair_module, torch = import_flair(args.device, set_device=not distributed_worker)
    if not distributed_worker and str(args.device).startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit(f"requested device {args.device!r}, but torch.cuda.is_available() is false")
    if args.embeddings_storage_mode == "gpu" and not torch.cuda.is_available():
        raise SystemExit('embeddings_storage_mode="gpu" requires verified CUDA')

    if hasattr(flair_module, "set_seed"):
        flair_module.set_seed(args.seed)
    else:
        torch.manual_seed(args.seed)

    corpus = maybe_downsample(load_corpus(args, flair_module), args)
    label_dictionary = corpus.make_label_dictionary(label_type=args.label_type, add_unk=args.add_unk)

    from flair.embeddings import TransformerWordEmbeddings
    from flair.models import SequenceTagger
    from flair.trainers import ModelTrainer

    context = args.context_size if args.context_size > 0 else False
    embeddings = TransformerWordEmbeddings(
        model=args.model_name_or_path,
        layers=args.layers,
        subtoken_pooling=args.subtoken_pooling,
        fine_tune=True,
        use_context=context,
        respect_document_boundaries=args.respect_document_boundaries,
    )
    tagger = SequenceTagger(
        embeddings=embeddings,
        tag_dictionary=label_dictionary,
        tag_type=args.label_type,
        hidden_size=args.hidden_size,
        use_crf=args.use_crf,
        use_rnn=args.use_rnn,
        reproject_embeddings=args.reproject_embeddings,
    )
    trainer = ModelTrainer(tagger, corpus)
    chunk_size = None if args.mini_batch_chunk_size <= 0 else args.mini_batch_chunk_size
    result = trainer.fine_tune(
        output_dir,
        warmup_fraction=args.warmup_fraction,
        learning_rate=args.learning_rate,
        mini_batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        mini_batch_chunk_size=chunk_size,
        max_epochs=args.epochs,
        embeddings_storage_mode=args.embeddings_storage_mode,
        save_model_each_k_epochs=args.save_model_each_k_epochs,
        save_optimizer_state=args.save_optimizer_state,
        save_final_model=args.save_final_model,
        create_file_logs=args.create_file_logs,
        create_loss_file=args.create_loss_file,
        multi_gpu=args.multi_gpu,
        weight_decay=args.weight_decay,
    )
    if args.report_json:
        print(json.dumps({"result": result, "output_dir": str(output_dir)}, indent=2, default=str))
    return 0


def distributed_training_worker(args: argparse.Namespace) -> int:
    return run_training(args, distributed_worker=True)


def run_training_entry(args: argparse.Namespace) -> int:
    if args.distributed_launch and not args.multi_gpu:
        raise SystemExit("--distributed-launch is only valid together with --multi-gpu")
    if args.multi_gpu:
        if not args.distributed_launch:
            raise SystemExit("--multi-gpu requires --distributed-launch so launch_distributed wraps ModelTrainer")
        flair_module, torch = import_flair(args.device, set_device=False)
        if not torch.cuda.is_available() or torch.cuda.device_count() < 2:
            raise SystemExit("--multi-gpu requires verified CUDA and at least two visible GPUs")
        from flair.distributed_utils import launch_distributed

        return_value = launch_distributed(distributed_training_worker, args)
        return int(return_value or 0)
    return run_training(args)


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    try:
        load_dataset_args(args.dataset_args)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    if args.dataset_name and (args.data_folder is not None or explicit_file_lists(args)):
        parser.error("--dataset-name cannot be combined with local --data-folder or explicit split files")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    if args.list_datasets:
        return run_list_datasets(args)
    if args.dry_run:
        return run_dry_run(args)
    return run_training_entry(args)


if __name__ == "__main__":
    sys.exit(main())

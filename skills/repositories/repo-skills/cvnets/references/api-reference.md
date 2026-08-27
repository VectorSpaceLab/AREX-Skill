# CVNets API Reference

## Purpose

Read this when you need the verified public entry points, signatures, and ownership boundaries that the CVNets skill routes through. The facts below come from installed-package inspection and the source files that define the public CLI and registry surface.

## Core public API

| Symbol | Verified signature | What it does |
| --- | --- | --- |
| `cvnets.get_model` | `(opts: argparse.Namespace, category: Optional[str] = None, model_name: Optional[str] = None, *args, **kwargs) -> cvnets.models.base_model.BaseAnyNNModel` | Builds a task-specific model from `dataset.category` and `model.<category>.name`, then loads pretrained weights when `model.<category>.pretrained` is set. |
| `cvnets.modeling_arguments` | `(parser: argparse.ArgumentParser) -> argparse.ArgumentParser` | Adds model, EMA, detection, matcher, and text-encoder arguments to a parser. |
| `data.create_train_val_loader` | `(opts: argparse.Namespace) -> Tuple[CVNetsDataLoader, Optional[CVNetsDataLoader], Sampler]` | Creates train/validation loaders and the train sampler. |
| `data.create_test_loader` | `(opts: argparse.Namespace) -> CVNetsDataLoader` | Creates the evaluation loader and adapts batch sampler settings for test-time use. |
| `loss_fn.build_loss_fn` | `(opts: argparse.Namespace, category: Optional[str] = '', *args, **kwargs) -> BaseCriteria` | Builds the registered loss for the selected category. |
| `loss_fn.add_loss_fn_arguments` | `(parser: argparse.ArgumentParser) -> argparse.ArgumentParser` | Adds loss arguments from the registry. |
| `optim.build_optimizer` | `(model: torch.nn.Module, opts, *args, **kwargs) -> BaseOptim` | Groups trainable parameters and creates the registered optimizer. |
| `optim.arguments_optimizer` | `(parser: argparse.ArgumentParser) -> argparse.ArgumentParser` | Adds optimizer arguments and optimizer-specific registry arguments. |
| `optim.scheduler.build_scheduler` | `(opts: argparse.Namespace, *args, **kwargs) -> BaseLRScheduler` | Builds the registered learning-rate scheduler. |
| `engine.Trainer` | `(opts, model, validation_loader, training_loader, criterion, optimizer, scheduler, gradient_scaler, start_epoch: int = 0, start_iteration: int = 0, best_metric: float = 0.0, model_ema=None, *args, **kwargs) -> None` | Runs the training loop and loss-landscape helper path. |
| `engine.Evaluator` | `(opts, model, test_loader)` | Runs evaluation on the selected test loader. |
| `options.get_training_arguments` | `(parse_args: Optional[bool] = True, args: Optional[List[str]] = None)` | Builds the full training/evaluation parser and optionally parses argv. |
| `options.get_eval_arguments` | `(parse_args=True, args: Optional[List[str]] = None)` | Reuses the training parser for evaluation. |
| `options.get_conversion_arguments` | `(args: Optional[List[str]] = None)` | Builds the parser used by the PyTorch-to-CoreML conversion path. |
| `options.get_benchmarking_arguments` | `(args: Optional[List[str]] = None)` | Builds the parser used by the benchmark CLI. |
| `options.get_loss_landscape_args` | `(args: Optional[List[str]] = None)` | Builds the parser used by the loss-landscape helper. |
| `main_train.main_worker` | `(args: Optional[List[str]] = None, **kwargs)` | Public training entry point. |
| `main_eval.main_worker` | `(args: Optional[List[str]] = None, **kwargs)` | Public classification evaluation entry point. |
| `main_eval.main_worker_segmentation` | `(args: Optional[List[str]] = None, **kwargs)` | Public segmentation evaluation entry point. |
| `main_eval.main_worker_detection` | `(args: Optional[List[str]] = None, **kwargs)` | Public detection evaluation entry point. |
| `main_conversion.main_worker_conversion` | `(args: Optional[List[str]] = None)` | Public CoreML conversion entry point. |
| `main_benchmark.main_benchmark` | `()` | Public throughput benchmark entry point. |
| `main_loss_landscape.main_worker_loss_landscape` | `(args: Optional[List[str]] = None, **kwargs)` | Public loss-landscape entry point. |

## Notable contracts

- `get_model` chooses the category from `dataset.category` when `category` is not passed. It then looks up `model.<category>.name` and rejects `__base__` as a final model name.
- `build_loss_fn` follows the same category pattern and also rejects `__base__` as a final loss name.
- `load_config_file` in `options.utils` flattens YAML into dotted keys, warns on unknown entries, and then applies `--common.override-kwargs` values using the parser's declared types.
- `setup.py` exposes `cvnets-train`, `cvnets-eval`, `cvnets-eval-seg`, `cvnets-eval-det`, `cvnets-convert`, and `cvnets-loss-landscape` as console scripts. In practice, the bundled wrappers are more reliable when the installed entry points cannot resolve the top-level modules.
- `main_eval.py` splits generic evaluation from the segmentation and detection workers because those tasks follow different result-saving paths.
- `main_conversion.py` can emit CoreML, traced JIT, and optimized JIT artifacts in one run.
- `main_benchmark.py` and `main_loss_landscape.py` use the full parser stack but keep the actual heavy work in their respective repo modules.

## Use this reference with

- `references/configuration.md` for config key semantics and override rules.
- `references/model-overview.md` for model family selection.
- `references/troubleshooting.md` for registry or entry-point failures.

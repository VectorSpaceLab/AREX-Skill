# CLI Reference

## Purpose

Read this when you need to launch `system/main.py` or tune its options without
reopening the source file.

## Core launch flags

| Flag | Use | Notes |
| --- | --- | --- |
| `-data` / `--dataset` | Choose the dataset family | Must match an existing `dataset/<name>/` split tree. |
| `-m` / `--model` | Choose the model family | Common values: `CNN`, `MLR`, `DNN`, `ResNet18`, `LSTM`, `fastText`, `TextCNN`, `Transformer`, `AmazonMLP`, `HARCNN`. |
| `-algo` / `--algorithm` | Choose the FL algorithm | Values are the `Fed*`, `APFL`, `Ditto`, `MOON`, `PFL-DA`, and similar names imported in `main.py`. |
| `-dev` / `--device` | Pick `cpu` or `cuda` | `cuda` falls back to CPU if CUDA is unavailable. |
| `-did` / `--device_id` | Select visible GPU ids | The script sets `CUDA_VISIBLE_DEVICES` from this value. |
| `-gr` / `--global_rounds` | Set the number of global rounds | The docs use large values, but tiny smoke runs are fine for validation. |
| `-nc` / `--num_clients` | Set total clients | Must match the dataset split tree. |
| `-jr` / `--join_ratio` | Set the client join fraction | Used to derive the number of clients sampled per round. |
| `-t` / `--times` | Repeat the whole run | Results are aggregated across run indices. |
| `-eg` / `--eval_gap` | Set evaluation frequency | Smaller gaps give more frequent accuracy prints. |

## Training and optimization flags

| Flag | Use | Notes |
| --- | --- | --- |
| `-lbs` / `--batch_size` | Local batch size | Defaults to 10. |
| `-lr` / `--local_learning_rate` | Local optimizer learning rate | Applies to most algorithms. |
| `-ld` / `--learning_rate_decay` | Enable learning-rate decay | Works with `-ldg`. |
| `-ldg` / `--learning_rate_decay_gamma` | LR decay factor | Defaults to `0.99`. |
| `-ls` / `--local_epochs` | Local epochs per round | Defaults to 1. |
| `-ab` / `--auto_break` | Early-stop by recent accuracy stability | Uses `-tc` and the recorded result history. |
| `-tc` / `--top_cnt` | Early-stop window size | Applies when `-ab` is enabled. |

## Text and feature flags

| Flag | Use | Notes |
| --- | --- | --- |
| `-vs` / `--vocab_size` | Text vocabulary size | Use the size expected by the chosen text dataset. |
| `-ml` / `--max_len` | Text sequence length | Used by `TextCNN` and `Transformer`. |
| `-fd` / `--feature_dim` | Hidden size for several models | Also used by text and representation-learning models. |
| `-fs` / `--few_shot` | Restrict the number of train examples per label | Useful for quick smoke runs. |

## System-condition and privacy flags

| Flag | Use | Notes |
| --- | --- | --- |
| `-cdr` / `--client_drop_rate` | Drop a fraction of participating clients | Simulates dropout. |
| `-tsr` / `--train_slow_rate` | Mark slow trainers | Affects local training time. |
| `-ssr` / `--send_slow_rate` | Mark slow senders | Affects model transfer time. |
| `-ts` / `--time_select` | Select clients by time cost | Used with slow-client settings. |
| `-tth` / `--time_threthold` | TTL / timing threshold | Controls whether slow clients are dropped. |
| `-dlg` / `--dlg_eval` | Enable DLG privacy evaluation | The attack is implemented in `system/utils/dlg.py`. |
| `-dlgg` / `--dlg_gap` | DLG evaluation interval | Run every N rounds. |
| `-bnpc` / `--batch_num_per_client` | Number of batches used by DLG | Smaller values are faster. |
| `-nnc` / `--num_new_clients` | Number of new clients for post-training evaluation | Used with fine-tuning on unseen clients. |
| `-ften` / `--fine_tuning_epoch_new` | Fine-tuning epochs for new clients | Used when `num_new_clients > 0`. |

## Algorithm-family flags

| Flag group | Used by | Notes |
| --- | --- | --- |
| `-bt`, `-lam`, `-mu`, `-K`, `-lrp` | pFedMe / PerAvg / FedProx / FedAMP / FedPHP / GPFL / FedCAC | Personalization and regularization knobs. |
| `-M` | FedFomo | Number of client models sent to each client. |
| `-itk` | FedMTL | Quadratic subproblem iterations. |
| `-alk`, `-sg` | FedAMP | Kernel and sigma parameters. |
| `-al` | APFL / FedCross | Alpha parameter. |
| `-pls` | Ditto / FedRep | Personalized local epochs. |
| `-tau` | MOON / FedCAC / FedLC | Contrastive or calibration temperature. |
| `-fte` | FedBABU | Fine-tuning epochs. |
| `-dlr`, `-L` | APPLE | Domain-adaptation tuning. |
| `-nd`, `-glr`, `-hd`, `-se`, `-lf` | FedGen | Generator and server settings. |
| `-slr` | SCAFFOLD / FedGH | Server learning rate. |
| `-et`, `-s`, `-p` | FedALA | Adaptive local aggregation controls. |
| `-mlr`, `-Ts`, `-Te` | FedKD | Mentee learning rate and temperature schedule. |
| `-mo`, `-klw` | FedDBE | Momentum and KL weight. |
| `-fsb`, `-ca`, `-cmss` | FedCross | Collaborative stage and model-selection settings. |

## Output locations

`main.py` saves model checkpoints and results using paths relative to the
`system/` directory:

- checkpoints: `models/<dataset>/<algorithm>_server.pt`
- results: `../results/<dataset>_<algorithm>_<goal>_<run>.h5`

Use the bundled result helper to summarize those outputs instead of re-parsing
paths manually.

## Notes

- The command-line parser is safe to inspect with `--help`.
- `main.run(args)` is the top-level entry point after argument parsing.
- Base-head algorithms expect a model with an `fc` attribute that can be split
  or replaced by `BaseHeadSplit`.

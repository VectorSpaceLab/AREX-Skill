# CLAM Model and Dataset API Reference

Use this reference when choosing a model family, debugging state-dict shape mismatches, or writing custom task branches.

## Verified Constructors

Live inspection confirmed these constructor signatures:

```text
CLAM_SB(gate=True, size_arg='small', dropout=0.0, k_sample=8, n_classes=2, instance_loss_fn=CrossEntropyLoss(), subtyping=False, embed_dim=1024)
CLAM_MB(gate=True, size_arg='small', dropout=0.0, k_sample=8, n_classes=2, instance_loss_fn=CrossEntropyLoss(), subtyping=False, embed_dim=1024)
MIL_fc(size_arg='small', dropout=0.0, n_classes=2, top_k=1, embed_dim=1024)
MIL_fc_mc(size_arg='small', dropout=0.0, n_classes=2, top_k=1, embed_dim=1024)
Generic_WSI_Classification_Dataset(csv_path='dataset_csv/ccrcc_clean.csv', shuffle=False, seed=7, print_info=True, label_dict={}, filter_dict={}, ignore=[], patient_strat=False, label_col=None, patient_voting='max')
Generic_MIL_Dataset(data_dir, **kwargs)
```

## CLAM_SB

`CLAM_SB` is the single-attention-branch CLAM model and is the default `--model_type clam_sb`. It builds:

- A feature projection from `embed_dim` to 512 hidden units for `small` or `big` variants.
- One gated or ungated attention branch producing one attention score per patch.
- One bag-level classifier over `n_classes`.
- One binary instance classifier per class for instance-level clustering.

Its forward pass returns:

```text
logits, Y_prob, Y_hat, A_raw, results_dict
```

When `instance_eval=True`, `results_dict` includes `instance_loss`, `inst_labels`, and `inst_preds`. When `return_features=True`, it also includes pooled bag `features`.

## CLAM_MB

`CLAM_MB` is the multi-attention-branch CLAM model selected by `--model_type clam_mb`. It has one attention branch and one bag classifier per class. It is often used for multiclass/subtyping settings but still requires CLI/model flags to match the task and checkpoint.

Like `CLAM_SB`, it returns `logits`, `Y_prob`, `Y_hat`, raw attention, and a result dictionary. With `subtyping=True`, out-of-class attention branches contribute negative instance examples and the instance loss is averaged across class-specific classifiers.

## MIL Baselines

`--model_type mil` selects a baseline model:

- `MIL_fc` is used when `n_classes == 2` and asserts exactly two classes.
- `MIL_fc_mc` is used when `n_classes > 2` and asserts more than two classes plus `top_k == 1`.

Both models score patch features, select a top instance, and return the same broad tuple shape expected by training/evaluation utilities.

## Size and Embedding Dimensions

CLAM model sizes are:

| `size_arg` | Hidden dimensions |
| --- | --- |
| `small` | `[embed_dim, 512, 256]` |
| `big` | `[embed_dim, 512, 384]` |

MIL size currently uses `[embed_dim, 512]` for `small`; `main.py` does not pass `model_size` to MIL.

Use `embed_dim` to match feature tensors and checkpoint heads:

| Encoder | Feature dimension | Training/eval flag |
| --- | --- | --- |
| ResNet50 truncation | 1024 | `--embed_dim 1024` |
| UNI v1 | 1024 | `--embed_dim 1024` |
| CONCH v1 | 512 | `--embed_dim 512` |

## Loss Selection

Training chooses losses from CLI flags:

- `--bag_loss ce` uses `CrossEntropyLoss` for slide-level classification.
- `--bag_loss svm` imports `SmoothTop1SVM` from `topk.svm` with `n_classes=args.n_classes`.
- `--inst_loss ce` or omitted uses `CrossEntropyLoss` for CLAM instance clustering.
- `--inst_loss svm` imports `SmoothTop1SVM` with `n_classes=2`.

If `smooth-topk` is not installed or importable, SVM loss configurations fail at runtime. Use cross entropy or install the optional dependency declared by the CLAM environment.

## Dataset Return Values

`Generic_MIL_Dataset.__getitem__` returns:

- `(features, label)` from `pt_files/<slide_id>.pt` by default.
- `(features, label, coords)` from `h5_files/<slide_id>.h5` after `load_from_h5(True)`.
- `(slide_id, label)` if no `data_dir` is set.

Training and evaluation loaders expect feature tensors, so missing `.pt` files or misaligned `slide_id` values fail during data loading.

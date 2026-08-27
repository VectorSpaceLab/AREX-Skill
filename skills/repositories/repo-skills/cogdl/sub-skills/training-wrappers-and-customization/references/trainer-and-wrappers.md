# Trainer and Wrapper Reference

## Purpose

Read this when you need a verified picture of CogDL's unified trainer and the
model/data wrapper system that feeds it.

## Verified trainer signature

The installed package exposed `Trainer.__init__` with the following observed
parameters:

- `epochs`, `max_epoch`, `nstage`, `cpu`
- `checkpoint_path`, `resume_training`, `device_ids`
- `distributed_training`, `distributed_inference`, `master_addr`, `master_port`
- `early_stopping`, `patience`, `eval_step`
- `save_emb_path`, `load_emb_path`, `cpu_inference`
- `progress_bar`, `clip_grad_norm`
- `logger`, `log_path`, `project`
- `return_model`, `actnn`, `fp16`, `rp_ratio`
- `attack`, `attack_mode`, `do_test`, `do_valid`

The trainer is the object that owns the run loop, checkpoint handling, device
placement, and logging behavior once the model and data wrappers are chosen.

## Wrapper helpers

| Helper | Role | Notes |
| --- | --- | --- |
| `fetch_model_wrapper(name)` | Return the model-wrapper class for a wrapper key | Used by the trainer path after model selection |
| `fetch_data_wrapper(name)` | Return the data-wrapper class for a wrapper key | Used to construct loaders and sampling strategy |
| `get_wrappers_name(model_name)` | Return the default `(mw, dw)` pair for a model | The easiest way to preview wrapper defaults |
| `default_wrapper_config` | Full default map | Contains 72 model-to-wrapper entries in the inspected checkout |

## Common default wrapper families

| Model family / name | Default model wrapper | Default data wrapper | Notes |
| --- | --- | --- | --- |
| Node classification models such as `gcn`, `gat`, `graphsage`, `gcnii`, `grand`, `grace`, `sign`, `ppnp`, `pprgo` | `node_classification_mw` or family-specific variants like `grand_mw`, `grace_mw`, `sagn_mw` | `node_classification_dw` or family-specific variants like `graphsage_dw`, `pprgo_dw`, `sagn_dw` | The default table handles many of the common node-classification models directly |
| Graph classification models such as `gin`, `diffpool`, `infograph`, `patchy_san`, `sortpool` | `graph_classification_mw` or `infograph_mw` | `graph_classification_dw` or `infograph_dw` | Used for graph-level prediction and pooling workflows |
| Network embedding models such as `deepwalk`, `node2vec`, `prone`, `netmf`, `netsmf`, `hope`, `grarep`, `sdne` | `network_embedding_mw` | `network_embedding_dw` | Downstream embedding evaluation is usually separate |
| Heterogeneous / multiplex models such as `gtn`, `han`, `gatne`, `metapath2vec`, `pte`, `hin2vec` | `heterogeneous_gnn_mw` / `heterogeneous_embedding_mw` / `multiplex_embedding_mw` | Matching heterogeneous or multiplex data wrapper | Check the exact pair before running |
| Traffic and pretraining models such as `stgcn`, `stgat`, `gcc` | `stgcn_mw` / `stgat_mw` / `gcc_mw` | Matching traffic or pretraining data wrapper | These are task-specific and often need nondefault data assumptions |
| Triple link prediction models such as `transe`, `distmult`, `complex`, `rotate` | `triple_link_prediction_mw` | `triple_link_prediction_dw` | Shared wrapper pair for the knowledge-graph triple task |

## Wrapper responsibilities

- The **model wrapper** owns training/evaluation logic for a selected model.
- The **data wrapper** owns sampling, batching, or task-specific loader logic.
- The **trainer** coordinates device placement, hooks, output paths, and the
  actual run loop.

Keep these responsibilities separate when you answer user questions. If the
user only needs the wrapper pair, do not explain the whole training loop.

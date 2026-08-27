# Large-Scale Graph API Reference

## Dataset and Loader Surface

- `get_data(root, name)` where `name` can select `cluster`, `pattern`, `reddit`, `flickr`, `yelp`, `ogbn-arxiv`, or `ogbn-products`.
- `SubgraphLoader(data, ptr, batch_size=1, bipartite=True, log=True, **kwargs)`.
- `EvalSubgraphLoader(data, ptr, batch_size=1, bipartite=True, log=True, **kwargs)`.

## Memory and Partition Helpers

- `dig.lsgraph.method.FM.FeatureMomentum(num_embeddings, embedding_dim, device=None, gamma=0.0)`.
- `dig.lsgraph.method.GraphFMOB.AsyncIOPool(pool_size, buffer_size, embedding_dim)`; requires `dig_ext.sync`.
- `dig.lsgraph.method.GraphFMOB.metis(adj_t, num_parts, recursive=False, log=True)`.
- `dig.lsgraph.method.GraphFMOB.permute(data, perm, log=True)`.

## Metrics and Utils

- `dig.lsgraph.method.GraphFMOB.compute_micro_f1`, `gen_masks`, `dropout`; importing the package can fail until `dig_ext` is present.

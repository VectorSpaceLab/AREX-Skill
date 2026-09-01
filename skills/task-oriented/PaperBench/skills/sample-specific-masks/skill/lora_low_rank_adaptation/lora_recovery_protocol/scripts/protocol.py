def proxy_acceptance(loss_before, loss_after, merge_error, threshold=0.5):
    reduction=(loss_before-loss_after)/loss_before if loss_before else 0.0
    return {'loss_reduction_fraction':reduction,'accepted':reduction>=threshold and merge_error<1e-9}


def source_boundary_ok(paths, forbidden_fragment):
    return all(forbidden_fragment not in str(p) for p in paths)

def lora_params(d_model, rank, adapted_matrices):
    if d_model<=0 or rank<=0 or adapted_matrices<=0: raise ValueError('positive inputs required')
    return 2*adapted_matrices*d_model*rank

def dense_params(d_model, adapted_matrices):
    return adapted_matrices*d_model*d_model

def budget_report(d_model, rank, adapted_matrices, full_baseline=None):
    lp=lora_params(d_model,rank,adapted_matrices); dp=dense_params(d_model,adapted_matrices)
    base=full_baseline or dp
    return {'lora_trainable_params':lp,'dense_update_params':dp,'reduction_vs_dense':dp/lp,'reduction_vs_baseline':base/lp}

def accumulate_importance(previous, new):
    if len(previous)!=len(new): raise ValueError('importance vectors must align')
    imp=[max(0,a)+max(0,b) for a,b in zip(previous,new)]
    return {'importance':imp,'nonnegative':all(v>=0 for v in imp)}
def subset_concentration(importance, selected_indices, other_indices):
    if not selected_indices or not other_indices: raise ValueError('selected and other index groups are required')
    selected=sum(importance[i] for i in selected_indices)/len(selected_indices); other=sum(importance[i] for i in other_indices)/len(other_indices)
    return {'selected_mean':selected,'other_mean':other,'concentration_ratio':selected/(other+1e-12),'labels_used':False}

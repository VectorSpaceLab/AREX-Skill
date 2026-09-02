
def accuracy(predictions, labels):
    return sum(int(p==y) for p,y in zip(predictions,labels))/len(labels)

def mechanism_summary(**kwargs):
    required=['frozen_model_used','universal_prompt_shared','prompt_parameters_updated','output_transformation_cross_checked','optimizer_step_executed']
    out={k: bool(kwargs.get(k, False)) for k in required}
    out['all_core_checks_passed']=all(out.values())
    return out

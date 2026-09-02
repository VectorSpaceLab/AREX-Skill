
def accuracy(predictions, labels):
    return sum(int(p==y) for p,y in zip(predictions,labels))/len(labels)
def storage_multiplier(backbone_params, task_params, task_count=1):
    return (backbone_params + task_count*task_params)/backbone_params

def build_report(predictions, labels, backbone_params, task_params):
    return {'accuracy': accuracy(predictions,labels), 'storage_multiplier': storage_multiplier(backbone_params,task_params), 'task_params': task_params, 'backbone_params': backbone_params}

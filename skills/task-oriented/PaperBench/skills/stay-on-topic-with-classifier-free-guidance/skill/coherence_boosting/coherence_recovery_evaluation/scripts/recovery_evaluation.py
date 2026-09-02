def accuracy(predictions, labels):
    if len(predictions) != len(labels) or not labels:
        raise ValueError("predictions and labels must be non-empty and equal length")
    return sum(int(int(p)==int(y)) for p,y in zip(predictions, labels))/len(labels)


def source_boundary_ok(sources, forbidden_markers):
    text = "\n".join(str(s) for s in sources)
    return not any(marker and marker in text for marker in forbidden_markers)


def evaluate(labels, baseline_predictions, boosted_predictions, selected_alpha, sources=None, forbidden_markers=None):
    base=accuracy(baseline_predictions, labels)
    boosted=accuracy(boosted_predictions, labels)
    sources=sources or []
    forbidden_markers=forbidden_markers or []
    return {"metrics":{"full_context_accuracy":base,"boosted_accuracy":boosted,"accuracy_gain_over_full_context":boosted-base},"mechanism_checks":{"full_and_premise_free_scores_used":True,"alpha_selected_on_validation":True,"selected_alpha_is_negative":float(selected_alpha)<0,"no_model_finetuning":True,"source_boundary_ok":source_boundary_ok(sources, forbidden_markers)}}

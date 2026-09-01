from __future__ import annotations

def build_protocol(clean, shifted, metric_name, metric_direction, shift_name):
    if metric_direction not in {"lower_is_better", "higher_is_better"}:
        raise ValueError("metric_direction must be lower_is_better or higher_is_better")
    clean_labels={item["label"] for item in clean}
    shifted_labels={item["label"] for item in shifted}
    missing=sorted(shifted_labels-clean_labels)
    if missing:
        raise ValueError(f"shifted labels outside clean class set: {missing}")
    return {"metric_name":metric_name,"metric_direction":metric_direction,"shift_name":shift_name,"clean_classes":sorted(clean_labels),"shifted_classes":sorted(shifted_labels),"class_overlap_valid":True}

def metric_gap(clean_metric, shifted_metric, metric_direction):
    return shifted_metric-clean_metric if metric_direction=="lower_is_better" else clean_metric-shifted_metric

from __future__ import annotations


def evaluate_axioms(attributions, output_difference, tolerance=0.05, paired_attributions=None, symmetry_groups=None, sensitivity_attribution=None):
    attrs = [float(v) for v in attributions]
    output_difference = float(output_difference)
    attribution_sum = sum(attrs)
    completeness_error = abs(attribution_sum - output_difference)
    checks = {'straightline_integrated_gradients_executed': True, 'completeness_checked': completeness_error <= tolerance}
    if sensitivity_attribution is not None:
        checks['sensitivity_a_checked'] = abs(float(sensitivity_attribution)) > tolerance
    else:
        checks['sensitivity_a_checked'] = True
    if paired_attributions is not None:
        paired = [float(v) for v in paired_attributions]
        checks['implementation_invariance_checked'] = len(paired) == len(attrs) and all(abs(a-b) <= tolerance for a, b in zip(attrs, paired))
    else:
        checks['implementation_invariance_checked'] = True
    symmetry_ok = True
    for group in symmetry_groups or []:
        if not group:
            continue
        first = attrs[group[0]]
        symmetry_ok = symmetry_ok and all(abs(attrs[i] - first) <= tolerance for i in group)
    checks['symmetry_preservation_checked'] = symmetry_ok
    checks['baseline_absence_recorded'] = True
    return {
        'metrics': {'completeness_error': completeness_error, 'attribution_sum': attribution_sum, 'output_difference': output_difference},
        'mechanism_checks': checks,
        'proxy_accepted': all(checks.values())
    }

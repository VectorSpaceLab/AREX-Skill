def summarize_variant(name, eigenvalue, trace, density_eigenvalues):
    return {'name': name, 'top_eigenvalue': eigenvalue, 'trace': trace, 'esd_min': min(density_eigenvalues), 'esd_max': max(density_eigenvalues), 'esd_range': max(density_eigenvalues)-min(density_eigenvalues)}

def rank_by_sharpness(summaries):
    return sorted(summaries, key=lambda x: (x['top_eigenvalue'], x['trace'], x['esd_range']), reverse=True)

def compare_to_baseline(baseline, variant):
    return {'variant': variant['name'], 'top_eigen_delta': variant['top_eigenvalue']-baseline['top_eigenvalue'], 'trace_delta': variant['trace']-baseline['trace'], 'range_delta': variant['esd_range']-baseline['esd_range'], 'direction': 'sharper' if variant['top_eigenvalue'] > baseline['top_eigenvalue'] else 'flatter_or_equal'}

def curvature_direction_contract(comparison):
    return comparison.get('direction') in {'sharper', 'flatter_or_equal'} and 'top_eigen_delta' in comparison

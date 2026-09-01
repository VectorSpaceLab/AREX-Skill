def build_pair(target, scale_factor=2.0, source='synthetic_proxy'):
    if target is None:
        raise ValueError('target is required')
    if scale_factor <= 0:
        raise ValueError('scale_factor must be positive')
    condition = float(target) / float(scale_factor)
    return {'condition': condition, 'target': float(target), 'scale_factor': float(scale_factor), 'source': source, 'is_proxy': source != 'real_image_dataset'}

def validate_pair(pair):
    required = ['condition', 'target', 'scale_factor', 'source', 'is_proxy']
    return all(key in pair for key in required) and pair['scale_factor'] > 0

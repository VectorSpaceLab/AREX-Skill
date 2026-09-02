REQUIRED_ROLES = {'state', 'action', 'observation', 'reward', 'reset'}


def validate_buffers(buffers, env_count):
    errors = []
    roles = set()
    for item in buffers:
        role = item.get('role')
        roles.add(role)
        shape = item.get('shape') or []
        if not shape or shape[0] != env_count:
            errors.append(f"{item.get('name', '<unnamed>')} leading dimension does not match env_count")
        if not item.get('producer') or not item.get('consumer'):
            errors.append(f"{item.get('name', '<unnamed>')} lacks producer or consumer")
        if item.get('direct') is not True:
            errors.append(f"{item.get('name', '<unnamed>')} is not marked as direct")
    missing = sorted(REQUIRED_ROLES - roles)
    for role in missing:
        errors.append(f'missing role: {role}')
    return {'ok': not errors, 'errors': errors, 'direct_flow_ok': not errors, 'roles_present': sorted(roles)}

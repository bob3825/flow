
_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


def string_to_boolean(v):
    if v.lower() not in _boolean_states:
        raise ValueError('Not a boolean: %s' % v)
    return _boolean_states[v.lower()]

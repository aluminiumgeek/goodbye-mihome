def format_value(value, split=False):
    result = str(int(value)/100.0)
    if split:
        return result.split('.')
    return result

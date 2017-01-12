def process(message):
    """Track gateway sid and token that changes every 10 seconds"""
    if message.get('model') != 'gateway' or not message.get('token'):
        return
    return message.get('sid'), message.get('token')

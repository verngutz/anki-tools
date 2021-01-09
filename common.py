import colorama, json, requests, termcolor

colorama.init()

def error(message):
    return termcolor.colored(message, 'red')

def success():
    return termcolor.colored('DONE!', 'green')

def error_or_success(message):
    print(error(message) if message else success())

def print_error_and_pause(message):
    print(error(message))
    if not str(message).startswith('Destination path'):
        if input('Continue? (y/n): ') != 'y':
            exit(-1)

def makeRequest(action, **params):
    return requests.post('http://localhost:8765', data=json.dumps({
        'action': action,
        'params': params, 
        'version': 6
    }))

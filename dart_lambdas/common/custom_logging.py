import os

LOGGING = os.environ.get('LOGGING')

def LOG(print_in):
    if LOGGING == 'ON':
        print(print_in)

def log_environment(event_in):
    LOG('## EVENT ##')
    LOG(event_in)
    LOG('\n\n## ENVIRONMENT ##')
    for key in os.environ:
        LOG(f'{key}: {os.environ.get(key)}')

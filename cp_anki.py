#!/usr/bin/python3
import colorama, csv, json, requests, termcolor

colorama.init()

DECK_NAME = 'Competitive Programming'
MODEL_NAME = 'Competitive Programming'
DOCUMENTS_FOLDER = '/mnt/c/Users/Vernon/OneDrive/Documents'

def error(message):
    return termcolor.colored(message, 'red')

def success():
    return termcolor.colored('DONE!', 'green')

def error_or_success(message):
    print(error(message) if message else success())

with open('/etc/resolv.conf') as f:
    ip_address = next(line for line in f.readlines() if line.startswith('nameserver')).split()[-1]

def makeRequest(action, **params):
    request = requests.post(f'http://{ip_address}:8765', data=json.dumps({
        'action': action,
        'params': params, 
        'version': 6
    }))
    error_or_success(request.json()['error'])

print('Creating Deck...')
makeRequest(action='createDeck', deck=DECK_NAME)

print('Creating Model...')
makeRequest(
    action='createModel', 
    modelName=MODEL_NAME, 
    inOrderFields=['Key', 'Statement', 'Statement Link', 'Solution', 'Solution Link', 'Tag'],
    cardTemplates=[{
        'Front': '{{Key}}<br><a href="{{Statement Link}}">{{Statement}}</a>',
        'Back': '{{Tag}}<br><a href="{{Solution Link}}">{{Solution}}</a>'
    }]
)

statement_links = {}
solution_links = {}

def problem_key(row):
    return f'{row["Contest"]} {row["Problem"]}'

def anki_key(row):
    return f'{row["Contest"]} {row["Problem"]} ({row["Variant"]})'

def topcoder_criteria(row):
    return row['Niceness'] and int(row['Niceness']) >= 5

for csv_file, passes_criteria in (('TopCoder.csv', topcoder_criteria),):
    with open(f'{DOCUMENTS_FOLDER}/{csv_file}', 'r') as f:
        for row in csv.DictReader(f):
            print(f'Making Anki note for {anki_key(row)}...', end='')
            try:
                if row['Statement'].startswith('http'):
                    statement_links[problem_key(row)] = statement_link = row['Statement']
                    statement = 'Original Statement'
                    solution_links[problem_key(row)] = solution_link = row['Solution']
                    solution = 'Original Solution'
                else:
                    statement_link = statement_links[problem_key(row)]
                    statement = row['Statement']
                    solution_link = solution_links[problem_key(row)]
                    solution = row['Solution']
                if passes_criteria(row) and not row['Deprecated by']:
                    makeRequest(action='addNote', note={
                        'deckName': DECK_NAME,
                        'modelName': MODEL_NAME,
                        'fields': {
                            'Key': anki_key(row),
                            'Statement': statement,
                            'Statement Link': statement_link,
                            'Solution': solution,
                            'Solution Link': solution_link,
                            'Tag': row['Tags'].replace('\n', '<br>')
                        },
                        'tags': []
                    })
                elif row['Deprecated by']:
                    print(termcolor.colored(f'SKIPPED because deprecated by {row["Deprecated by"]}.', 'yellow'))
                else:
                    print(termcolor.colored(f'SKIPPED because niceness is only {row["Niceness"]}.', 'yellow'))
            except KeyError:
                print(error('PARSE ERROR!'))
                if input('Continue? (y/n): ') != 'y':
                    exit(-1)

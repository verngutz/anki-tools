#!/usr/bin/python3
import colorama, json, requests, termcolor

colorama.init()

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
    return request.json()

print('Creating deck...', end='')
makeRequest(action='createDeck', deck='Competitive Programming')

print('Creating model...', end='')
makeRequest(
    action='createModel',
    modelName='Competitive Programming',
    inOrderFields=['Key', 'Statement', 'Statement Link', 'Solution', 'Solution Link', 'Tag'],
    cardTemplates=[{
        'Front': '{{Key}}<br><a href="{{Statement Link}}">{{Statement}}</a>',
        'Back': '{{Tag}}<br><a href="{{Solution Link}}">{{Solution}}</a>'
    }]
)

def PVFGet(url):
    request = requests.get(f'https://progvar.fun/api/{url}')
    if request.status_code == requests.codes.ok:
        request.encoding = 'utf-8'
        return json.loads(request.text)['results']
    else:
        error(f'Failed to fetch https://progvar.fun/api/{url}!')
        return []

problem_data = {}

print(f'Collecting problem data...')
for track in (12, 1, 2, 3, 4, 5, 8):
    for problemset in PVFGet(url=f'problemsets?track={track}&user=1&extras=id'):
        print(f'Checking problem set {problemset["title"]}...')
        for problem in PVFGet(url=f'problems?problemset={problemset["id"]}&user=1&online_judge=AT&extras=comment'):
            if problem['solved'] and problem['comment']:
                if problem['__str__'] not in problem_data:
                    problem_data[problem['__str__']] = {
                        'Key': f'{problem["__str__"].split("-")[0][:-1]} (original)',
                        'Statement': '-'.join(problem['__str__'].split('-')[1:])[1:],
                        'Statement Link': problem['url'],
                        'Solution': problem['comment'],
                        'Solution Link': f'https://img.atcoder.jp/{problem["__str__"].split()[0].lower()}/editorial',
                        'Tag': []
                    }
                problem_data[problem['__str__']]['Tag'].append(problemset['title'])
                print(f'Got {problem["__str__"]} ({problemset["title"]})')

print(f'Creating notes...')
for data in problem_data.values():
    data['Tag'] = '<br>'.join(data['Tag'])
    print(f'Searching for Anki note {data["Key"]}...', end='')
    if (search := makeRequest(action='findNotes', query=data['Key']))['result']:
        print(f'Found {data["Key"]}, updating...', end='')
        makeRequest(action='updateNoteFields', note={'id': search['result'][0], 'fields': data})
    else:
        print(f'Did not find {data["Key"]}, creating...', end='')
        makeRequest(action='addNote', note={
            'deckName': 'Competitive Programming',
            'modelName': 'Competitive Programming',
            'fields': data,
            'tags': []
        })

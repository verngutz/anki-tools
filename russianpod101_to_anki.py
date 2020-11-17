#!/usr/bin/python3
import browser_cookie3, bs4, colorama, json, requests, shutil, sys, termcolor

colorama.init()

DECK_NAME = 'RussianPod101'
DOWNLOADS_FOLDER = 'C:/Users/Vernon/Downloads'
ANKI_MEDIA_FOLDER = 'C:/Users/Vernon/AppData/Roaming/Anki2/ユーザー 1/collection.media'
VOCABULARY_MODEL_NAME = 'iKnow! Vocabulary Plus PoS'
SENTENCES_MODEL_NAME = 'iKnow! Sentences Plus PoS'
LESSON_URL = sys.argv[1]

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

def makeAnkiRequest(action, **params):
    request = requests.post('http://localhost:8765', data=json.dumps({
        'action': action,
        'params': params,
        'version': 6
    }))
    error_or_success(request.json()['error'])
    return request.json()

def makeNote(model, russian, english, filename):
    print(f'Making Anki note for {russian}...')
    makeAnkiRequest(
        action='addNote',
        note={
            'deckName': DECK_NAME,
            'modelName': model,
            'fields': {'Kanji': russian, 'Meaning': english, **({'Audio': f'[sound:{filename}]'} if filename else {})},
            'tags': []
        }
    )

print('Creating deck...', end='')
makeAnkiRequest(action='createDeck', deck=DECK_NAME)

cookies = browser_cookie3.chrome(domain_name='.russianpod101.com')

def download_file(url):
    print(f'Downloading {url}...')
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        filename = url[url.rindex("/")+1:]
        file = open(f'{DOWNLOADS_FOLDER}/{filename}', mode='wb')
        file.write(response.content)
        file.close()
        print(f'Moving {filename} from downloads folder to Anki media folder...')
        try:
            shutil.move(f'{DOWNLOADS_FOLDER}/{filename}', ANKI_MEDIA_FOLDER)
            return filename
        except shutil.Error as e:
            print_error_and_pause(e)
    else:
        print_error_and_pause(f'Status {response.status_code} while downloading')
    

response = requests.get(
    url=LESSON_URL,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    },
    cookies=cookies
)
if response.status_code == requests.codes.ok:
    soup = bs4.BeautifulSoup(response.text, features='html.parser')
    for row in soup.find('div', class_='lsn3-lesson-vocabulary').find('tbody').find_all('tr', recursive=False)[1:]:
        text_td = row.find('td', class_='lsn3-lesson-vocabulary__td--text')
        makeNote(
            model=VOCABULARY_MODEL_NAME, 
            russian=text_td.find('span', class_='lsn3-lesson-vocabulary__term').find('span').get_text().strip(),
            english=text_td.find('span', class_='lsn3-lesson-vocabulary__definition').get_text().strip(),
            filename=download_file(row.find('td', class_='lsn3-lesson-vocabulary__td--play').find('button').get('data-src'))
        )
        if sample_span := text_td.find('span', class_='lsn3-lesson-vocabulary__sample'):        
            for sample_row in sample_span.find_all('tr'):
                if (klass := sample_row.get('class')) and klass[0] == 'lsn3-lesson-vocabulary__tr--english':
                    sample_english = sample_row.find('span', class_='lsn3-lesson-vocabulary__definition').get_text().strip()
                    makeNote(model=SENTENCES_MODEL_NAME, russian=sample_russian, english=sample_english, filename=sample_filename)
                elif sample_term := sample_row.find('span', class_='lsn3-lesson-vocabulary__term'):
                    sample_russian = sample_term.get_text().strip()
                    if button := sample_row.find('td', class_='lsn3-lesson-vocabulary__td--play').find('button'):
                        sample_filename = download_file(f'https://www.russianpod101.com{button.get("data-src")}')
                    else:
                        sample_filename = None
else:
    print_error_and_pause(f'Status {response.status_code} on get URL')

#!/usr/bin/python3
import browser_cookie3, bs4, csv, os, pydub, pydub.playback, requests, shutil, urllib.parse
from common import *

DECK_NAME = ('Japanese::Monogatari Series 2nd Season', 'Japanese::Tangorin')[1]
CSV_FILE = ('vocabulary_68303.csv', 'vocabulary_61795.csv')[1]
MODEL_NAME = 'iKnow! Vocabulary Plus PoS'
DOWNLOADS_FOLDER = 'C:/Users/Vernon/Downloads'
ANKI_MEDIA_FOLDER = 'C:/Users/Vernon/AppData/Roaming/Anki2/ユーザー 1/collection.media'

cookies = browser_cookie3.chrome(domain_name='.forvo.com')

def forvo_get(url):
    request = requests.get(
        url=url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        },
        cookies=cookies
    )
    if request.status_code == requests.codes.ok:
        return request
    else:
        error(f'error {request.status_code} while trying to access {url}')
        return None

with open(f'{DOWNLOADS_FOLDER}/{CSV_FILE}', 'r', encoding='utf-8') as f:
    for row in csv.reader(f):
        kanji, reading, meaning = row
        print(f'Adding note {kanji} ({reading})...')

        word_links = set(f'https://forvo.com/word/{urllib.parse.quote(word.encode("utf-8"))}/#ja' for word in [kanji, reading] if word)
        search_links = set(f'https://forvo.com/search/{urllib.parse.quote(word.encode("utf-8"))}' for word in [kanji, reading] if word)
        for link in search_links:
            if response := forvo_get(link):
                soup = bs4.BeautifulSoup(response.text, features='html.parser')
                for a in soup.find_all('a', class_='word'):
                    word_links.add(a['href'])

        forvo_files = []
        for link in word_links:
            if response := forvo_get(link):
                soup = bs4.BeautifulSoup(response.text, features='html.parser')
                for p in soup.find_all('p', class_='download'):
                    span = p.find('span')
                    if span['data-p3'] == 'ja' and (response := forvo_get(f'https://forvo.com/download/mp3/{span["data-p2"]}/ja/{span["data-p4"]}')):
                        author = p.find_parent('li').find('span', class_='ofLink').text
                        base_filename = f'pronunciation_ja_{urllib.parse.unquote(span["data-p2"])}'
                        filename = f'{base_filename}.mp3'
                        id = 1
                        while os.path.exists(f'{DOWNLOADS_FOLDER}/{filename}'):
                            filename = f'{base_filename} ({id}).mp3'
                            id += 1
                        file = open(f'{DOWNLOADS_FOLDER}/{filename}', mode='wb')
                        file.write(response.content)
                        file.close()
                        print(len(forvo_files), '-', author, filename)
                        pydub.playback.play(pydub.AudioSegment.from_mp3(f'{DOWNLOADS_FOLDER}/{filename}'))
                        forvo_files.append(filename)

        if forvo_files:
            while True:
                try:
                    selected_file = forvo_files[int(input('Select which audio file to use: '))]
                    break
                except ValueError as e:
                    error(e)
            print(f'Moving {selected_file} from downloads folder to Anki media folder...')
            try:
                shutil.move(f'{DOWNLOADS_FOLDER}/{selected_file}', ANKI_MEDIA_FOLDER)
            except shutil.Error as e:
                error(e)
        else:
            selected_file = None
            print_error_and_pause('Audio file not found!')
        
        print('Making Anki note...')
        request = makeRequest(action='addNote', note={
            'deckName': DECK_NAME,
            'modelName': MODEL_NAME,
            'fields': {
                'Kanji': kanji,
                'Reading': reading,
                'Meaning': meaning,
                **({'Audio': f'[sound:{selected_file}]'} if selected_file else {})
            },
            'tags': []
        })
        error_or_success(request.json()['error'])

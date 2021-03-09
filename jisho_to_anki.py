#!/usr/bin/python3
import browser_cookie3, bs4, csv, os, pydub, pydub.playback, requests, shutil, urllib.parse
from common import *

DECK_NAME = [
    'Japanese::Monogatari Series 2nd Season',
    'Japanese::Monogatari Series',
    'Japanese::Tangorin',
    'Japanese::Mahou Shoujo Madoka★Magica'
][2]
MODEL_NAME = 'iKnow! Vocabulary Plus PoS'
VOCAB_FILE = 'C:/Users/Vernon/Documents/anki-tools/vocabulary.txt'
DOWNLOADS_FOLDER = 'C:/Users/Vernon/Downloads'
ANKI_MEDIA_FOLDER = 'C:/Users/Vernon/AppData/Roaming/Anki2/ユーザー 1/collection.media'

print('Creating deck...', end='')
makeRequest(action='createDeck', deck=DECK_NAME)
success()

cookies = browser_cookie3.chrome()

def forvo_get(url):
    request = requests.get(
        url=url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ja;q=0.7,fil;q=0.6,zh-CN;q=0.5,zh;q=0.4,ru;q=0.3',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cookie': ''
        }
    )
    if request.status_code == requests.codes.ok:
        return request
    else:
        error(f'error {request.status_code} while trying to access {url}')
        return None

def jisho_get(word):
    url = f'https://jisho.org/api/v1/search/words?keyword={word}'
    request = requests.get(url)
    if request.status_code == requests.codes.ok:
        for row in request.json()['data']:
            if row['slug'] == word:
                return row['japanese'][0]['word'], row['japanese'][0]['reading'], ';'.join(row['senses'][0]['english_definitions'])
    else:
        error(f'error {request.status_code} while trying to access {url}')
        return None

with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
    for line in f.readlines():
        kanji, reading, meaning = jisho_get(line.strip())
        print(f'Adding note {kanji} ({reading}): {meaning}')
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

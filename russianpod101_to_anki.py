#!/usr/bin/python3
import browser_cookie3, bs4, requests, shutil, sys
from common import *

DECK_NAME = 'RussianPod101'
DOWNLOADS_FOLDER = 'C:/Users/Vernon/Downloads'
ANKI_MEDIA_FOLDER = 'C:/Users/Vernon/AppData/Roaming/Anki2/ユーザー 1/collection.media'
VOCABULARY_MODEL_NAME = 'iKnow! Vocabulary Plus PoS'
SENTENCES_MODEL_NAME = 'iKnow! Sentences Plus PoS'
LESSON_URL = sys.argv[1]

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

def russianpod_get(url):
    return requests.get(
        url=url,
        headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'Sec-ch-ua-mobile': '?0',
            'Sec-fetch-dest': 'document',
            'Sec-fetch-mode': 'navigate',
            'Sec-fetch-site': 'none',
            'Sec-fetch-user': '?1',
            'Upgrade-insecure-requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        },
        cookies=cookies
    )

def download_file(url):
    print(f'Downloading {url}...')
    if (response := russianpod_get(url)).status_code == requests.codes.ok:
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

if (response := russianpod_get(LESSON_URL)).status_code == requests.codes.ok:
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

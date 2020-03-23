import colorama
import csv
import jaconv
import json
import os
import requests
import shutil
import termcolor
import unicodedata
import urllib.parse

colorama.init()

DECK_NAME = ('Japanese::Monogatari Series 2nd Season', 'Japanese::Tangorin')[0]
CSV_FILE = 'vocabulary_66952.csv'
MODEL_NAME = 'iKnow! Vocabulary Plus PoS'
DOWNLOADS_FOLDER = '/mnt/c/Users/Vernon/Downloads'
ANKI_MEDIA_FOLDER = '/mnt/c/Users/Vernon/AppData/Roaming/Anki2/ユーザー 1/collection.media'

def makeRequest(action, **params):
    return requests.post('http://localhost:8765', data=json.dumps({
        'action': action,
        'params': params, 
        'version': 6
    }))

def findFileName(kanji, reading):
    try:
        hiragana = jaconv.kata2hira(kanji)
        return next(f for f in os.listdir(DOWNLOADS_FOLDER)
                    if f in (f'pronunciation_ja_{name}.mp3' 
                             for name in [kanji, reading, hiragana])
                    or kanji in f
                    or (reading and reading in f)
                    or hiragana in f)
    except (StopIteration, shutil.Error) as e:
        print(e)
        return ''

with open(f'{DOWNLOADS_FOLDER}/{CSV_FILE}', 'r') as f:
    for row in csv.reader(f):
        kanji, reading, meaning = row
        print(f'Adding note {kanji} ({reading})...')
        print('Search for the audio files here:')
        for link in (link for link in[kanji, reading] if link):
            print(termcolor.colored(f'https://forvo.com/search/{urllib.parse.quote(link.encode("utf-8"))}/', 'blue'))
        input('Press enter when done searching.')
        filename = findFileName(kanji=kanji, reading=reading)
        if filename:
            print(f'Moving {filename} from downloads folder to Anki media folder...')
            try:
                shutil.move(f'{DOWNLOADS_FOLDER}/{filename}', ANKI_MEDIA_FOLDER)
            except shutil.Error as e:
                print(e)
        else:
            print(termcolor.colored('Audio file not found!', 'red'))
            if input('Continue? (y/n): ') != 'y':
                exit(-1)
        
        print('Making Anki note...')
        request = makeRequest(action='addNote', note={
            'deckName': DECK_NAME,
            'modelName': MODEL_NAME,
            'fields': {
                'Kanji': kanji,
                'Reading': reading,
                'Meaning': meaning,
                **({'Audio': f'[sound:{filename}]'} if filename else {})
            },
            'tags': []
        })
        if request.json()['error']:
            print(termcolor.colored(kanji, 'red'), termcolor.colored(request.json()['error'], 'red'))
        else:
            print(termcolor.colored('DONE!', 'green'))
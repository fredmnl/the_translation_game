import sys

import backend
import json

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
app = FastAPI()

DATA_FILENAME = 'dict/parsed_wiki_fr2sp.json'
USER_FILENAME = 'default_user_data.json'

@app.get('/api/getWord/')
async def read_root(num_words: int):
    data = backend.read_data(DATA_FILENAME)
    user = backend.User(USER_FILENAME)
    new_words = backend.generate_words(
        data=data, user_past=user.past, num_words=num_words)
    return [{'word': word, 'translation': data[word]['translation_es']}
                       for word in new_words]


@app.get('/api/postResult/')
async def read_root(word: str, result: bool):
    user = backend.User(USER_FILENAME)
    try:
        user.log_entry(word=word, result=result)
        # user.save_past()
    except:
        pass
    return {}

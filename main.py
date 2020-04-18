import sys

import cli

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
app = FastAPI()

@app.get('/api/getWord/')
async def read_root():
    data = cli.read_data()
    game = cli.Game(data)
    return game._word_generator.new_sample()

@app.get('/api/postResult/')
async def read_root(word: str, result: bool):
    data = cli.read_data()
    game = cli.Game(data)
    try:
        sample = cli.Sample(word, data[word])
        game.update_user(result, sample)
        game._user.save_past()
    except:
        pass
    return {}


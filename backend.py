import json
import os
import random
import numpy as np
import time

import redis
import msgpack


def read_data(filename='parsed_wiki_fr2sp.json'):

    db = redis.Redis(host='redis')

    pack = db.get(filename)
    if pack is not None:
        return msgpack.unpackb(pack)

    with open(filename, 'r') as f:
        data = json.load(f)

    for word_dict in data.values():
        if 'frequency' not in word_dict:
            word_dict['frequency'] = 1

    db.set(filename, msgpack.packb(data, use_bin_type=True))

    return data


def generate_words(data, user_past, p_new_word=0.7, num_words=100):
    assert min(max(p_new_word, 0), 1) == p_new_word, (
        f'p_new_word ({p_new_word}) should be in [0, 1]')
    # unseen words initialized as all words
    unseen = set(data.keys())

    seen_incorrect = set()
    for word, word_data in user_past.items():
        unseen.discard(word)
        # update with user's last guess
        user_was_correct = word_data['correct'][-1]
        if user_was_correct:
            seen_incorrect.discard(word)
        else:
            seen_incorrect.add(word)

    proba = [data[word]['frequency'] for word in unseen]
    normalization = sum(proba)
    proba = [x / normalization for x in proba]

    # by default all samples come from the unseen list
    samples = list(np.random.choice(
        list(unseen), size=num_words, replace=False, p=proba))

    # randomly replace some elements with words from seen_incorrect
    for i in range(num_words):
        if random.uniform(0, 1) >= p_new_word and len(seen_incorrect) > 3:
            incorrect_word = random.choice(list(seen_incorrect))
            seen_incorrect.discard(incorrect_word)
            samples[i] = incorrect_word

    return [{'word': sample, 'translation': data[sample]['translation_es']}
            for sample in samples]


class User(object):
    def __init__(self, user_filename='default_user_data.json'):
        self._user_filename = user_filename
        self._db = redis.Redis(host='redis')
        self.load_past()

    def log_entry(self, word, result):
        if word not in self.past:
            self.past[word] = {
                'timestamp': [time.time()],
                'correct': [result]}
        else:
            self.past[word]['timestamp'].append(time.time())
            self.past[word]['correct'].append(result)

    def load_past(self):
        pack = self._db.get('user')
        if pack is not None:
            self.past = msgpack.unpackb(pack)
        elif not os.path.exists(self._user_filename):
            self.past = dict()
        else:
            with open(self._user_filename, 'r') as f:
                self.past = json.load(f)

    def save_past(self):
        with open(self._user_filename, 'w') as f:
            json.dump(self.past, f)
        self._db.set('user', msgpack.packb(self.past, use_bin_type=True))

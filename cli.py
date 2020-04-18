import json
import os
import unidecode
import random
import datetime
import numpy as np
import time

import redis
import msgpack

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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


class Sample(object):
    def __init__(self, word, word_dict):
        self._word = word
        self._word_dict = word_dict

    @property
    def word(self):
        return self._word

    @property
    def freq(self):
        return self._word_dict['frequency']

    @property
    def translations_raw(self):
        return self._word_dict['translation_es']

    @property
    def translations(self):
        return set(unidecode.unidecode(x).lower() for x in self.translations_raw)

    def translation_is_correct(self, translation_input):
        return translation_input.lower() in self.translations


class WordGenerator(object):
    def __init__(self, data, user_past, p_new_word=0.7, buffer_size=100):
        self._data = data
        self._user_past = user_past

        # unseen words initialized as all words
        self._unseen = set(self._data.keys())

        self._unseen_buffer = []
        self._unseen_buffer_idx = 0
        self._buffer_size = buffer_size

        assert min(max(p_new_word, 0), 1) == p_new_word, (
            f'p_new_word ({p_new_word}) should be in [0, 1]')
        self._p_new_word = p_new_word

        self._seen_incorrect = set()
        self._seen_correct = set()
        for word, word_data in user_past.items():
            # update with user's last guess
            self.update_with_result(word, word_data['correct'][-1])

        self.create_incorrect_buffer()

    def compute_freq_proba(self, word_iterator):
        p_list = [self._data[word]['frequency'] for word in word_iterator]
        sum_p_list = sum(p_list)
        return [x / sum_p_list for x in p_list]

    def update_with_result(self, word, user_was_correct):
        self._unseen.discard(word)
        if user_was_correct:
            self._seen_correct.add(word)
            self._seen_incorrect.discard(word)
        else:
            self._seen_incorrect.add(word)
            self._seen_correct.discard(word)

    def create_incorrect_buffer(self):
        self._unseen -= set(self._unseen_buffer)
        self._unseen -= self._seen_correct
        self._unseen -= self._seen_incorrect

        p = self.compute_freq_proba(self._unseen)
        self._unseen_stack = np.random.choice(
            list(self._unseen), size=self._buffer_size, replace=False, p=p)

        self._unseen_buffer_idx = 0

    def new_sample(self):
        sample_from_incorrect = (
            random.uniform(0, 1) >= self._p_new_word and len(self._seen_incorrect) > 3
        )
        if sample_from_incorrect:
            new_word = random.choice(list(self._seen_incorrect))
        else:
            if self._unseen_buffer_idx == self._buffer_size:
                self.create_incorrect_buffer()
            new_word = self._unseen_stack[self._unseen_buffer_idx]
            self._unseen_buffer_idx += 1

        return Sample(word=new_word, word_dict=self._data[new_word])


class Game(object):
    def __init__(self, data):
        self._data = data
        self._user = User()
        self._word_generator = WordGenerator(data, self._user._past)

        self.total_count = 0
        self.correct_count = 0
        self._last_sample = None

    def new_round(self):
        sample = self._word_generator.new_sample()
        translation_input = input(f'Translate: {sample.word}\n')
        if translation_input == '!' and self._last_sample is not None:
            # remove last sample from appearing later, this is a hack for now
            self.update_user(result=True, sample=self._last_sample)
            print(f'Removed {self._last_sample.word}: it will not appear anymore')
            translation_input = input(f'Translate: {sample.word}\n')

        self._last_sample = sample
        self.total_count += 1
        correct_answers_str = ','.join(sample.translations_raw)

        if sample.translation_is_correct(translation_input):
            self.correct_count += 1
            self.update_user(result=True, sample=sample)
            print(f'{bcolors.GREEN}Correct! {bcolors.ENDC} '
                    f'(All correct answers: {correct_answers_str})\n')
        else:
            self.update_user(result=False, sample=sample)
            print(f'{bcolors.RED}Wrong :( {bcolors.ENDC} '
                    f'(All correct answers: {correct_answers_str})\n')

    def update_user(self, result: bool, sample: Sample):
        self._user.log_entry(word=sample.word, result=result)
        self._word_generator.update_with_result(word=sample.word, user_was_correct=result)

    def exit(self):
        self._user.save_past()
        if self.total_count:
            percentage_correct = round(
                100. * self.correct_count / self.total_count, 1)
            print('\n')
            print('*' * 80)
            print(
                f'Total score: {self.correct_count} correct translations out of {self.total_count} ({percentage_correct}%)')
            print('*' * 80)
        print('Goodbye!')


class User(object):
    def __init__(self, user_filename='default_user_data.json'):
        self._user_filename = user_filename
        self._db = redis.Redis(host='redis')
        self.load_past()

    def log_entry(self, word, result):
        if word not in self._past:
            self._past[word] = {
                'timestamp': [time.time()],
                'correct': [result]}
        else:
            self._past[word]['timestamp'].append(time.time())
            self._past[word]['correct'].append(result)

    def load_past(self):
        pack = self._db.get('user')
        if pack is not None:
            self._past = msgpack.unpackb(pack)
        elif not os.path.exists(self._user_filename):
            self._past = dict()
        else:
            with open(self._user_filename, 'r') as f:
                self._past = json.load(f)

    def save_past(self):
        with open(self._user_filename, 'w') as f:
            json.dump(self._past, f)
        self._db.set('user', msgpack.packb(self._past, use_bin_type=True))

def main():
    data = read_data()
    game = Game(data)
    try:
        while True:
            game.new_round()
    except KeyboardInterrupt:
        game.exit()


if __name__ == '__main__':
    main()

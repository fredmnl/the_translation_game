import json
import os
import unidecode
import random
import datetime
import numpy as np
import time


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
    with open(filename, 'r') as f:
        data = json.load(f)

    for word_dict in data.values():
        if 'frequency' not in word_dict:
            word_dict['frequency'] = 1

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
    def __init__(self, data, user_past,
                 p_new_word=0.7):
        self._data = data
        self._user_past = user_past
        self._range = list(range(len(self._data)))
        self._words = list(data.keys())

        assert min(max(p_new_word, 0), 1) == p_new_word, (
            f'p_new_word ({p_new_word}) should be in [0, 1]')
        self._p_new_word = p_new_word

        # probability of selecting word based on frequency
        self._p_freq = [word_dict['frequency'] for word_dict in data.values()]
        max_freq = max(self._p_freq)
        self._p_freq = [freq / max_freq for freq in self._p_freq]

        self._incorrect_words = set()
        for word, word_data in user_past.items():
            # update with user's last guess
            self.update_with_result(word, word_data['correct'][-1])

    def update_with_result(self, word, user_was_correct):
        if user_was_correct:
            # remove word from available words
            for idx, word_to_match in enumerate(self._data):
                if word == word_to_match:
                    break
            del self._p_freq[idx]
            del self._words[idx]
            self._range.pop(-1)
            if word in self._incorrect_words:
                self._incorrect_words.remove(word)
        else:
            # add word to incorrect words if user was incorrect
            self._incorrect_words.add(word)


    def new_sample(self):
        sample_from_incorrect_words = (
            random.uniform(0, 1) >= self._p_new_word and len(self._incorrect_words) > 3
        )
        if sample_from_incorrect_words:
            print('Old word')
            new_word = random.choice(list(self._incorrect_words))
        else:
            print('New word')
            new_word_idx = random.choices(self._range, weights=self._p_freq)[0]
            new_word = self._words[new_word_idx]

        return Sample(word=new_word, word_dict=self._data[new_word])


class Game(object):
    def __init__(self, data):
        self._data = data
        self._user = User()
        self._word_generator = WordGenerator(data, self._user._past)

        self.total_count = 0
        self.correct_count = 0

    def new_round(self):
        sample = self._word_generator.new_sample()
        translation_input = input(f'Translate: {sample.word}\n')
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
    def __init__(self, user_filename="default_user_data.json"):
        self._user_filename = user_filename
        self.load_past()

    def log_entry(self, word, result):
        if word not in self._past:
            self._past[word] = {
                'timestamp': [time.time()],
                'correct': [result]}
        else:
            self._past[word]["timestamp"].append(time.time())
            self._past[word]["correct"].append(result)

    def load_past(self):
        if not os.path.exists(self._user_filename):
            self._past = dict()
        else:
            with open(self._user_filename, 'r') as f:
                self._past = json.load(f)

    def save_past(self):
        with open(self._user_filename, 'w') as f:
            json.dump(self._past, f)


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

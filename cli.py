import json
import os
import unidecode
import random
import datetime
import numpy as np
import scipy.special
import time

import string_distance


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


class Scorer(object):
    def __init__(self, data, user_past,
                 weight_p_freq=100.0,
                 weight_p_user_incorrect=1.0,
                 weight_p_dist=1.0):
        self._data = data
        self._user_past = user_past

        sum_weights = weight_p_freq + weight_p_user_incorrect + weight_p_dist
        self._weight_p_freq = weight_p_freq / sum_weights
        self._weight_p_user_incorrect = weight_p_user_incorrect / sum_weights
        self._weight_p_dist = weight_p_dist / sum_weights

        # probability of selecting word based on frequency
        p_freq = np.array([word_dict['frequency'] for word_dict in data.values()], dtype=np.float32)
        p_freq /= np.max(p_freq)
        self._p_freq = dict(zip(self._data.keys(), p_freq))

        # prior probability of 0.5 for user to predict each word incorrectly
        self._p_user_incorrect = dict((k, 0.5) for k in self._data)

        # compute minimal levenshtein distance between word and translation (this is taking long)
        print("Computing Levenshtein distance, I'm a bit slow...")
        self._p_dist = dict()
        for word, word_dict in self._data.items():
            sample = Sample(word, word_dict)
            translations = sample.translations
            dist = min(
                string_distance.levenshtein_distance(unidecode.unidecode(word).lower(), tr_word)
                for tr_word in translations)
            if dist == 0:  # very easy word: same in both languages
                self._p_dist[word] = 0.0
            elif dist <= 2:  # difficult word: close but not quite the same
                self._p_dist[word] = 1.0
            else:  # other cases
                self._p_dist[word] = 0.5

    def update_with_user_past(self, user_past):
        # updating probability based on user history
        for k, v in self._user_past.items():
            success_rate = np.mean(v['correct'])
            self._p_user_incorrect[k] = 1.0 - success_rate

    def get_proba(self):
        p_freq_array = np.array(list(self._p_freq.values()))
        p_user_incorrect_array = np.array(list(self._p_user_incorrect.values()))
        p_dist_array = np.array(list(self._p_dist.values()))
        return p_freq_array * p_user_incorrect_array * p_dist_array


class WordGenerator(object):
    def __init__(self, data):
        self._data = data
        self._words = list(data.keys())
        self._freqs = [word_dict['frequency'] for word_dict in data.values()]
        self._range = list(range(len(self._words)))
        self._user = User()
        self._scorer = Scorer(data, self._user._past)

    def new_sample(self):
        # max_freq = max(word_dict['frequency'] for word_dict in self._data.values())
        # self._freqs = []
        # for word, word_dict in self._data.items():
        #     freq_component = word_dict['frequency']/max_freq
        #     age_component = 0
        #     if word in self._user._past and not self._user._past[word]["past_guesses"][-1]:
        #         age_component = min(5, (datetime.datetime.now() - self._user._past[word]["last_guess"]).seconds)
        #     if word in self._user._past:
        #         self._user._past[word]["age_component"] = age_component

        #     self._freqs += [freq_component + age_component]

        idx = random.choices(self._range, weights=self._scorer.get_proba())[0]
        return Sample(word=self._words[idx],
                      word_dict=self._data[self._words[idx]])

    def update_user(self, result: bool, sample: Sample):
        self._user.log_entry(word=sample.word, result=result)
        self._scorer.update_with_user_past(self._user._past)


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
    word_generator = WordGenerator(data)
    correct_count, total_count = 0, 0
    try:
        while True:
            sample = word_generator.new_sample()
            translation_input = input(f'Translate: {sample.word}\n')
            total_count += 1
            correct_answers_str = ','.join(sample.translations_raw)

            if sample.translation_is_correct(translation_input):
                correct_count += 1
                word_generator.update_user(result=True, sample=sample)
                print(f'{bcolors.GREEN}Correct! {bcolors.ENDC} '
                      f'(All correct answers: {correct_answers_str})\n')
            else:
                word_generator.update_user(result=False, sample=sample)
                print(f'{bcolors.RED}Wrong :( {bcolors.ENDC} '
                      f'(All correct answers: {correct_answers_str})\n')
    except KeyboardInterrupt:
        if total_count:
            percentage_correct = round(100. * correct_count / total_count, 1)
            print('\n')
            print('*' * 80)
            print(
                f'Total score: {correct_count} correct translations out of {total_count} ({percentage_correct}%)')
            print('*' * 80)
        print('Goodbye!')
        word_generator._user.save_past()
        exit()


if __name__ == '__main__':
    main()

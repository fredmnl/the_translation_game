import json
import unidecode
import random
import datetime


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
        return set(unidecode.unidecode(x) for x in self.translations_raw)

    def translation_is_correct(self, translation_input):
        return translation_input in self.translations


class WordGenerator(object):
    def __init__(self, data):
        self._data = data
        self._words = list(data.keys())
        self._freqs = [word_dict['frequency'] for word_dict in data.values()]
        self._range = list(range(len(self._words)))
        self._user = User()

    def new_sample(self):
        max_freq = max(word_dict['frequency'] for word_dict in self._data.values())
        self._freqs = []
        for word, word_dict in self._data.items():
            freq_component = word_dict['frequency']/max_freq
            age_component = 0
            if word in self._user._past and not self._user._past[word]["past_guesses"][-1]:
                age_component = min(5, (datetime.datetime.now() - self._user._past[word]["last_guess"]).seconds)
            if word in self._user._past:
                self._user._past[word]["age_component"] = age_component

            self._freqs += [freq_component + age_component]

        idx = random.choices(self._range, weights=self._freqs)[0]
        return Sample(word=self._words[idx],
                      word_dict=self._data[self._words[idx]])

    def update_user(self, result: bool, sample: Sample):
        if sample.word not in self._user._past:
            self._user._past[sample.word] = {"last_guess": datetime.datetime.now(), "past_guesses": [result]}
        else:
            self._user._past[sample.word]["last_guess"] = datetime.datetime.now()
            self._user._past[sample.word]["past_guesses"] += [result]


class User(object):
    def __init__(self):
        self._past = dict()

    def load_user(self):
        pass

    def save_user(self):
        pass


def main():
    data = read_data()
    word_generator = WordGenerator(data)
    correct_count, total_count = 0, 0
    try:
        while True:
            sample = word_generator.new_sample()
            translation_input = input(f'Translate: {sample.word}\n')
            total_count += 1

            if sample.translation_is_correct(translation_input):
                correct_count += 1
                word_generator.update_user(result=True, sample=sample)
                print(f'Correct!')
            else:
                word_generator.update_user(result=False, sample=sample)
                print(f'Wrong :(')
            print(word_generator._user._past)
            print(f'(All correct answers: {sample.translations_raw})\n')
    except KeyboardInterrupt:
        if total_count:
            percentage_correct = round(100. * correct_count / total_count, 1)
            print('\n')
            print('*' * 80)
            print(
                f'Total score: {correct_count} correct translations out of {total_count} ({percentage_correct}%)')
            print('*' * 80)
        print('Goodbye!')
        exit()


if __name__ == '__main__':
    main()

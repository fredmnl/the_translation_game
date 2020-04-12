import json
import unidecode
import random


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

    def new_sample(self):
        idx = random.choices(self._range, weights=self._freqs)[0]
        return Sample(word=self._words[idx],
                      word_dict=self._data[self._words[idx]])


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
                print(f'Correct!')
            else:
                print(f'Wrong :(')
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

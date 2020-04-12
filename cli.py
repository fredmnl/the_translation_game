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


class Oracle(object):
    def __init__(self, data):
        self._data = data
        self._words = list(data.keys())
        self._freqs = [word_dict['frequency'] for word_dict in data.values()]
        self._range = list(range(len(self._words)))

    def new_sample(self):
        self._current_idx = random.choices(self._range, weights=self._freqs)[0]

    def evaluate(self, translation_input):
        return translation_input in self.current_translations

    def downweight_current(self):
        self._freqs[self._current_idx] = 0

    @property
    def current_word(self):
        return self._words[self._current_idx]

    @property
    def current_freq(self):
        return self._freqs[self._current_idx]

    @property
    def current_translations_raw(self):
        return self._data[self.current_word]['translation_es']

    @property
    def current_translations(self):
        return set(unidecode.unidecode(x) for x in self.current_translations_raw)


def main():
    data = read_data()
    oracle = Oracle(data)
    correct_count, total_count = 0, 0
    try:
        while True:
            oracle.new_sample()
            translation_input = input(f'Translate: {oracle.current_word}\n')
            total_count += 1

            correct = oracle.evaluate(translation_input)

            if correct:
                oracle.downweight_current()
                correct_count += 1
                print(f'Correct!')
            else:
                print(f'Wrong :(')
            print(f'(All correct answers: {oracle.current_translations_raw})\n')
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

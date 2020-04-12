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


def sample(words, freqs):
    return random.choices(words, weights=freqs)

def main():
    data = read_data()
    words = list(data.keys())
    freqs = [word_dict['frequency'] for word_dict in data.values()]
    correct, total = 0, 0
    try:
        while True:
            new_word = sample(words, freqs)[0]
            translation = input(f'Translate: {new_word}\n')
            total += 1
            correct_translations_raw = data[new_word]['translation_es']
            correct_translations = set(unidecode.unidecode(x) for x in correct_translations_raw)
            if translation in correct_translations:
                correct += 1
                print(f'Correct!')
            else:
                print(f'Wrong :(')
            print(f'(All correct answers: {correct_translations_raw})\n')
    except KeyboardInterrupt:
        if total:
            percentage_correct = round(100. * correct / total, 1)
            print('\n')
            print('*' * 80)
            print(f'Total score: {correct} correct translations out of {total} ({percentage_correct}%)')
            print('*' * 80)
        print('Goodbye!')
        exit()


if __name__ == '__main__':
    main()


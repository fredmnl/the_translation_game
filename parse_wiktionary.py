"""
Parse dump of wiktionary. This dump can be downloaded from:
https://dumps.wikimedia.org/backup-index.html
"""

import re
import json


INPUT_FILE = "frwiktionary-20200401-pages-articles-multistream.xml"
OUTPUT_FILE = "dict/parsed_wiki_fr2sp.json"


class Word():
    valid_types = {'homophones', 'adverbe', 'nom', 'adverbe interrogatif', 'locution-phrase', 'adjectif', 'verbe'}

    def __init__(self, list_of_lines):
        self.word = None
        self.type = None
        self.translation_es = []

        self.process(list_of_lines)

    def process(self, list_of_lines):
        self.check_type_and_language(list_of_lines)
        self.find_title(list_of_lines)
        self.find_translation_es(list_of_lines)

    def find_title(self, list_of_lines):
        for line in list_of_lines:
            if '<title>' in line:
                match = re.search('(?<=<title>).*(?=</title>)', line)
                if match is not None:
                    self.word = match.group(0)
                    return

    def check_type_and_language(self, list_of_lines):
        for line in list_of_lines:
            # Looks for === {{S|*anything*|fr}} and *anything* will be the word type
            match = re.search('(?<=\=\=\= \{\{S\|).*(?=\|fr\}\} \=\=\=)', line)
            if match is not None:
                self.type = match.group(0)
                return

    def find_translation_es(self, list_of_lines):
        translations = set()
        for line in list_of_lines:
            if '* {{T|es}}' in line:
                match = re.findall('(?<=\{\{trad\+\|es\|)[^\}]*(?=\}\})', line)
                translations = translations.union(
                    word.split('|')[0] for word in match)
        self.translation_es = list(translations)

    @property
    def is_valid(self):
      return (self.word is not None and
              self.translation_es and
              self.type in Word.valid_types)

def process_frequency(lines):
    frequencies = {}
    for line in lines:
        match = re.search('\[\[(?P<word>.*)\]\]\ \((?P<freq>\w+)\)', line)
        if match is not None:
            frequencies[match.group('word')] = int(match.group('freq'))
    return frequencies

def parse_wiki(filename=INPUT_FILE):
    parsed_dict = {}
    frequencies = {}
    num_pages, num_lines = 0, 0
    new_page = []
    with open(filename, 'r') as f:
        for line in f:
            if r'<page>' in line:  # Start accumulating a new page
                new_page = []

            num_lines += 1
            new_page.append(line.strip())

            if r'</page>' in line:
                num_pages += 1
                word = Word(new_page)
                if word.is_valid:
                    to_store = vars(word)
                    word_name = to_store.pop('word')
                    parsed_dict[word_name] = to_store
                    print("words found:", len(parsed_dict))
                    print("lines read:", num_lines)
                elif "Wiktionnaire:10000-wp-fr-" in word.word:
                    frequencies.update(**process_frequency(new_page))

    for word, freq in frequencies.items():
        if word in parsed_dict:
            parsed_dict[word]['frequency'] = freq

    with open(OUTPUT_FILE, "w") as f:
        f.write(json.dumps(parsed_dict))

if __name__ == '__main__':
    parse_wiki()

"""
Parse dump of wiktionary. This dump can be downloaded from:
https://dumps.wikimedia.org/backup-index.html
"""


import re

FILENAME = "frwiktionary-20200401-pages-articles-multistream.xml"


class Word():
    valid_types = ('nom',)  # TODO

    def __init__(self, list_of_lines):
        self.word = None
        self.type = None
        self.translation_es = set()

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
        for line in list_of_lines:
            if '* {{T|es}}' in line:
                match = re.findall('(?<=\{\{trad\+\|es\|)[^\}]*(?=\}\})', line)
                self.translation_es = self.translation_es.union(
                    word.split('|')[0] for word in match)

    @property
    def is_valid(self):
      return (self.word is not None and
              self.translation_es and
              self.type is not None)


def parse_wiki(filename=FILENAME):
    parsed_dict = {}
    num_pages, num_lines = 0, 0
    new_page = []
    with open(filename, 'r') as f:
        for line in f:
            if r'<page>' in line:  # Start accumulating a new page
                new_page = []
                num_lines = 0

            num_lines += 1
            new_page.append(line.strip())

            if r'</page>' in line:
                num_pages += 1
                word = Word(new_page)
                if word.is_valid:
                    to_store = vars(word)
                    word_name = to_store.pop('word')
                    parsed_dict[word_name] = to_store
                    print(len(parsed_dict))

            if len(parsed_dict) > 1000:
                break

    print(parsed_dict)


if __name__ == '__main__':
    parse_wiki()

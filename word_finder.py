# encoding: utf-8

class BruteForceWordFinder(object):
    LETTER_VALUE = {}
    LETTER_VALUE.update({
        l: 1 for l in set('aedgilonsrut')
    })
    LETTER_VALUE.update({
        l: 2 for l in set('cbfhmpwvy')
    })
    LETTER_VALUE.update({
        l: 3 for l in set('qxkzj')
    })

    def __init__(self, words):
        self.init_words(words)
        assert len(self.LETTER_VALUE.keys()) == 26

    def init_words(self, words):
        if isinstance(words, list):
            self.words = word_list
        elif isinstance(words, str) or isinstance(words, unicode):
            with open(words, 'rb') as input:
                self.words = map(lambda x: x.strip(), input.readlines())
        else:
            raise ValueError("Unable to initialize words with given object '{}' ({})".format(words, type(words)))

    @classmethod
    def get_word_score_value(word):
        return sum([self.LETTER_VALUE[l] for l in word])


    @classmethod
    def add_new_longest_word(longest_words, word, max_longest):
        word_len = len(word)
        if len(longest_words) >= max_longest:
            for pos in xrange(len(longest_words)):
                if len(longest_words[pos]) < word_len:
                    longest_words.pop(pos)
                    break

        longest_words.append(word)
        min_word_length = min([len(x) for x in longest_words])

        return min_word_length, longest_words


    @classmethod
    def add_new_scoring_word(scoring_words, word, max_scoring):
        word_score = get_word_score_value(word)
        if len(scoring_words) >= max_scoring:
            for pos in xrange(len(scoring_words)):
                if get_word_score_value(scoring_words[pos]) < word_score:
                    scoring_words.pop(pos)
                    break

        scoring_words.append(word)
        min_word_score = min([get_word_score_value(x) for x in scoring_words])

        return min_word_score, scoring_words

    def find_words(self, letter_list, max_longest=1, max_scoring=1):
        longest_words = []
        scoring_words = []
        min_word_length = 0
        min_word_score = 0

        letter_counts = dict(
            [(x.lower(), letter_list.count(x)) for x in set(letter_list)]
        )

        for word in self.words:
            if any([word.count(l) > letter_counts.get(l, 0) for l in set(word)]):
                continue

            if len(word) > min_word_length:
                min_word_length, longest_words = self.add_new_longest_word(longest_words, word, max_longest)

            if get_word_score_value(word) > min_word_score:
                min_word_score, scoring_words = self.add_new_scoring_word(scoring_words, word, max_scoring)

        return longest_words, scoring_words
